"""
This is your original ResumeSkillExtractor class from the Kaggle notebook,
kept functionally identical (same skills_db, same regex/spaCy/hybrid logic)
but restructured for production use:

  - No hardcoded /kaggle/input or /kaggle/working paths -- takes any path
  - Logging instead of print() -- so a caller (like the dashboard, or a
    future API) can capture/route output instead of it going to stdout
  - Raises exceptions on real failures instead of silently printing an
    error and returning empty results -- a caller needs to know a file
    failed to process, not just see a printed message it might not read
  - Loads the skills taxonomy from an external JSON file (skills_db.json)
    instead of a method body, so you can edit the skill list without
    touching code -- and so tests can load a smaller fixture taxonomy
"""
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Union

import pdfplumber

logger = logging.getLogger(__name__)

DEFAULT_SKILLS_DB_PATH = Path(__file__).parent / "skills_db.json"


class PDFExtractionError(Exception):
    """Raised when a PDF can't be read or contains no extractable text."""


class ResumeSkillExtractor:
    def __init__(self, skills_db_path: Union[str, Path, None] = None, spacy_model: str = "en_core_web_sm"):
        self.nlp = None
        self._has_spacy = False
        try:
            import spacy
            self.nlp = spacy.load(spacy_model)
            self._has_spacy = True
        except ImportError:
            logger.warning(
                "spaCy is not installed -- falling back to regex-only "
                "extraction. Run: pip install spacy && python -m spacy download %s",
                spacy_model,
            )
        except OSError:
            logger.warning(
                "spaCy model '%s' not installed -- falling back to regex-only "
                "extraction. Run: python -m spacy download %s",
                spacy_model, spacy_model,
            )

        self.skills_db = self._load_skills_database(skills_db_path or DEFAULT_SKILLS_DB_PATH)

    def _load_skills_database(self, path: Union[str, Path]) -> Dict[str, List[str]]:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Skills database not found at {path}. Expected a JSON file "
                f"mapping category -> list of skills."
            )
        with open(path, "r") as f:
            return json.load(f)

    def extract_text_from_pdf(self, pdf_path: Union[str, Path]) -> str:
        """Extract text from a PDF file. Raises PDFExtractionError instead of
        printing and returning empty string, so callers can't silently treat
        a broken PDF as 'zero skills found'."""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise PDFExtractionError(f"Could not read PDF '{pdf_path}': {e}") from e

        if not text.strip():
            raise PDFExtractionError(
                f"'{pdf_path}' produced no extractable text -- it may be a "
                f"scanned/image-only PDF that needs OCR first."
            )
        return text

    def clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.lower()

    def extract_skills_regex(self, text: str) -> List[str]:
        found_skills = []
        text = self.clean_text(text)
        all_skills = [s for skills in self.skills_db.values() for s in skills]
        for skill in all_skills:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, text):
                found_skills.append(skill)
        return list(set(found_skills))

    def extract_skills_spacy(self, text: str) -> List[str]:
        if not self._has_spacy:
            return []

        doc = self.nlp(text)
        found_skills = []

        searchable = self.skills_db.get("programming", []) + self.skills_db.get("ml_frameworks", [])
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            for skill in searchable:
                if skill in chunk_text:
                    found_skills.append(skill)

        for ent in doc.ents:
            ent_text = ent.text.lower()
            if ent_text in self.skills_db.get("programming", []):
                found_skills.append(ent_text)

        return list(set(found_skills))

    def extract_skills_hybrid(self, text: str) -> Dict[str, List[str]]:
        regex_skills = self.extract_skills_regex(text)
        spacy_skills = self.extract_skills_spacy(text)

        categorized_skills: Dict[str, List[str]] = {}
        for skill in set(regex_skills + spacy_skills):
            for category, skills in self.skills_db.items():
                if skill in skills:
                    categorized_skills.setdefault(category, []).append(skill)

        logger.info("Extracted %d skills across %d categories",
                    sum(len(v) for v in categorized_skills.values()), len(categorized_skills))
        return categorized_skills

    def process_resume(self, pdf_path: Union[str, Path]) -> Dict[str, List[str]]:
        """Convenience method: PDF path in, categorized skills out."""
        text = self.extract_text_from_pdf(pdf_path)
        return self.extract_skills_hybrid(text)
