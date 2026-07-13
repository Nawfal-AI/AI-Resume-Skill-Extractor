"""
Dashboard entrypoint. Run with: streamlit run app.py

Deliberately thin -- all real logic lives in the resume_skill_extractor
package so it can be tested without spinning up Streamlit, and so a future
API (FastAPI, etc.) could reuse the exact same extractor/matcher calls.
"""
import io

import pandas as pd
import streamlit as st

from resume_skill_extractor.extractor import ResumeSkillExtractor, PDFExtractionError
from resume_skill_extractor.logging_config import configure_logging
from resume_skill_extractor.matcher import match_resume_to_jd

configure_logging()

st.set_page_config(page_title="Resume Skill Extractor Dashboard", layout="wide")
st.title("Resume Skill Extractor Dashboard")
st.caption("Dashboard layer on top of the original ResumeSkillExtractor pipeline.")


@st.cache_resource
def get_extractor() -> ResumeSkillExtractor:
    return ResumeSkillExtractor()


extractor = get_extractor()
if not extractor._has_spacy:
    st.info("Running in regex-only mode (spaCy model not installed) — "
            "results are still accurate for the built-in skill taxonomy.", icon="ℹ️")

col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Upload a resume (PDF)")
    resume_file = st.file_uploader("Resume PDF", type=["pdf"])
with col2:
    st.subheader("2. Paste the job description")
    jd_text = st.text_area("Job description text", height=220)

run = st.button("Analyze", type="primary", disabled=not (resume_file and jd_text))

if run:
    try:
        resume_text = extractor.extract_text_from_pdf(io.BytesIO(resume_file.read()))
    except PDFExtractionError as e:
        st.error(str(e))
        st.stop()

    with st.spinner("Extracting and matching skills..."):
        categorized = extractor.extract_skills_hybrid(resume_text)
        result = match_resume_to_jd(resume_text, jd_text, extractor)

    st.divider()
    total_skills = sum(len(v) for v in categorized.values())
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Skills found", total_skills)
    m2.metric("Skill keyword overlap", f"{result.skill_overlap_pct}%")
    m3.metric("Semantic similarity", f"{result.semantic_similarity_pct}%")
    m4.metric("Missing skills flagged", len(result.missing_skills))

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("Skills found, by category")
        rows = [{"Skill": s, "Category": cat} for cat, skills in categorized.items() for s in skills]
        df = pd.DataFrame(rows)
        if not df.empty:
            counts = df["Category"].value_counts().reset_index()
            counts.columns = ["Category", "Count"]
            st.bar_chart(counts.set_index("Category"))
            with st.expander("See individual skills"):
                st.dataframe(df, use_container_width=True)
        else:
            st.write("No taxonomy skills matched.")

    with right:
        st.subheader("Match against this job description")
        st.write(f"**Matched skills ({len(result.matched_skills)}):**")
        st.write(", ".join(result.matched_skills) or "None")
        st.write(f"**Skills the JD asks for but the resume doesn't show ({len(result.missing_skills)}):**")
        if result.missing_skills:
            st.warning(", ".join(result.missing_skills))
        else:
            st.success("No gaps against the built-in taxonomy.")

    st.divider()
    csv = df.to_csv(index=False).encode("utf-8") if not df.empty else b""
    st.download_button("Download extracted skills as CSV", csv, "extracted_skills.csv", "text/csv")
