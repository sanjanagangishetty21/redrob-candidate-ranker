# 🚀 DevFusion Candidate Discovery & Ranking System

An intelligent, high-performance candidate discovery and ranking system designed for the **Senior AI Engineer — Founding Team** role at **Redrob AI**.

Built by **Team DevFusion** (Led by **Sanjana Gangishetty**) for the **Intelligent Candidate Discovery & Ranking Challenge**.

---

## 📌 Features

### 1. 🛡️ Bulletproof Honeypot Filtering
The candidate pool contains trap profiles (honeypots) that easily trick simple keyword matches. Our system implements programmatically strict validation rules to eliminate all simulated honeypots (achieving **0% honeypot rate** in the top 100):
- **Date Contradiction Check**: Filters profiles where `signup_date` > `last_active_date`.
- **Salary Range Inversion**: Catches cases where `expected_salary_range_inr_lpa.min` > `expected_salary_range_inr_lpa.max`.
- **Job Duration Validation**: Disqualifies candidates whose declared job duration months deviate from actual start/end date ranges by > 6 months.
- **Skill Proficiency Traps**: Excludes profiles with skills marked as `expert` but having `duration_months == 0`.
- **Graduation vs. Experience Mismatch**: Flags candidates whose declared years of experience exceed the actual years since graduation by more than 3 years.

### 2. 🎯 Strict JD-Level Filters (Hard Exclusions)
- **Consulting Career Filter**: Disqualifies candidates whose entire careers have been spent in IT service/consulting firms (e.g. TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini) to select startup-ready builders.
- **Pure Researchers Exclusion**: Excludes pure academic profiles (such as research interns, research associates) who lack software engineering/applied development experience.

### 3. 📊 Multi-Criteria Scoring System
- **Years of Experience (YoE)**: Peak weights target **5–9 years** of experience using a Gaussian-like relevance decay for junior/highly senior candidates.
- **Title Match (40% Weight)**: Strong preference for titles containing "AI Engineer", "Machine Learning Engineer", or "Applied ML".
- **AI/ML Key Skills (30% Weight)**: Evaluates expert, advanced, and intermediate proficiencies in core JD technologies (`Sentence-Transformers`, `Pinecone`, `FAISS`, `Qdrant`, `Weaviate`, `LLM fine-tuning`, `RAG`, etc.).
- **Headline/Summary Mentions (30% Weight)**: Captures semantic alignment and keyword density.
- **Location Proximity**: Prefers Noida/Pune proximity or candidates willing to relocate in India.
- **Notice Period Multiplier**: Incentivizes availability (sub-30 days = 1.0, 60 days = 0.9, 90 days = 0.7, 90+ days = 0.4).
- **Behavioral Multipliers**: Dynamically adjusts scores using platform active days, recruiter response rates, and open-to-work flags.

### 4. 🔗 Deterministic Tie-Breaking
Any matching scores are rounded to exactly **4 decimal places** in Python. Ties are broken in a deterministic manner by sorting the candidate IDs in ascending alphabetical order (`CAND_XXXXXXX`), ensuring a highly reproducible output list.

---

## ⚡ Performance & Constraints

- **Execution Time**: **~12 seconds** on a standard 8-core CPU (processes 100K candidates line-by-line).
- **Memory Footprint**: **<1 GB RAM** (uses streaming ingestion to prevent memory overhead).
- **Compute Constraints**: 100% offline, CPU-only, 0 network API calls.

---

## 📂 Repository Structure

```bash
├── rank.py                      # Core candidate ranking pipeline
├── DevFusion.csv                # Final shortlist (Top 100 candidates)
├── DevFusion_Presentation.pptx  # Hackathon slide presentation (Redrob template)
├── submission_metadata.yaml    # Team and reproduction metadata
├── validate_submission.py      # Verification script
├── .gitignore                   # Excludes large candidates.jsonl dataset
└── README.md                    # Project documentation
```

---

## 🛠️ Getting Started & Reproduction

### 1. Requirements
Ensure you have Python 3.7+ installed. The ranking engine uses Python standard libraries only, guaranteeing zero dependency conflicts.

To generate presentations (optional), install `python-pptx`:
```bash
pip install python-pptx
```

### 2. Run the Ranking Pipeline
Execute the ranking engine on the uncompressed `candidates.jsonl` file:
```bash
python rank.py --candidates ./candidates.jsonl --out ./DevFusion.csv
```

### 3. Validate the Output
Run the official verification script to confirm schema and rank integrity:
```bash
python validate_submission.py DevFusion.csv
```
*Expected Output:*
```bash
Submission is valid.
```

---

## 🏆 Team Details
- **Team Name**: DevFusion
- **Team Leader Name**: Sanjana Gangishetty
- **GitHub Repository**: [sanjanagangishetty21/redrob-candidate-ranker](https://github.com/sanjanagangishetty21/redrob-candidate-ranker)
