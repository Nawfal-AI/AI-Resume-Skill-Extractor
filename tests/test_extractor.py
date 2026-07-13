import pytest

from resume_skill_extractor.extractor import ResumeSkillExtractor, PDFExtractionError


@pytest.fixture(scope="module")
def extractor():
    # use_spacy model may not be installed in CI -- extractor falls back
    # to regex-only automatically, and these tests don't depend on spaCy
    # being present.
    return ResumeSkillExtractor()


def test_extract_skills_regex_finds_known_skill(extractor):
    text = "Experienced with Python, PyTorch, and AWS."
    found = extractor.extract_skills_regex(text)
    assert "python" in found
    assert "pytorch" in found
    assert "aws" in found


def test_extract_skills_regex_respects_word_boundaries(extractor):
    # "r" is a known skill (the R language) -- must not match inside "product"
    text = "We shipped a great product this quarter."
    found = extractor.extract_skills_regex(text)
    assert "r" not in found


def test_extract_skills_hybrid_categorizes_correctly(extractor):
    text = "Skilled in Python and PostgreSQL, deployed via Docker."
    result = extractor.extract_skills_hybrid(text)
    assert "python" in result.get("programming", [])
    assert "postgresql" in result.get("databases", [])
    assert "docker" in result.get("cloud_platforms", [])


def test_extract_skills_hybrid_empty_text_returns_empty(extractor):
    result = extractor.extract_skills_hybrid("")
    assert result == {}


def test_extract_text_from_pdf_raises_on_missing_file(extractor):
    with pytest.raises(PDFExtractionError):
        extractor.extract_text_from_pdf("does_not_exist.pdf")
