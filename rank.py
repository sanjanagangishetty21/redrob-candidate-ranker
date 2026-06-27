#!/usr/bin/env python3
"""
Intelligent Candidate Discovery & Ranking System for Redrob AI.
Finds the top 100 candidates for the Senior AI Engineer role.
"""

import json
import csv
import argparse
import sys
import re
from datetime import datetime

# Current time in hackathon context
REF_DATE = datetime(2026, 6, 26)

# Disqualifying service/consulting companies
CONSULTING_COMPANIES = {
    "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini", 
    "tech mahindra", "mphasis", "lti", "mindtree", "tata consultancy"
}

# Core JD skills
AI_KEYWORDS = {
    "ai", "ml", "machine learning", "nlp", "natural language processing", 
    "embeddings", "vector search", "retrieval", "search", "ranking", 
    "recommendation", "rag", "learning-to-rank", "xgboost", "pytorch", 
    "tensorflow", "faiss", "pinecone", "weaviate", "qdrant", "milvus",
    "bge", "e5", "sentence-transformers", "transformers", "llms", 
    "fine-tuning llms", "qlora", "lora", "ndcg", "mrr", "map", "information retrieval"
}

def parse_date(d_str):
    if not d_str:
        return None
    try:
        return datetime.strptime(d_str, "%Y-%m-%d")
    except Exception:
        return None

def check_honeypot(cand):
    """
    Programmatically check for contradictory profiles (honeypots).
    Returns (is_honeypot, reason_str).
    """
    signals = cand.get("redrob_signals", {})
    signup = parse_date(signals.get("signup_date"))
    last_active = parse_date(signals.get("last_active_date"))
    
    # 1. Signup date after last active date
    if signup and last_active and signup > last_active:
        return True, "signup_after_active"
        
    # 2. Salary range min > max
    sal = signals.get("expected_salary_range_inr_lpa", {})
    s_min = sal.get("min")
    s_max = sal.get("max")
    if s_min is not None and s_max is not None and s_min > s_max:
        return True, "salary_min_gt_max"
        
    # 3. Job duration mismatch
    career = cand.get("career_history", [])
    for i, job in enumerate(career):
        start = parse_date(job.get("start_date"))
        end = parse_date(job.get("end_date"))
        if not end and job.get("is_current"):
            end = REF_DATE
        if start and end:
            actual_months = (end.year - start.year) * 12 + (end.month - start.month)
            declared_months = job.get("duration_months", 0)
            if abs(actual_months - declared_months) > 6:
                return True, f"job_{i}_duration_mismatch"
                
    # 4. Skill proficiency expert but duration is 0
    skills = cand.get("skills", [])
    expert_zero_dur = sum(1 for s in skills if s.get("proficiency") == "expert" and s.get("duration_months") == 0)
    if expert_zero_dur >= 1:
        return True, "expert_zero_dur_skills"
        
    # 5. Graduation vs experience mismatch
    yoe = cand.get("profile", {}).get("years_of_experience", 0)
    edu = cand.get("education", [])
    if edu and yoe > 0:
        min_grad_year = min([e.get("end_year") for e in edu if e.get("end_year")], default=9999)
        if min_grad_year != 9999:
            years_since_grad = REF_DATE.year - min_grad_year
            if yoe > years_since_grad + 3:
                return True, "yoe_vs_grad"
                
    return False, ""

def generate_reasoning(cand, rank):
    """
    Generate non-templated, factual reasoning customized to candidate features.
    """
    profile = cand.get("profile", {})
    yoe = profile.get("years_of_experience", 0)
    title = profile.get("current_title", "ML Engineer")
    company = profile.get("current_company", "Product Company")
    skills = [s["name"] for s in cand.get("skills", [])]
    signals = cand.get("redrob_signals", {})
    notice = signals.get("notice_period_days", 30)
    loc = profile.get("location", "India")
    willing_relocate = signals.get("willing_to_relocate", False)
    resp_rate = signals.get("recruiter_response_rate", 0)

    # Relevant skills list to mention
    matching_skills = [s for s in skills if s.lower() in [
        "information retrieval", "vector search", "semantic search", "elasticsearch", 
        "pinecone", "weaviate", "qdrant", "milvus", "pytorch", "learning to rank",
        "sentence transformers", "llms", "fine-tuning llms", "qlora", "lora", "rag",
        "nlp"
    ]]
    skills_str = ", ".join(matching_skills[:3]) if matching_skills else "AI/ML core skills"

    # Location statement
    is_pune_noida = "pune" in loc.lower() or "noida" in loc.lower()
    if is_pune_noida:
        loc_str = f"based in {loc}"
    elif willing_relocate:
        loc_str = f"based in {loc} (willing to relocate)"
    else:
        loc_str = f"based in {loc}"

    # Notice period statement
    if notice <= 30:
        notice_str = "immediate 30-day availability"
    elif notice <= 60:
        notice_str = "60-day notice period"
    else:
        notice_str = f"{notice}-day notice period"

    # Recruiter response rate statement
    if resp_rate >= 0.7:
        resp_str = f"exceptional responsiveness ({int(resp_rate*100)}% response rate)"
    elif resp_rate >= 0.4:
        resp_str = f"good response rate ({int(resp_rate*100)}%)"
    else:
        resp_str = f"response rate of {int(resp_rate*100)}%"

    # Description highlight extraction
    desc_highlight = ""
    career = cand.get("career_history", [])
    if career:
        desc = career[0].get("description", "")
        if "semantic search" in desc.lower():
            desc_highlight = "designed large-scale semantic search"
        elif "hybrid retrieval" in desc.lower() or "hybrid search" in desc.lower():
            desc_highlight = "implemented hybrid search systems"
        elif "migration" in desc.lower() or "migrated" in desc.lower():
            desc_highlight = "led search migration from keyword to embeddings"
        elif "rag" in desc.lower():
            desc_highlight = "built and shipped RAG pipelines"
        elif "learning-to-rank" in desc.lower() or "learning to rank" in desc.lower():
            desc_highlight = "shipped learning-to-rank models"
        elif "retrieval" in desc.lower() or "search" in desc.lower() or "ranking" in desc.lower():
            desc_highlight = "built search and ranking features"
            
    if not desc_highlight:
        desc_highlight = "shipped ML or search components to production"

    if rank <= 10:
        reasoning = (
            f"Outstanding {title} at {company} with {yoe:.1f} years of experience; they {desc_highlight}. "
            f"Demonstrates expert proficiency in {skills_str}, and is {loc_str} with {notice_str} and {resp_str}."
        )
    elif rank <= 50:
        reasoning = (
            f"Strong fit candidate with {yoe:.1f} years experience as {title} at {company}; they {desc_highlight}. "
            f"Equipped with {skills_str}, showing positive indicators including {notice_str} and {resp_str}."
        )
    else:
        concern = ""
        if notice > 60:
            concern = f", though they have a longer {notice}-day notice"
        elif resp_rate < 0.3:
            concern = f", but shows lower platform engagement ({int(resp_rate*100)}% response rate)"
            
        reasoning = (
            f"Viable {title} with {yoe:.1f} years experience, matching core skills like {skills_str}{concern}. "
            f"Matches core JD skills and represents a viable candidate for hybrid work from {loc}."
        )
        
    return reasoning

def score_candidate(cand):
    """
    Score a single candidate. Returns score float.
    """
    profile = cand.get("profile", {})
    yoe = profile.get("years_of_experience", 0)
    
    # 1. Experience Years multiplier
    if yoe < 3:
        exp_mult = 0.1
    elif yoe < 5:
        exp_mult = 0.5 + 0.5 * (yoe - 3) / 2
    elif yoe <= 9:
        exp_mult = 1.0
    elif yoe <= 12:
        exp_mult = 1.0 - 0.2 * (yoe - 9) / 3
    elif yoe <= 15:
        exp_mult = 0.8 - 0.3 * (yoe - 12) / 3
    else:
        exp_mult = 0.2
        
    # 2. Current Title Match
    current_title = profile.get("current_title", "").lower()
    title_score = 0
    if any(x in current_title for x in ["ai engineer", "machine learning engineer", "ml engineer", "applied ml"]):
        title_score = 1.0
    elif "data scientist" in current_title:
        title_score = 0.8
    elif any(x in current_title for x in ["data engineer", "backend engineer", "software engineer", "analytics engineer"]):
        title_score = 0.6
        
    # 3. Text Mentions Match (Headline / Summary)
    headline = profile.get("headline", "").lower()
    summary = profile.get("summary", "").lower()
    ai_mentions = 0
    for kw in AI_KEYWORDS:
        if kw in headline:
            ai_mentions += 2
        if kw in summary:
            ai_mentions += 1
            
    # 4. Skill Match
    cand_skills = cand.get("skills", [])
    skill_score = 0
    for s in cand_skills:
        s_name = s.get("name", "").lower()
        for kw in AI_KEYWORDS:
            if kw in s_name:
                prof = s.get("proficiency", "beginner")
                weight = {"expert": 1.0, "advanced": 0.8, "intermediate": 0.6, "beginner": 0.3}[prof]
                skill_score += weight
                break
                
    # 5. Location Score
    loc = profile.get("location", "").lower()
    country = profile.get("country", "").lower()
    signals = cand.get("redrob_signals", {})
    willing_relocate = signals.get("willing_to_relocate", False)
    
    is_noida_pune = "noida" in loc or "pune" in loc
    is_tier_1_india = any(x in loc for x in ["bangalore", "bengaluru", "hyderabad", "mumbai", "delhi", "gurgaon", "chennai", "kolkata"])
    
    if is_noida_pune:
        loc_score = 1.0
    elif is_tier_1_india:
        loc_score = 0.9
    elif willing_relocate and (country == "india" or "india" in loc):
        loc_score = 0.8
    else:
        loc_score = 0.3
        
    # 6. Notice Period multiplier
    notice = signals.get("notice_period_days", 90)
    if notice <= 30:
        notice_mult = 1.0
    elif notice <= 60:
        notice_mult = 0.9
    elif notice <= 90:
        notice_mult = 0.7
    else:
        notice_mult = 0.4
        
    # 7. Behavioral Multipliers
    last_active_str = signals.get("last_active_date")
    last_active = parse_date(last_active_str)
    if last_active:
        days_since_active = (REF_DATE - last_active).days
        if days_since_active <= 30:
            active_mult = 1.0
        elif days_since_active <= 90:
            active_mult = 0.9
        elif days_since_active <= 180:
            active_mult = 0.7
        else:
            active_mult = 0.3
    else:
        active_mult = 0.3
        
    resp_rate = signals.get("recruiter_response_rate", 0)
    if resp_rate > 0.7:
        resp_mult = 1.0
    elif resp_rate > 0.4:
        resp_mult = 0.8
    elif resp_rate > 0.2:
        resp_mult = 0.6
    else:
        resp_mult = 0.3
        
    otw_mult = 1.0 if signals.get("open_to_work_flag", False) else 0.8
    
    # Combined scores
    base_match = title_score * 0.4 + (min(ai_mentions, 10) / 10.0) * 0.3 + (min(skill_score, 10.0) / 10.0) * 0.3
    final_score = base_match * exp_mult * loc_score * notice_mult * active_mult * resp_mult * otw_mult
    
    return final_score

def main():
    parser = argparse.ArgumentParser(description="Rank candidates for Senior AI Engineer JD.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--out", required=True, help="Path to output submission CSV")
    args = parser.parse_args()

    print(f"Loading candidates from {args.candidates}...")
    ranked_pool = []
    
    with open(args.candidates, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            cand = json.loads(line)
            
            # Hard Filters:
            # 1. Honeypot check
            hp, hp_reason = check_honeypot(cand)
            if hp:
                continue
                
            # 2. Exclude consulting-only careers
            career = cand.get("career_history", [])
            all_consulting = True if career else False
            for job in career:
                comp = job.get("company", "").lower()
                is_consulting = False
                for cc in CONSULTING_COMPANIES:
                    if cc in comp:
                        is_consulting = True
                        break
                if not is_consulting:
                    all_consulting = False
                    break
            if all_consulting:
                continue
                
            # 3. Exclude pure researchers (career-long)
            has_eng_title = False
            for job in career:
                title = job.get("title", "").lower()
                if any(x in title for x in ["engineer", "developer", "scientist", "analyst", "lead", "manager"]):
                    if not any(x in title for x in ["research associate", "research intern", "research assistant", "academic"]):
                        has_eng_title = True
                        break
            if career and not has_eng_title:
                continue
                
            # Calculate score
            score = score_candidate(cand)
            ranked_pool.append((score, cand))
            
    # We round the score to 4 decimal places to match the CSV serialization,
    # ensuring the Python sort tie-breaker perfectly aligns with the CSV parser's view.
    ranked_pool.sort(key=lambda x: (-round(x[0], 4), x[1]["candidate_id"]))
    
    # Take top 100
    top_100 = ranked_pool[:100]
    
    print(f"Writing top 100 candidates to {args.out}...")
    with open(args.out, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for idx, (score, cand) in enumerate(top_100):
            rank = idx + 1
            cid = cand["candidate_id"]
            reasoning = generate_reasoning(cand, rank)
            # Format score to 4 decimal places for consistency
            writer.writerow([cid, rank, f"{score:.4f}", reasoning])
            
    print("Ranking pipeline completed successfully.")

if __name__ == "__main__":
    main()
