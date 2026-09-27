# 📝 AI Blog Writing Agent

An AI-powered technical blog writing agent built using **Python, LangGraph, LangChain, OpenAI, Tavily, Pydantic, and Streamlit**.

The application takes a blog topic from the user and automatically decides whether web research is required, creates a structured blog plan, generates individual blog sections, combines them, and produces a complete Markdown blog.

---

## 🚀 Project Overview

Writing a technical blog manually involves several steps such as understanding the topic, deciding the structure, researching information, collecting sources, creating a writing plan, writing individual sections, and combining everything into a final article.

This project automates this workflow using an **agentic AI architecture built with LangGraph**.

Instead of using one large LLM call, the system divides the workflow into multiple specialized nodes.

---

## ✨ Features

- 🤖 AI-powered blog generation
- 🧠 LangGraph-based agent workflow
- 🔀 Automatic research routing
- 🔎 Web research using Tavily
- 📚 Evidence and source collection
- 🗂️ Structured blog planning using Pydantic
- ⚡ Parallel section generation
- 📝 Markdown blog generation
- 💾 Automatic Markdown file saving
- 🖥️ Streamlit web interface
- 📋 Blog plan visualization
- 🔎 Research evidence visualization
- 📖 Blog preview
- 🧾 Agent execution logs
- ⬇️ Download generated blog

---

## 🏗️ Architecture

The complete LangGraph workflow is:

**START → Router → Research → Orchestrator → Worker → Reducer → END**

The Research step is conditional.

If research is required:

**START → Router → Research → Orchestrator → Worker → Reducer → END**

If research is not required:

**START → Router → Orchestrator → Worker → Reducer → END**

The Orchestrator creates the blog plan, Workers generate the individual sections, and the Reducer combines the sections into the final blog.

---

## 🧩 LangGraph Nodes

### 1. Router

The Router is the first decision-making node.

It determines:

- Whether web research is required
- The mode of the blog generation process
- Search queries when research is required

The system supports three modes:

### Closed Book

Used for evergreen topics where current information is not necessary.

```text
needs_research = False
```

Example:

```text
What is a Python decorator?
```

### Hybrid

Used for topics that are mostly evergreen but may benefit from current tools, models, or examples.

```text
needs_research = True
```

### Open Book

Used for topics that depend heavily on recent information.

Examples:

```text
Latest AI developments
AI news this week
Current LLM rankings
Current AI pricing
```

---

## 🔎 2. Research Node

When the Router determines that research is required, the Research node executes the generated search queries.

The project uses **Tavily** for web search.

The raw search results are converted into structured evidence.

Each evidence item can contain:

- Title
- URL
- Published date
- Snippet
- Source

Duplicate URLs are removed before the evidence is passed to the next stage.

---

## 🧠 3. Orchestrator Node

The Orchestrator creates the overall structure of the blog.

It generates a structured `Plan` containing:

- Blog title
- Target audience
- Tone
- Blog type
- Constraints
- Sections/tasks

Each task contains:

- Section title
- Goal
- Key points
- Target word count
- Tags
- Research requirement
- Citation requirement
- Code requirement

This allows the blog to be divided into smaller sections that can be generated independently.

---

## ⚡ 4. Worker Node

The Worker is responsible for generating individual blog sections.

The Worker receives:

- Blog topic
- Blog plan
- Section information
- Research evidence
- Writing requirements

It then generates the section in Markdown.

The LangGraph workflow uses a fan-out pattern so that planned sections can be generated independently before being combined by the Reducer.

---

## 🔄 5. Reducer Node

The Reducer receives the generated sections.

It:

1. Sorts the sections using their task IDs
2. Combines the sections in the correct order
3. Adds the blog title
4. Creates the final Markdown document
5. Saves the generated blog as a `.md` file

---

## 🖥️ Streamlit Interface

The project includes a Streamlit interface for interacting with the agent.

The user enters a topic and clicks:

**🚀 Generate Blog**

The application then runs the LangGraph workflow and displays the results.

### 🧩 Plan

Displays:

- Blog title
- Audience
- Tone
- Blog type
- Blog sections
- Section goals
- Target word counts
- Research requirements
- Citation requirements
- Code requirements

### 🔎 Evidence

Displays the research sources collected by the Research node.

The evidence can contain:

- Source title
- Source name
- Publication date
- Snippet
- URL

### 📝 Blog Preview

Displays the complete generated Markdown blog.

The generated blog can also be downloaded from the application.

### 🧾 Logs

Displays the major stages completed by the agent:

```text
✅ Router completed
✅ Research completed
✅ Blog plan created
✅ Sections generated
✅ Sections merged
✅ Blog saved
```

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| LangGraph | Agent workflow and orchestration |
| LangChain | LLM and tool integration |
| OpenAI | Language model |
| Tavily | Web research |
| Pydantic | Structured output validation |
| Streamlit | Web interface |
| Markdown | Generated blog format |

---

## 📁 Project Structure

```text
Blog/
│
├── .venv/
│
├── app.py
├── bwa_backend.py
│
├── 1_bwa_basic.ipynb
├── 2_bwa_improved_prompting.ipynb
├── bwa_research.ipynb
│
├── requirements.txt
├── README.md
├── .gitignore
└── .env
```

### File Description

| File | Description |
|---|---|
| `app.py` | Streamlit user interface |
| `bwa_backend.py` | LangGraph backend and agent workflow |
| `1_bwa_basic.ipynb` | Initial blog-writing implementation |
| `2_bwa_improved_prompting.ipynb` | Improved prompting experiments |
| `bwa_research.ipynb` | Research and development notebook |
| `requirements.txt` | Python dependencies |
| `README.md` | Project documentation |
| `.gitignore` | Files excluded from Git |
| `.env` | API keys and environment variables |

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Blog
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

For Windows:

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root.

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

**Never commit the `.env` file to GitHub.**

---

## ▶️ Run the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

The application will open in the browser.

---

## 💡 Example Topics

You can enter topics such as:

```text
What is Retrieval Augmented Generation?

What is a Python decorator?

How to Learn Generative AI

What are AI Agents?

Understanding Transformer Architecture

State of Multimodal LLMs
```

---

## 🔄 Example Workflow

### Topic requiring research

```text
User Topic → Router → Research → Orchestrator → Worker → Reducer → Final Blog
```

### Topic not requiring research

```text
User Topic → Router → Orchestrator → Worker → Reducer → Final Blog
```

---

## 🧠 Why LangGraph?

LangGraph is used to represent the blog-writing process as a structured workflow.

Instead of relying on one large LLM call, the project separates the process into specialized stages:

```text
Routing → Research → Planning → Section Generation → Reduction
```

This makes the workflow easier to understand, debug, maintain, and extend.

The architecture also allows different blog sections to be generated independently.

---

## 📌 Key Concepts Demonstrated

This project demonstrates practical implementation of:

- Agentic AI
- LangGraph
- LangChain
- LLM integration
- Structured outputs
- Pydantic models
- Tool integration
- Web research
- Conditional routing
- State management
- Parallel section generation
- Prompt engineering
- Streamlit
- Markdown generation

---

## 🔮 Future Improvements

Possible future improvements include:

- Blog history
- Previously generated blog search
- Persistent search history
- Streaming LangGraph execution
- More detailed observability
- Improved source ranking
- Additional LLM providers
- Database-backed blog storage
- Deployment

---

## 👩‍💻 Author

**Khushi Vaishnav**

B.Tech – Computer Science and Business Systems

### Areas of Interest

- Data Science
- Machine Learning
- AI/ML Engineering
- Generative AI
- Agentic AI
