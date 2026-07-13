"""
New capability: compares extracted resume skills against a job description.
Not in your original notebook -- this is the piece that turns "list of
skills found" into "how well does this resume fit this specific job."
"""
import logging
from dataclasses import dataclass
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from resume_skill_extractor.extractor import ResumeSkillExtractor

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    matched_skills: List[str]
    missing_skills: List[str]
    skill_overlap_pct: float
    semantic_similarity_pct: float


def _flatten(categorized: Dict[str, List[str]]) -> set:
    return {s for skills in categorized.values() for s in skills}


def semantic_similarity(resume_text: str, jd_text: str) -> float:
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform([resume_text, jd_text])
    score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return round(score * 100, 1)


def match_resume_to_jd(resume_text: str, jd_text: str, extractor: ResumeSkillExtractor) -> MatchResult:
    resume_skills = _flatten(extractor.extract_skills_hybrid(resume_text))
    jd_skills = _flatten(extractor.extract_skills_hybrid(jd_text))

    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)
    overlap_pct = round(100 * len(matched) / len(jd_skills), 1) if jd_skills else 0.0
    sem_sim = semantic_similarity(resume_text, jd_text)

    logger.info("Match result: %.1f%% skill overlap, %.1f%% semantic similarity",
                overlap_pct, sem_sim)

    return MatchResult(
        matched_skills=matched,
        missing_skills=missing,
        skill_overlap_pct=overlap_pct,
        semantic_similarity_pct=sem_sim,
    )
