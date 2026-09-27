from __future__ import annotations

import operator
from pathlib import Path
from typing import TypedDict, List, Optional, Literal, Annotated
from dotenv import load_dotenv
load_dotenv()

from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults


# ============================================================
# 1) SCHEMAS
# ============================================================

class Task(BaseModel):
    id: int
    title: str

    goal: str = Field(
        ...,
        description=(
            "One sentence describing what the reader should "
            "be able to do/understand after this section."
        ),
    )

    bullets: List[str] = Field(
        ...,
        min_length=3,
        max_length=6,
        description=(
            "3–6 concrete, non-overlapping subpoints "
            "to cover in this section."
        ),
    )

    target_words: int = Field(
        ...,
        description="Target word count for this section (120–550)."
    )

    tags: List[str] = Field(default_factory=list)

    requires_research: bool = False
    requires_citations: bool = False
    requires_code: bool = False


class Plan(BaseModel):
    blog_title: str
    audience: str
    tone: str

    blog_kind: Literal[
        "explainer",
        "tutorial",
        "news_roundup",
        "comparison",
        "system_design"
    ] = "explainer"

    constraints: List[str] = Field(default_factory=list)

    tasks: List[Task]


class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None


class RouterDecision(BaseModel):
    needs_research: bool

    mode: Literal[
        "closed_book",
        "hybrid",
        "open_book"
    ]

    queries: List[str] = Field(
        default_factory=list
    )


class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(
        default_factory=list
    )


# ============================================================
# 2) STATE
# ============================================================

class State(TypedDict):
    topic: str

    # Routing / research
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]

    # Workers
    sections: Annotated[
        List[tuple[int, str]],
        operator.add
    ]

    final: str


# ============================================================
# 3) LLM
# ============================================================

llm = ChatOpenAI(
    model="gpt-4.1-mini"
)


# ============================================================
# 4) ROUTER
# ============================================================

ROUTER_SYSTEM = """
You are a routing module for a technical blog planner.

Decide whether web research is needed BEFORE planning.

Modes:

- closed_book (needs_research=false):
  Evergreen topics where correctness does not depend on recent facts
  (concepts, fundamentals).

- hybrid (needs_research=true):
  Mostly evergreen but needs up-to-date examples/tools/models
  to be useful.

- open_book (needs_research=true):
  Mostly volatile: weekly roundups, "this week", "latest",
  rankings, pricing, policy/regulation.

If needs_research=true:

- Output 3–10 high-signal queries.
- Queries should be scoped and specific.
- Avoid generic queries like just "AI" or "LLM".
- If user asked for "last week/this week/latest",
  reflect that constraint IN THE QUERIES.
"""


def router_node(state: State) -> dict:

    topic = state["topic"]

    decider = llm.with_structured_output(
        RouterDecision
    )

    decision = decider.invoke(
        [
            SystemMessage(
                content=ROUTER_SYSTEM
            ),
            HumanMessage(
                content=f"Topic: {topic}"
            ),
        ]
    )

    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
    }


def route_next(state: State) -> str:

    return (
        "research"
        if state["needs_research"]
        else "orchestrator"
    )


# ============================================================
# 5) RESEARCH - TAVILY
# ============================================================

def _tavily_search(
    query: str,
    max_results: int = 5
) -> List[dict]:

    tool = TavilySearchResults(
        max_results=max_results
    )

    results = tool.invoke(
        {"query": query}
    )

    normalized: List[dict] = []

    for r in results or []:

        normalized.append(
            {
                "title": r.get("title") or "",
                "url": r.get("url") or "",
                "snippet": (
                    r.get("content")
                    or r.get("snippet")
                    or ""
                ),
                "published_at": (
                    r.get("published_date")
                    or r.get("published_at")
                ),
                "source": r.get("source"),
            }
        )

    return normalized


RESEARCH_SYSTEM = """
You are a research synthesizer for technical writing.

Given raw web search results, produce a deduplicated
list of EvidenceItem objects.

Rules:

- Only include items with a non-empty url.
- Prefer relevant + authoritative sources
  (company blogs, docs, reputable outlets).
- If a published date is explicitly present in the
  result payload, keep it as YYYY-MM-DD.
- If missing or unclear, set published_at=null.
- Do NOT guess dates.
- Keep snippets short.
- Deduplicate by URL.
"""


def research_node(state: State) -> dict:

    queries = (
        state.get("queries", [])
        or []
    )

    max_results = 6

    raw_results: List[dict] = []

    for q in queries:

        raw_results.extend(
            _tavily_search(
                q,
                max_results=max_results
            )
        )

    if not raw_results:

        return {
            "evidence": []
        }

    extractor = llm.with_structured_output(
        EvidencePack
    )

    pack = extractor.invoke(
        [
            SystemMessage(
                content=RESEARCH_SYSTEM
            ),
            HumanMessage(
                content=(
                    f"Raw results:\n"
                    f"{raw_results}"
                )
            ),
        ]
    )

    # Deduplicate by URL
    dedup = {}

    for e in pack.evidence:

        if e.url:

            dedup[e.url] = e

    return {
        "evidence": list(
            dedup.values()
        )
    }


# ============================================================
# 6) ORCHESTRATOR - CREATE PLAN
# ============================================================

ORCH_SYSTEM = """
You are a senior technical writer and developer advocate.

Your job is to produce a highly actionable outline
for a technical blog post.

Hard requirements:

- Create 5–9 sections (tasks) suitable for the topic
  and audience.

- Each task must include:
  1) goal (1 sentence)
  2) 3–6 bullets that are concrete,
     specific, and non-overlapping
  3) target word count (120–550)

Quality bar:

- Assume the reader is a developer.
- Use correct terminology.
- Bullets must be actionable:
  build/compare/measure/verify/debug.

- Ensure the overall plan includes at least 2 of these:

  * minimal code sketch / MWE
  * edge cases / failure modes
  * performance/cost considerations
  * security/privacy considerations
  * debugging/observability tips

Grounding rules:

- Mode closed_book:
  keep it evergreen; do not depend on evidence.

- Mode hybrid:
  use evidence for up-to-date examples
  (models/tools/releases) in bullets.

- Mark sections using fresh information as:
  requires_research=True
  and requires_citations=True.

- Mode open_book:
  set blog_kind = "news_roundup".

- Every section is about summarizing events
  and implications.

- DO NOT include tutorial/how-to sections
  unless the user explicitly asked for that.

- If evidence is empty or insufficient,
  create a plan that transparently says
  "insufficient sources" and includes only
  what can be supported.

Output must strictly match the Plan schema.
"""


def orchestrator_node(state: State) -> dict:

    planner = llm.with_structured_output(
        Plan
    )

    evidence = state.get(
        "evidence",
        []
    )

    mode = state.get(
        "mode",
        "closed_book"
    )

    evidence_data = [
        e.model_dump()
        for e in evidence
    ][:16]

    plan = planner.invoke(
        [
            SystemMessage(
                content=ORCH_SYSTEM
            ),
            HumanMessage(
                content=(
                    f"Topic: {state['topic']}\n"
                    f"Mode: {mode}\n\n"
                    f"Evidence "
                    f"(ONLY use for fresh claims; "
                    f"may be empty):\n"
                    f"{evidence_data}"
                )
            ),
        ]
    )

    return {
        "plan": plan
    }
# ============================================================
# 7) FANOUT
# ============================================================

def fanout(state: State):

    return [

        Send(
            "worker",
            {
                "task": task.model_dump(),

                "topic": state["topic"],

                "mode": state["mode"],

                "plan": state["plan"].model_dump(),

                "evidence": [
                    e.model_dump()
                    for e in state.get(
                        "evidence",
                        []
                    )
                ],
            },
        )

        for task in state["plan"].tasks
    ]


# ============================================================
# 8) WORKER - WRITE ONE SECTION
# ============================================================

WORKER_SYSTEM = """
You are a senior technical writer and developer advocate.

Write ONE section of a technical blog post in Markdown.

Hard constraints:

- Follow the provided Goal and cover ALL Bullets
  in order.
- Do not skip or merge bullets.
- Stay close to Target words (±15%).
- Output ONLY the section content in Markdown.
- No blog title H1.
- No extra commentary.
- Start with a '## <Section Title>' heading.

Scope guard:

- If blog_kind == "news_roundup":
  do NOT turn this into a tutorial/how-to guide.

- Do NOT teach web scraping, RSS, automation,
  or "how to fetch news" unless bullets explicitly
  ask for it.

- Focus on summarizing events and implications.

Grounding policy:

- If mode == open_book:
  - Do NOT introduce any specific
    event/company/model/funding/policy claim
    unless supported by provided Evidence URLs.

  - For each event claim, attach a source
    as a Markdown link: ([Source](URL)).

  - Only use URLs provided in Evidence.

  - If not supported, write:
    "Not found in provided sources."

- If requires_citations == true:
  for outside-world claims, cite Evidence URLs
  the same way.

- Evergreen reasoning is OK without citations
  unless requires_citations is true.

Code:

- If requires_code == true,
  include at least one minimal,
  correct code snippet relevant to the bullets.

Style:

- Short paragraphs.
- Bullets where helpful.
- Code fences for code.
- Avoid fluff/marketing.
- Be precise and implementation-oriented.
"""


def worker_node(payload: dict) -> dict:

    task = Task(
        **payload["task"]
    )

    plan = Plan(
        **payload["plan"]
    )

    evidence = [
        EvidenceItem(**e)
        for e in payload.get(
            "evidence",
            []
        )
    ]

    topic = payload["topic"]

    mode = payload.get(
        "mode",
        "closed_book"
    )

    bullets_text = (
        "\n- "
        + "\n- ".join(
            task.bullets
        )
    )

    evidence_text = ""

    if evidence:

        evidence_text = "\n".join(

            f"- {e.title} | "
            f"{e.url} | "
            f"{e.published_at or 'date:unknown'}"

            for e in evidence[:20]
        )

    section_md = llm.invoke(
        [
            SystemMessage(
                content=WORKER_SYSTEM
            ),

            HumanMessage(
                content=(

                    f"Blog title: "
                    f"{plan.blog_title}\n"

                    f"Audience: "
                    f"{plan.audience}\n"

                    f"Tone: "
                    f"{plan.tone}\n"

                    f"Blog kind: "
                    f"{plan.blog_kind}\n"

                    f"Constraints: "
                    f"{plan.constraints}\n"

                    f"Topic: "
                    f"{topic}\n"

                    f"Mode: "
                    f"{mode}\n\n"

                    f"Section title: "
                    f"{task.title}\n"

                    f"Goal: "
                    f"{task.goal}\n"

                    f"Target words: "
                    f"{task.target_words}\n"

                    f"Tags: "
                    f"{task.tags}\n"

                    f"requires_research: "
                    f"{task.requires_research}\n"

                    f"requires_citations: "
                    f"{task.requires_citations}\n"

                    f"requires_code: "
                    f"{task.requires_code}\n"

                    f"Bullets:"
                    f"{bullets_text}\n\n"

                    f"Evidence "
                    f"(ONLY use these URLs "
                    f"when citing):\n"
                    f"{evidence_text}\n"
                )
            ),
        ]
    ).content.strip()

    return {
        "sections": [
            (
                task.id,
                section_md
            )
        ]
    }


# ============================================================
# 9) REDUCER - MERGE SECTIONS + SAVE BLOG
# ============================================================

def reducer_node(state: State) -> dict:

    plan = state["plan"]

    ordered_sections = [

        md

        for _, md in sorted(
            state["sections"],
            key=lambda x: x[0]
        )
    ]

    body = (
        "\n\n".join(
            ordered_sections
        ).strip()
    )

    final_md = (
        f"# {plan.blog_title}\n\n"
        f"{body}\n"
    )

    filename = (
        f"{plan.blog_title}.md"
    )

    Path(filename).write_text(
        final_md,
        encoding="utf-8"
    )

    return {
        "final": final_md
    }


# ============================================================
# 10) BUILD LANGGRAPH
# ============================================================

g = StateGraph(State)

g.add_node(
    "router",
    router_node
)

g.add_node(
    "research",
    research_node
)

g.add_node(
    "orchestrator",
    orchestrator_node
)

g.add_node(
    "worker",
    worker_node
)

g.add_node(
    "reducer",
    reducer_node
)


# START → ROUTER

g.add_edge(
    START,
    "router"
)


# ROUTER → RESEARCH / ORCHESTRATOR

g.add_conditional_edges(
    "router",
    route_next,
    {
        "research": "research",
        "orchestrator": "orchestrator"
    }
)


# RESEARCH → ORCHESTRATOR

g.add_edge(
    "research",
    "orchestrator"
)


# ORCHESTRATOR → WORKERS

g.add_conditional_edges(
    "orchestrator",
    fanout,
    ["worker"]
)


# WORKER → REDUCER

g.add_edge(
    "worker",
    "reducer"
)


# REDUCER → END

g.add_edge(
    "reducer",
    END
)


# Compile the graph

app = g.compile()


# ============================================================
# 11) RUNNER
# ============================================================

def run(topic: str):

    out = app.invoke(
        {
            "topic": topic,

            "mode": "",

            "needs_research": False,

            "queries": [],

            "evidence": [],

            "plan": None,

            "sections": [],

            "final": "",
        }
    )

    return out