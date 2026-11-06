# AI Resume Skill Extractor

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://nawfal-ai-ai-resume-skill-extractor.streamlit.app)
[![CI](https://github.com/Nawfal-AI/AI-Resume-Skill-Extractor/actions/workflows/ci.yml/badge.svg)](https://github.com/Nawfal-AI/AI-Resume-Skill-Extractor/actions)

> **Live demo → https://nawfal-ai-ai-resume-skill-extractor.streamlit.app**

An NLP tool that extracts technical skills from PDF resumes and scores how
well a resume matches a specific job description, with a Streamlit dashboard
deployed on Streamlit Community Cloud.

---

## What it does

- Extracts text from a resume PDF
- Identifies technical skills via regex + spaCy (falls back to regex-only if
  spaCy isn't installed — see `src/resume_skill_extractor/extractor.py`)
- Categorizes skills (programming, web frameworks, ML frameworks, databases,
  cloud platforms, data tools — see `skills_db.json`)
- Compares extracted skills against a pasted job description: keyword
  overlap %, TF-IDF semantic similarity %, and a missing-skills list
- Visualizes everything in a Streamlit dashboard, with CSV export

## Tech stack

| Layer | Technology |
|---|---|
| NLP extraction | spaCy `en_core_web_sm` + regex fallback |
| Semantic matching | scikit-learn TF-IDF cosine similarity |
| PDF parsing | pdfplumber |
| Dashboard | Streamlit |
| Cloud deployment | Streamlit Community Cloud (free tier, CI/CD via git push) |
| Containerization | Docker |
| Testing & CI | pytest + GitHub Actions |
| Packaging | pyproject.toml (installable package) |

## Project structure

```
AI-Resume-Skill-Extractor/
├── src/resume_skill_extractor/    # the actual package
│   ├── __init__.py
│   ├── extractor.py               # PDF -> text -> categorized skills
│   ├── matcher.py                 # resume vs. job description comparison
│   ├── logging_config.py          # central logging setup
│   └── skills_db.json             # editable skill taxonomy
├── tests/
│   ├── test_extractor.py
│   └── test_matcher.py
├── sample_resumes/                # example PDFs to try
├── legacy/
│   └── ai-resume-skill-extractor.ipynb   # original Kaggle notebook
├── .streamlit/
│   └── config.toml                # Streamlit theme + server settings
├── app.py                         # Streamlit dashboard entrypoint
├── pyproject.toml                 # packaging + dependencies
├── requirements.txt               # Streamlit Community Cloud reads this
└── Dockerfile                     # local Docker deployment
```

## Running locally

```bash
git clone https://github.com/Nawfal-AI/AI-Resume-Skill-Extractor.git
cd AI-Resume-Skill-Extractor
pip install -e ".[dashboard]"
python -m spacy download en_core_web_sm   # optional — falls back to regex-only
streamlit run app.py
```

Open `http://localhost:8501`, upload a PDF from `sample_resumes/`, paste any
job description, and click Analyze.

## Running with Docker

```bash
docker build -t resume-skill-extractor .
docker run -p 8501:8501 resume-skill-extractor
```

## Running the tests

```bash
pip install -e ".[dev]"
pytest --cov=resume_skill_extractor
```

CI runs this automatically on every push via GitHub Actions.

## Cloud deployment

This app is deployed for free on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Connected GitHub repo → Streamlit Cloud reads `requirements.txt` and runs `streamlit run app.py`
2. Every `git push` to `main` triggers an automatic redeploy (continuous deployment)
3. No server management, no Docker needed on the cloud side
4. Live at: **https://nawfal-ai-ai-resume-skill-extractor.streamlit.app**

## What changed from the original notebook

| Original notebook | This version |
|---|---|
| Hardcoded `/kaggle/input` paths | Works with any path, anywhere |
| `print()` for all output | Proper logging (`logging_config.py`) |
| Silent `try/except` returning empty results | Raises `PDFExtractionError` |
| Skills list hardcoded inside a method | External, editable `skills_db.json` |
| No tests | `tests/` with pytest, run in CI |
| No packaging | Installable package via `pyproject.toml` |
| No deployment story | Docker + Streamlit Community Cloud (live URL) |
| No job-description matching | `matcher.py` — TF-IDF gap analysis |
