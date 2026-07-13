import pytest

from resume_skill_extractor.extractor import ResumeSkillExtractor
from resume_skill_extractor.matcher import match_resume_to_jd


@pytest.fixture(scope="module")
def extractor():
    return ResumeSkillExtractor()


def test_match_identifies_overlap_and_gaps(extractor):
    resume_text = "Proficient in Python and Docker."
    jd_text = "Looking for someone with Python, Docker, and Kubernetes experience."

    result = match_resume_to_jd(resume_text, jd_text, extractor)

    assert "python" in result.matched_skills
    assert "docker" in result.matched_skills
    assert "kubernetes" in result.missing_skills
    assert 0 <= result.skill_overlap_pct <= 100
    assert 0 <= result.semantic_similarity_pct <= 100


def test_match_perfect_overlap_scores_100_percent(extractor):
    text = "Python, Docker, AWS."
    result = match_resume_to_jd(text, text, extractor)
    assert result.skill_overlap_pct == 100.0
    assert result.missing_skills == []
