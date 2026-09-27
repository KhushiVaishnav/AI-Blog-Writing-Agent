import streamlit as st

from bwa_backend import run


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Blog Writing Agent",
    page_icon="📝",
    layout="wide"
)


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("📝 Blog Writing Agent")

st.write(
    "Enter a topic and let the AI agent research, "
    "plan, and write a complete blog."
)


# --------------------------------------------------
# TOPIC INPUT
# --------------------------------------------------

topic = st.text_input(
    "Enter blog topic",
    placeholder="Example: State of Multimodal LLMs in 2026"
)


# --------------------------------------------------
# GENERATE BUTTON
# --------------------------------------------------

if st.button("🚀 Generate Blog", type="primary"):

    if not topic.strip():

        st.warning("Please enter a blog topic.")

    else:

        try:

            with st.spinner(
                "Agent is researching, planning and writing..."
            ):

                result = run(topic)

            st.success("Blog generated successfully!")

            # ------------------------------------------
            # TABS
            # ------------------------------------------

            tab1, tab2, tab3, tab4 = st.tabs(
                [
                    "🧩 Plan",
                    "🔎 Evidence",
                    "📝 Blog Preview",
                    "🧾 Logs"
                ]
            )

            # ------------------------------------------
            # PLAN
            # ------------------------------------------

            with tab1:

                plan = result.get("plan")

                if plan:

                    st.subheader(plan.blog_title)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write("**Audience**")
                        st.write(plan.audience)

                    with col2:
                        st.write("**Tone**")
                        st.write(plan.tone)

                    with col3:
                        st.write("**Blog Type**")
                        st.write(plan.blog_kind)

                    st.divider()

                    st.subheader("Blog Structure")

                    for task in plan.tasks:

                        with st.expander(
                            f"{task.id}. {task.title}",
                            expanded=False
                        ):

                            st.write("**Goal:**")
                            st.write(task.goal)

                            st.write(
                                f"**Target words:** "
                                f"{task.target_words}"
                            )

                            st.write("**Points to cover:**")

                            for bullet in task.bullets:
                                st.write(f"- {bullet}")

                            st.write(
                                "**Research required:**",
                                task.requires_research
                            )

                            st.write(
                                "**Citations required:**",
                                task.requires_citations
                            )

                            st.write(
                                "**Code required:**",
                                task.requires_code
                            )

                else:

                    st.info("No plan available.")

            # ------------------------------------------
            # EVIDENCE
            # ------------------------------------------

            with tab2:

                evidence = result.get(
                    "evidence",
                    []
                )

                if evidence:

                    st.subheader(
                        f"Research Sources ({len(evidence)})"
                    )

                    for index, item in enumerate(
                        evidence,
                        start=1
                    ):

                        st.markdown(
                            f"### {index}. {item.title}"
                        )

                        st.write(
                            f"**Source:** "
                            f"{item.source or 'Unknown'}"
                        )

                        if item.published_at:

                            st.write(
                                f"**Published:** "
                                f"{item.published_at}"
                            )

                        if item.snippet:

                            st.write(item.snippet)

                        st.markdown(
                            f"[Open source]({item.url})"
                        )

                        st.divider()

                else:

                    st.info(
                        "No web research was required "
                        "for this topic."
                    )

            # ------------------------------------------
            # BLOG PREVIEW
            # ------------------------------------------

            with tab3:

                final_blog = result.get(
                    "final",
                    ""
                )

                if final_blog:

                    st.markdown(final_blog)

                    st.download_button(
                        label="⬇️ Download Blog",
                        data=final_blog,
                        file_name="generated_blog.md",
                        mime="text/markdown"
                    )

                else:

                    st.warning(
                        "No blog was generated."
                    )

            # ------------------------------------------
            # LOGS
            # ------------------------------------------

            with tab4:

                st.write("### Agent Execution")

                st.write(
                    "✅ Router completed"
                )

                if result.get(
                    "needs_research"
                ):
                    st.write(
                        "✅ Research completed"
                    )
                else:
                    st.write(
                        "⏭️ Research not required"
                    )

                st.write(
                    "✅ Blog plan created"
                )

                st.write(
                    "✅ Sections generated"
                )

                st.write(
                    "✅ Sections merged"
                )

                st.write(
                    "✅ Blog saved"
                )

                st.divider()

                st.write(
                    "**Agent mode:**",
                    result.get(
                        "mode",
                        "Unknown"
                    )
                )

                queries = result.get(
                    "queries",
                    []
                )

                if queries:

                    st.write(
                        "**Research queries:**"
                    )

                    for query in queries:
                        st.write(
                            f"- {query}"
                        )

        except Exception as e:

            st.error(
                f"Something went wrong: {e}"
            )