🔗 Live demo: https://your-app-name.streamlit.app


# AI Resume Skill Extractor

An NLP tool that extracts technical skills from PDF resumes and scores how
well a resume matches a specific job description, with a Streamlit dashboard
on top.

This began as a Kaggle notebook (kept for history in `legacy/`) and has been
restructured into a proper, tested, containerized Python package.

## What it does

- Extracts text from a resume PDF
- Identifies technical skills via regex + spaCy (falls back to regex-only if
  spaCy isn't installed — see `src/resume_skill_extractor/extractor.py`)
- Categorizes skills (programming, web frameworks, ML frameworks, databases,
  cloud platforms, data tools — see `skills_db.json`)
- Compares extracted skills against a pasted job description: keyword
  overlap %, TF-IDF semantic similarity %, and a missing-skills list
- Visualizes everything in a Streamlit dashboard, with CSV export

## Project structure

```
resume-skill-extractor/
├── src/resume_skill_extractor/    # the actual package
│   ├── __init__.py
│   ├── extractor.py               # PDF -> text -> categorized skills
│   ├── matcher.py                 # resume vs. job description comparison
│   ├── logging_config.py          # central logging setup
│   └── skills_db.json             # editable skill taxonomy
├── tests/
│   ├── test_extractor.py
│   └── test_matcher.py
├── sample_resumes/                # example PDFs to try it on
├── legacy/
│   └── ai-resume-skill-extractor.ipynb   # original Kaggle notebook, kept for history
├── app.py                         # Streamlit dashboard entrypoint
├── pyproject.toml                 # packaging + dependencies
├── requirements.txt               # plain pip list (Streamlit Cloud reads this)
├── Dockerfile
├── .github/workflows/ci.yml       # runs tests on every push
├── .gitignore
└── README.md
```

## Running it locally

```bash
git clone https://github.com/Nawfal-AI/AI-Resume-Skill-Extractor.git
cd AI-Resume-Skill-Extractor
pip install -e ".[dashboard]"
python -m spacy download en_core_web_sm   # optional — falls back to regex-only without it
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

CI runs this automatically on every push via GitHub Actions
(`.github/workflows/ci.yml`).

## What changed from the original notebook

| Original notebook | This version |
|---|---|
| Hardcoded `/kaggle/input`, `/kaggle/working` paths | Works with any path, anywhere |
| `print()` for all output | Proper logging (`logging_config.py`) |
| Silent `try/except` that prints and returns empty results | Raises `PDFExtractionError` so failures are visible to the caller |
| Skills list hardcoded inside a method | External, editable `skills_db.json` |
| No tests | `tests/` with pytest, run in CI |
| No packaging | Installable package via `pyproject.toml` |
| `streamlit` in requirements but never used | Actual working dashboard, `app.py` |
| No job-description matching | `matcher.py` — new capability |
| No deployment story | `Dockerfile` + Streamlit Community Cloud-ready |

## Deploying the dashboard for free

[Streamlit Community Cloud](https://streamlit.io/cloud) will deploy this
directly from the GitHub repo for free: connect your GitHub account, point it
at this repo and `app.py`, and it builds from `requirements.txt`
automatically. Good enough to link a live demo from your resume.
