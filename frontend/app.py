import streamlit as st
import requests
import plotly.graph_objects as go

st.set_page_config(
    page_title="Career Intelligence & Skill Gap Platform",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 Career Intelligence & Skill Gap Platform")
st.caption("AI-Powered Resume Analysis, GitHub Profiling, Hybrid Job Matching & GenAI Resume Optimization")

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Settings & Candidate Inputs")
    api_url = st.text_input("FastAPI Backend URL", value="http://127.0.0.1:8000")
    github_user = st.text_input("GitHub Username (Optional)", value="")
    target_role_input = st.text_input("Target Career Role", value="Machine Learning Engineer")
    st.markdown("---")
    st.markdown("### 💡 What this platform does:")
    st.markdown("""
    - **NLP:** spaCy NER & skill extraction
    - **Classical ML & BERT:** Role classification
    - **Vector DB & BM25:** Hybrid semantic job retrieval
    - **GenAI:** STAR resume bullet rewrites & mock interview prep
    """)

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Skill Gap & Profile Analysis",
    "✨ GenAI STAR Resume Tailoring",
    "🗺️ Personalized Learning Roadmap",
    "🎯 Mock Interview Prep",
    "🔍 Hybrid Job Search (Vector+BM25)",
])

# --- TAB 1: Skill Gap & Profile Analysis ---
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. Candidate Resume")
        uploaded_resume = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
        resume_text_input = st.text_area(
            "Or Paste Resume Text directly:",
            height=200,
            value="Senior Python Developer with 4 years experience building backend microservices with FastAPI, Docker, and PostgreSQL. Experienced with PyTorch and Scikit-Learn for ML model training and deployment. Strong team collaboration and problem-solving skills.",
        )
    with col2:
        st.subheader("2. Target Job Description")
        jd_text_input = st.text_area(
            "Paste Target Job Description:",
            height=250,
            value="We are seeking a Lead Machine Learning Engineer. Required skills: Python, PyTorch, MLflow, Docker, Kubernetes, AWS, FastAPI, and Transformers. Must have strong experience deploying models in production, microservices, CI/CD, and communication skills.",
        )

    if st.button("🚀 Run Complete Career Intelligence Analysis", type="primary", use_container_width=True):
        if uploaded_resume:
            with st.spinner("Uploading and parsing resume..."):
                try:
                    upload_response = requests.post(
                        f"{api_url}/resume/upload",
                        files={
                            "file": (
                                uploaded_resume.name,
                                uploaded_resume.getvalue(),
                                uploaded_resume.type or "application/octet-stream",
                            )
                        },
                        timeout=30,
                    )
                    if upload_response.status_code != 200:
                        st.error(f"Resume parsing failed ({upload_response.status_code}): {upload_response.text}")
                        st.stop()
                    parsed_resume = upload_response.json()
                    resume_text_input = parsed_resume["text"]
                    st.session_state["resume_sections"] = parsed_resume["sections"]
                except requests.Timeout:
                    st.error("Resume parsing timed out. Large or scanned PDFs may need more time or OCR setup.")
                    st.stop()
                except requests.RequestException as e:
                    st.error(f"Could not upload resume to backend: {e}")
                    st.stop()
        else:
            st.session_state.pop("resume_sections", None)

        payload = {
            "resume_text": resume_text_input,
            "job_description_text": jd_text_input,
            "github_username": github_user if github_user else None,
            "target_role": target_role_input,
        }

        with st.spinner("Analyzing profile across NLP, ML, and GenAI models..."):
            try:
                resp = requests.post(f"{api_url}/analyze/complete", json=payload, timeout=60)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state["analysis_data"] = data
                    st.session_state.pop("interview_prep", None)
                    st.session_state.pop("rag_recommendations", None)
                    st.session_state.pop("profile_explanation", None)
                    st.session_state["resume_text"] = resume_text_input
                    st.session_state["job_description_text"] = jd_text_input
                    st.session_state["target_role"] = target_role_input
                    st.success("Analysis Complete!")
                else:
                    st.error(f"Backend API error ({resp.status_code}): {resp.text}")
            except requests.Timeout:
                st.error(
                    "Career analysis timed out. Restart the FastAPI backend to load the latest code, "
                    "then retry; GitHub lookups can also take longer."
                )
            except requests.RequestException as e:
                st.error(f"Could not connect to backend at {api_url}: {e}")

    # Display Analysis Results if present in session
    if "analysis_data" in st.session_state:
        data = st.session_state["analysis_data"]
        st.markdown("---")
        if st.session_state.get("resume_sections"):
            with st.expander("Parsed resume sections"):
                for section, content in st.session_state["resume_sections"].items():
                    st.markdown(f"**{section.replace('_', ' ').title()}**")
                    st.write(content)

        # Top Metrics
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric("Skill Match Rate", f"{data['skill_match_percentage']}%")
        mcol2.metric("Detected Skills", len(data["candidate_skills"]))
        mcol3.metric("Required Skills", len(data["required_skills"]))
        mcol4.metric("Missing Skills", len(data["missing_skills"]))

        # Gauge Chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=data["skill_match_percentage"],
            title={"text": "Target Role Match Score"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#4CAF50" if data["skill_match_percentage"] >= 70 else "#FF9800"},
                "steps": [
                    {"range": [0, 50], "color": "#ffebee"},
                    {"range": [50, 75], "color": "#fff3e0"},
                    {"range": [75, 100], "color": "#e8f5e9"},
                ],
            },
        ))
        fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

        scol1, scol2 = st.columns(2)
        with scol1:
            st.success("✅ Matched Skills Detected")
            st.write(", ".join(f"`{s}`" for s in data["candidate_skills"]) or "None detected")

        with scol2:
            st.warning("⚠️ Critical Skill Gaps to Address")
            st.write(", ".join(f"`{s}`" for s in data["missing_skills"]) or "None! Perfect skill alignment.")
            for gap in data.get("ranked_skill_gaps", []):
                st.caption(
                    f"{gap['priority'].title()} priority · {gap['skill']} · "
                    f"mentioned {gap['mention_count']} time(s) · score {gap['priority_score']}"
                )
            st.caption(data.get("skill_match_score_explanation", ""))

        if data.get("github_profile"):
            st.markdown("### 🐙 GitHub Signals Detected")
            gh = data["github_profile"]
            gh_col1, gh_col2, gh_col3 = st.columns(3)
            gh_col1.write(f"**Public Repos:** {gh.get('public_repos', 0)}")
            gh_col2.write(f"**Total Stars:** {gh.get('total_stars', 0)}")
            gh_col3.write(f"**Top Languages:** {', '.join(gh.get('top_languages', []))}")
            if gh.get("detected_frameworks"):
                st.info(f"Verified Frameworks from Repos: {', '.join(gh['detected_frameworks'])}")

        if st.button("✨ Explain my profile with AI", type="primary"):
            with st.spinner("Gemma is preparing a source-grounded profile explanation..."):
                try:
                    response = requests.post(
                        f"{api_url}/analyze/explanation",
                        json={
                            "resume_text": st.session_state.get("resume_text", resume_text_input),
                            "job_description_text": st.session_state.get("job_description_text", jd_text_input),
                            "target_role": st.session_state.get("target_role", target_role_input),
                        },
                        timeout=180,
                    )
                    if response.status_code == 200:
                        st.session_state["profile_explanation"] = response.json()
                    else:
                        st.error(f"Profile explanation failed ({response.status_code}): {response.text}")
                except requests.Timeout:
                    st.error("Gemma timed out while explaining the profile. Retry after the model is warm.")
                except requests.RequestException as e:
                    st.error(f"Profile explanation request failed: {e}")

        explanation = st.session_state.get("profile_explanation")
        if explanation:
            st.markdown("### AI Profile Explanation")
            st.write(explanation["profile_summary"])
            st.caption(f"Evidence-based skill coverage: {explanation['skill_match_percentage']}% · {explanation['score_method']}")
            strengths, gaps = st.columns(2)
            with strengths:
                st.markdown("**Strengths supported by your profile**")
                for item in explanation["strengths"]:
                    st.write(f"**{item['skill']}**: {item['explanation']}")
                    for quote in item["candidate_evidence"]:
                        st.caption(f"Resume: “{quote}”")
                    for quote in item["job_evidence"]:
                        st.caption(f"Job: “{quote}”")
            with gaps:
                st.markdown("**Priority development areas**")
                for item in explanation["priority_gaps"]:
                    st.write(f"**{item['skill']}**: {item['explanation']}")
                    for quote in item["job_evidence"]:
                        st.caption(f"Job requirement: “{quote}”")
            for limitation in explanation["limitations"]:
                st.caption(limitation)

# --- TAB 2: GenAI STAR Resume Tailoring ---
with tab2:
    st.subheader("✨ STAR-Format Resume Bullet Optimizer")
    st.markdown("Transform passive statements into quantifiable, high-impact STAR bullets injecting target skills.")

    default_bullets = [
        "Worked on backend API development using Python.",
        "Trained machine learning models and improved accuracy.",
        "Helped the team with docker deployments and database queries.",
    ]
    user_bullets_input = st.text_area(
        "Enter raw bullet points (one per line):",
        value="\n".join(default_bullets),
        height=140,
    )

    if st.button("✨ Optimize Bullets with GenAI", type="primary"):
        bullets = [b.strip() for b in user_bullets_input.split("\n") if b.strip()]
        missing_skills = st.session_state.get("analysis_data", {}).get("missing_skills", ["MLflow", "Kubernetes", "AWS"])
        target_role = st.session_state.get("target_role", "Machine Learning Engineer")

        with st.spinner("Applying STAR framework and weaving target skills..."):
            try:
                resp = requests.post(
                    f"{api_url}/genai/rewrite-bullets",
                    json={
                        "bullet_points": bullets,
                        "target_role": target_role,
                        "target_skills": missing_skills,
                    },
                    timeout=180,
                )
                if resp.status_code == 200:
                    rewrites = resp.json()["rewrites"]
                    for idx, r in enumerate(rewrites, 1):
                        with st.expander(f"Bullet #{idx}: {r.get('rewritten', '')[:60]}...", expanded=True):
                            st.markdown(f"**Original:** {r.get('original', '')}")
                            st.markdown(f"**🌟 Polished STAR Bullet:**\n\n> {r.get('rewritten', '')}")
                            if "star_breakdown" in r and isinstance(r["star_breakdown"], dict):
                                b = r["star_breakdown"]
                                st.caption(f"**Situation/Task:** {b.get('situation_task', '')} | **Action:** {b.get('action', '')} | **Result:** {b.get('result', '')}")
                else:
                    st.error(f"Error: {resp.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")

# --- TAB 3: Personalized Learning Roadmap ---
with tab3:
    st.subheader("🗺️ Actionable Learning Roadmap")
    roadmap_items = st.session_state.get("analysis_data", {}).get("roadmap", [])
    if roadmap_items:
        for item in roadmap_items:
            with st.container(border=True):
                st.markdown(
                    f"**Step {item['step']}: {item['skill']}** · "
                    f"{item.get('priority', 'medium').title()} priority"
                )
                for resource in item.get("resources", []):
                    st.markdown(f"[{resource['title']}]({resource['url']})")
                for project in item.get("project_suggestions", []):
                    st.write(f"Project: {project}")
    else:
        st.info("Run an analysis in Tab 1 to generate a customized roadmap for your missing skills.")

# --- TAB 4: Mock Interview Prep ---
with tab4:
    st.subheader("🎯 Custom Interview Prep Kit")
    analysis_data = st.session_state.get("analysis_data", {})
    questions = st.session_state.get("interview_prep", [])
    if analysis_data and st.button("Generate Interview Prep", type="primary"):
        with st.spinner("Generating interview questions with the local model..."):
            try:
                response = requests.post(
                    f"{api_url}/genai/interview-prep",
                    json={
                        "candidate_role": analysis_data.get("predicted_role") or "Unclassified",
                        "target_role": st.session_state.get("target_role", "Machine Learning Engineer"),
                        "missing_skills": analysis_data.get("missing_skills", []),
                        "job_description_snippet": jd_text_input[:400],
                    },
                    timeout=180,
                )
                if response.status_code == 200:
                    questions = response.json()["questions"]
                    st.session_state["interview_prep"] = questions
                else:
                    st.error(f"Interview generation failed ({response.status_code}): {response.text}")
            except requests.RequestException as e:
                st.error(f"Interview generation request failed: {e}")
    if questions:
        for idx, q in enumerate(questions, 1):
            with st.expander(f"Q{idx} [{q.get('category', 'Technical')}]: {q.get('skill_tested', '')}", expanded=True):
                st.markdown(f"### {q.get('question', '')}")
                st.markdown(f"**🔍 What Interviewers Look For:** {q.get('what_interviewer_looks_for', '')}")
                st.markdown(f"**💡 Sample STAR Talking Point:** {q.get('sample_star_talking_point', '')}")
    else:
        st.info("Run an analysis in Tab 1 or trigger interview prep to see customized questions.")

# --- TAB 5: Hybrid Job Search ---
with tab5:
    st.subheader("🔍 Hybrid Semantic + Keyword Job Search (ChromaDB + BM25)")
    search_query = st.text_input("Enter Search Query (or use your resume text):", value="Machine Learning Engineer PyTorch Kubernetes AWS")
    top_k = st.slider("Number of Top Jobs to Retrieve", min_value=1, max_value=10, value=5)

    if st.button("🔎 Search Jobs with RRF Hybrid Retrieval"):
        try:
            resp = requests.post(f"{api_url}/search/hybrid", json={"query": search_query, "top_k": top_k})
            if resp.status_code == 200:
                results = resp.json()["results"]
                if results:
                    for r in results:
                        st.markdown(f"#### Match Score: `{r.get('match_score', 0.0)}` (RRF: `{r.get('rrf_score', 0.0)}`)")
                        st.write(r.get("text", ""))
                        st.markdown("---")
                else:
                    st.warning("No jobs currently indexed in Vector DB. Use `/search/index-jobs` or run `scripts/train_pipeline.py` to populate job postings.")
            else:
                st.error(f"Search API Error: {resp.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")

    analysis_data = st.session_state.get("analysis_data")
    if analysis_data and st.button("✨ Generate evidence-grounded recommendations", type="primary"):
        profile_text = st.session_state.get("resume_text", "")
        if not profile_text:
            st.error("Run profile analysis first so recommendations can cite your resume evidence.")
        else:
            with st.spinner("Retrieving jobs and asking Gemma for source-grounded fit explanations..."):
                try:
                    response = requests.post(
                        f"{api_url}/search/recommend",
                        json={
                            "profile_text": profile_text,
                            "target_role": st.session_state.get("target_role", target_role_input),
                            "top_k": min(top_k, 3),
                        },
                        timeout=180,
                    )
                    if response.status_code == 200:
                        st.session_state["rag_recommendations"] = response.json()["recommendations"]
                    else:
                        st.error(f"Recommendation request failed ({response.status_code}): {response.text}")
                except requests.Timeout:
                    st.error("The local model timed out while preparing recommendations. Try fewer jobs or retry after the model is warm.")
                except requests.RequestException as e:
                    st.error(f"Could not reach the recommendation service: {e}")

    for recommendation in st.session_state.get("rag_recommendations", []):
        with st.container(border=True):
            st.markdown(f"**{recommendation['title']}** · retrieval score {recommendation['retrieval_score']}")
            st.write(recommendation["fit_summary"])
            st.caption(f"Evidence quality: {recommendation['evidence_quality_score']}/100 · {recommendation['evidence_quality_note']}")
            st.markdown("**Candidate evidence**")
            for quote in recommendation["candidate_evidence"]:
                st.write(f"> {quote}")
            st.markdown("**Job requirements evidence**")
            for quote in recommendation["job_evidence"]:
                st.write(f"> {quote}")
            if recommendation["skill_gaps"]:
                st.write("Potential gaps: " + ", ".join(recommendation["skill_gaps"]))
            with st.expander("Evidence rubric"):
                for criterion, score in recommendation["evidence_quality"].items():
                    st.write(f"{criterion.title()}: {score}/2")
