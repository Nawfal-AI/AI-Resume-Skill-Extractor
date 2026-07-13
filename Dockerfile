# Production container for the dashboard. Build with:
#   docker build -t resume-skill-extractor .
# Run with:
#   docker run -p 8501:8501 resume-skill-extractor

FROM python:3.11-slim

WORKDIR /app

# System deps needed by pdfplumber's PDF parsing backend
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY app.py ./

RUN pip install --no-cache-dir -e ".[dashboard]" \
    && python -m spacy download en_core_web_sm

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
