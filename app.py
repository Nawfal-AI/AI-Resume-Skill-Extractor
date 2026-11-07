"""
Dashboard entrypoint. Run with: streamlit run app.py

Deliberately thin -- all real logic lives in the resume_skill_extractor
package so it can be tested without spinning up Streamlit, and so a future
API (FastAPI, etc.) could reuse the exact same extractor/matcher calls.

Streamlit Community Cloud deployment:
  - requirements.txt handles all dependencies including the spaCy model wheel
  - No secrets or environment variables required
  - Push to main branch → auto-redeploy
"""
import subprocess
import sys

# ── Ensure spaCy model is available (belt-and-suspenders for cloud deploy) ──
def _ensure_spacy_model():
    try:
        import spacy
        spacy.load("en_core_web_sm")
    except OSError:
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
            check=False,
            capture_output=True,
        )

_ensure_spacy_model()

from resume_skill_extractor.extractor import ResumeSkillExtractor, PDFExtractionError  # noqa: E402
from resume_skill_extractor.logging_config import configure_logging  # noqa: E402
from resume_skill_extractor.matcher import match_resume_to_jd  # noqa: E402

configure_logging()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Skill Extractor",
    page_icon="🔍",
    layout="wide",
)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🔍 AI Resume Skill Extractor")
st.caption(
    "Upload a resume PDF and paste a job description — get a skill overlap score, "
    "semantic similarity, and a gap analysis in seconds."
)

st.divider()

# ── Extractor (cached so the spaCy model loads once per session) ─────────────
@st.cache_resource
def get_extractor() -> ResumeSkillExtractor:
    return ResumeSkillExtractor()

extractor = get_extractor()

if not extractor._has_spacy:
    st.info(
        "Running in regex-only mode (spaCy model unavailable) — "
        "results are still accurate for the built-in skill taxonomy.",
        icon="ℹ️",
    )

# ── Inputs ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("1 · Upload resume (PDF)")
    resume_file = st.file_uploader(
        "Drop your resume PDF here",
        type=["pdf"],
        help="Max 10 MB. Text-based PDFs only (not scanned images).",
    )
    if resume_file:
        st.success(f"✅ Loaded: {resume_file.name}")

with col2:
    st.subheader("2 · Paste the job description")
    jd_text = st.text_area(
        "Job description text",
        height=220,
        placeholder="Paste the full job description here…",
    )
    if jd_text:
        word_count = len(jd_text.split())
        st.caption(f"{word_count} words")

st.divider()

# ── Sample resume shortcut ────────────────────────────────────────────────────
with st.expander("📄 Try a sample resume instead of uploading"):
    sample_choice = st.selectbox(
        "Choose a sample",
        ["— select —", "Computer Science Student", "Senior CV Scientist"],
    )
    sample_map = {
        "Computer Science Student": "sample_resumes/computer-science-student-resume-example.pdf",
        "Senior CV Scientist": "sample_resumes/senior-computer-vision-scientist-resume-example.pdf",
    }
    if sample_choice != "— select —":
        st.info(f"Sample selected: **{sample_choice}**. Click Analyze below.")

# ── Analyze button ────────────────────────────────────────────────────────────
input_ready = (resume_file or sample_choice != "— select —") and bool(jd_text.strip())
run = st.button("Analyze ▶", type="primary", disabled=not input_ready)

# ── Analysis ──────────────────────────────────────────────────────────────────
if run:
    # Resolve PDF source
    if resume_file:
        pdf_source = io.BytesIO(resume_file.read())
        source_label = resume_file.name
    else:
        pdf_source = sample_map[sample_choice]
        source_label = sample_choice

    try:
        resume_text = extractor.extract_text_from_pdf(pdf_source)
    except PDFExtractionError as e:
        st.error(str(e))
        st.stop()

    with st.spinner("Extracting and matching skills…"):
        categorized = extractor.extract_skills_hybrid(resume_text)
        result = match_resume_to_jd(resume_text, jd_text, extractor)

    # ── Metrics row ──────────────────────────────────────────────────────────
    st.subheader(f"Results — {source_label}")
    total_skills = sum(len(v) for v in categorized.values())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Skills found", total_skills)
    m2.metric("Skill keyword overlap", f"{result.skill_overlap_pct}%")
    m3.metric("Semantic similarity (TF-IDF)", f"{result.semantic_similarity_pct}%")
    m4.metric("Missing skills flagged", len(result.missing_skills))

    st.divider()

    # ── Detail columns ───────────────────────────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.subheader("Skills found, by category")
        rows = [
            {"Skill": s, "Category": cat}
            for cat, skills in categorized.items()
            for s in skills
        ]
        df = pd.DataFrame(rows)
        if not df.empty:
            counts = df["Category"].value_counts().reset_index()
            counts.columns = ["Category", "Count"]
            st.bar_chart(counts.set_index("Category"))
            with st.expander("See all individual skills"):
                st.dataframe(df, use_container_width=True)
        else:
            st.write("No taxonomy skills matched.")

    with right:
        st.subheader("Job description gap analysis")

        st.write(f"**✅ Matched skills ({len(result.matched_skills)})**")
        if result.matched_skills:
            st.write(", ".join(result.matched_skills))
        else:
            st.write("None matched from the built-in taxonomy.")

        st.write(f"**⚠️ Skills in the JD not found in resume ({len(result.missing_skills)})**")
        if result.missing_skills:
            st.warning(", ".join(result.missing_skills))
        else:
            st.success("No gaps detected against the built-in taxonomy.")

    # ── Download ─────────────────────────────────────────────────────────────
    st.divider()
    if not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download extracted skills as CSV",
            csv,
            "extracted_skills.csv",
            "text/csv",
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Built by [Nawfal Abdul Malick](https://linkedin.com/in/nawfal-abdul-malick) · "
    "[GitHub](https://github.com/Nawfal-AI/AI-Resume-Skill-Extractor) · "
    "Powered by spaCy + scikit-learn · Deployed on Streamlit Community Cloud"
)
