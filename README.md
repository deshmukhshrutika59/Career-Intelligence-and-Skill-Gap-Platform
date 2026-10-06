# Career Intelligence and Skill Gap Platform

Analyzes a resume, GitHub profile, and target job description to extract skills,
classify career domain, predict job-role suitability, recommend missing skills,
rank job descriptions, and generate a personalized learning roadmap.

## Pipeline & Core Features

1. **NLP** — canonical skill ontology and alias matching with evidence spans; optionally augmented by a trained spaCy NER artifact ([nlp/skill_extractor.py](src/career_intel/nlp/skill_extractor.py))
2. **Classical ML** — TF-IDF + LogisticRegression / SVM / XGBoost role classifier ([ml/train_classical.py](src/career_intel/ml/train_classical.py))
3. **Deep Learning** — Fine-tuned DistilBERT semantic role classifier ([dl/train_bert.py](src/career_intel/dl/train_bert.py))
4. **Vector DB & Hybrid Search** — persistent ChromaDB vectors + BM25 fused via RRF; optional RAG recommendations use Gemma to explain retrieved jobs with source-verified resume/job quotes ([recommender/hybrid_search.py](src/career_intel/recommender/hybrid_search.py), [recommender/job_recommendations.py](src/career_intel/recommender/job_recommendations.py))
5. **GenAI / LLM Integration** — STAR resume bullet point optimizer and mock interview question generator ([genai/](src/career_intel/genai/))
6. **GitHub Intelligence** — Deep repo inspection, framework discovery, and dependency manifest parsing ([github_analysis/](src/career_intel/github_analysis/))
7. **Interactive Dashboard** — Streamlit UI with skill match radar/gauge charts and roadmap viewer ([frontend/app.py](frontend/app.py))
8. **Production MLOps** — MLflow tracking, PSI skill drift monitor ([evaluation/drift_monitor.py](src/career_intel/evaluation/drift_monitor.py)), and GitHub Actions CI workflow ([.github/workflows/ci.yml](.github/workflows/ci.yml))

## Project layout

```
career-intelligence-platform/
├── config/                # YAML config + logging config
├── data/                   # raw / interim / processed / external datasets
├── notebooks/              # exploration & model prototyping
├── models/                 # trained model artifacts (gitignored)
├── mlruns/                 # MLflow tracking store (gitignored)
├── src/career_intel/       # installable Python package (see below)
├── tests/                  # pytest unit/integration tests
├── scripts/                # one-off / pipeline entrypoint scripts
├── docs/                   # architecture & API docs
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### `src/career_intel` package

| Module | Responsibility |
|---|---|
| `data/` | resume/JD loading, cleaning, parsing (PDF/DOCX → text) |
| `nlp/` | spaCy NER pipeline, skill dictionary + fuzzy matching |
| `ml/` | TF-IDF feature pipeline, classical classifiers (LogReg/SVM/XGBoost) |
| `dl/` | HuggingFace DistilBERT fine-tuning + inference |
| `recommender/` | sentence-embeddings, cosine similarity, roadmap generation |
| `github_analysis/` | GitHub REST API client for profile signal extraction |
| `evaluation/` | precision/recall/F1, macro-F1, Precision@K/Recall@K, latency |
| `api/` | FastAPI app, routers, Pydantic schemas, DB access |
| `utils/` | shared logging & text utilities |

## Getting started

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
python -m spacy download en_core_web_sm
copy .env.example .env

# Run backend API
uvicorn career_intel.api.main:app --reload

# Run Streamlit Frontend Dashboard
streamlit run frontend/app.py
```

Run MLflow UI:

```powershell
mlflow ui --backend-store-uri ./mlruns
```

## Phase 1: Dataset Setup

The project includes small, project-generated demo CSVs under `data/processed/` for validating the data pipeline. They contain no personal data and are **not suitable for training, benchmarking, or reporting model quality**.

For real English job and anonymized candidate-profile samples, use the Djinni Recruitment Dataset. Its paper describes PII removal and states that the corpus is available under MIT; see the [English job subset](https://huggingface.co/datasets/lang-uk/recruitment-dataset-job-descriptions-english), [English candidate-profile subset](https://huggingface.co/datasets/lang-uk/recruitment-dataset-candidate-profiles-english), and [dataset paper](https://aclanthology.org/2024.unlp-1.2/). The importer strips email addresses, URLs, and phone-like strings, but this is not a guarantee of de-identification. Candidate outputs remain local and git-ignored; review data-protection obligations before reuse or deployment.

Stream a bounded sample (default: 2,000 rows per split):

```powershell
python scripts/import_djinni.py --limit 1000
```

Use `--jobs-only` or `--resumes-only` to import one split. The importer retains upstream titles and only assigns project role labels for exact configured aliases; other rows remain unmapped for review.

O*NET 31.0 is used as an occupational reference source for role descriptions, skills, tasks, software skills, and alternate titles. It is not a vacancy-level job-posting corpus. Download the official text database archive from [O*NET Database](https://www.onetcenter.org/database.html) into `data/external/onet_db_31_0_text.zip`, then import it:

```powershell
python scripts/import_onet.py
```

The importer creates provenance-tagged tables under `data/processed/onet_31_0/`. These generated files and the downloaded archive are excluded from Git. O*NET 31.0 Database content is licensed under CC BY 4.0; include attribution to the U.S. Department of Labor, Employment and Training Administration, link the license, and identify project modifications. See [O*NET license terms](https://www.onetcenter.org/license_db.html).

Build the project-role crosswalk after importing O*NET:

```powershell
python scripts/build_onet_role_crosswalk.py
```

The resulting `project_role_crosswalk.csv` preserves exact alternate-title evidence and flags one-to-many or approximate occupation mappings for review. Do not use it as a supervised training-label mapping until those decisions are reviewed.

Labeled resume and job-description CSVs must include `text` and `role_label`. Use unique `record_id` values when available, and include `source` and `license` provenance columns for dataset validation. Role labels must be listed in `config/career_roles.json`.

Validate the bundled demo data:

```powershell
python scripts/validate_datasets.py
```

To validate other files, pass `--resumes` and `--jobs` with their CSV paths. Keep raw third-party or personal data out of version control; check its license and privacy requirements before use.
The downloaded Djinni samples and O*NET exports are local, Git-ignored data rather than committed corpus files. O*NET occupation profiles and synthetic examples are not substitutes for vacancy-level training labels or a held-out evaluation set.

## Phase 4: Role Labeling and Classical Baseline

Prepare a local review file from imported postings:

```powershell
python scripts/prepare_role_review.py
```

The script writes `data/processed/djinni_en/role_label_review.csv`. `suggested_role` is only a title-based hint; it is not a label. Review each title and description, fill `approved_role` with a value from `config/career_roles.json`, and set `review_status` to `approved`. Leave unrelated roles pending or reject them. Do not approve a suggestion automatically.

Export only approved rows and require at least five examples per included role:

```powershell
python scripts/finalize_role_labels.py --minimum-per-role 5
```

Then train the XGBoost TF-IDF baseline from the approved dataset:

```powershell
python scripts/train_pipeline.py --input data/processed/djinni_en/job_descriptions_labeled.csv
```

The trainer validates role names, non-empty text, per-class counts, and stratified split size. It logs accuracy and macro-F1 plus per-class precision/recall/F1 to MLflow. This demo classifier setup uses vacancy data; suitable, labeled resume examples and a distinct held-out test set are still needed for broader role suitability evaluation.

The same vacancy sample can populate the persistent Chroma + BM25 index without role labels:

```powershell
python scripts/index_job_descriptions.py --input data/processed/djinni_en/job_descriptions.csv
```

BM25 is rebuilt from the persisted Chroma documents when the API starts. The indexed postings support search development, but relevance judgments are still required to report Precision@K/Recall@K.

## Phases 5–8: Matching and Recommendations

- **Job matching:** `scripts/index_job_descriptions.py` batches local vacancy rows into Chroma. Dense vectors persist there; BM25 is reconstructed from those persisted documents when the API starts. RRF combines both rankings. Precision@K/Recall@K still require human-judged query/job relevance pairs.
- **Grounded recommendations:** In the Hybrid Job Search tab, first run retrieval, then request RAG recommendations for the analyzed resume. This separate Gemma call requires exact quotes from both candidate and job sources and scores closeness, relevance, accuracy, depth, ownership, verifiability, outcome, and transferability. Model rubric scores are guidance, not calibrated hiring predictions.
- **GitHub evidence:** `/github/profile` reports evidence sources separately: language statistics, repository metadata, dependency manifests, and README mentions. README or topic mentions are signals, not proof that a candidate implemented a skill; private repositories are skipped.
- **Skill gaps:** gap priority uses required-skill mention frequency and a documented category weight (technical 1.0; soft skill 0.65). The weighted coverage score is a heuristic, not a job-suitability probability.
- **Learning roadmap:** missing skills are ordered by that priority and enriched from `config/learning_resources.json` with official documentation links and practical project suggestions. Uncatalogued skills may have no resource suggestions.

Run tests:

```powershell
pytest -q
```

## Phase 3: Skill NER

`config/skill_taxonomy.json` defines canonical skill names and aliases. Phrase matches return exact evidence spans with a heuristic confidence tier. A saved spaCy NER pipeline in `models/ner/` augments phrase matching when present; an empty placeholder folder does not activate NER. The confidence tiers are not calibrated probabilities.

Create separate human-annotated JSONL files for training and validation. Each line contains a text and character-offset entity spans. `data/annotations/skill_ner.example.jsonl` is only a one-record format example, not a usable training or evaluation corpus. Do not use synthetic examples or the validation file as training data:

```json
{"text":"Used Python and Docker.","entities":[{"start":5,"end":11,"label":"SKILL"},{"start":16,"end":22,"label":"SKILL"}]}
```

Keep resume-derived annotation files local under `data/annotations/`; they are git-ignored. Train and evaluate only after both annotation files are ready:

```powershell
python scripts/train_skill_ner.py --train data/annotations/skill_train.jsonl --validation data/annotations/skill_validation.jsonl
```

The command saves a spaCy artifact and exact-span precision, recall, and F1 under `models/ner/`. Those metrics are meaningful only when validation spans were independently reviewed.

Run tests:

```powershell
pytest -q
```

## Evaluation metrics tracked

Skill extraction returns source spans and heuristic confidence tiers. The tier values are not calibrated probabilities; calibration and precision/recall/F1 measurement require a manually annotated gold set.

- Skill extraction: precision, recall, F1
- Role classification: accuracy, macro-F1
- Recommendation: Precision@K, Recall@K
- API: p50/p95 response time
- Throughput: resumes/JDs processed per run
