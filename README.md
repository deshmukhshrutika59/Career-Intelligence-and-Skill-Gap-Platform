# Career Intelligence and Skill Gap Platform

A local-first career analysis app that compares resume evidence with a target job description. It extracts skills, highlights evidence-backed gaps, adds optional public GitHub signals, finds relevant jobs, and suggests practical learning resources.

The project includes a FastAPI backend and a Streamlit dashboard. Local Ollama powers optional generative features; the core skill analysis does not require an LLM.

## Features

- **Resume parsing:** PDF, DOCX, and TXT uploads, section detection, and optional local Tesseract OCR for scanned PDFs.
- **Skill extraction:** Canonical skill names, aliases, categories, and evidence spans from a configurable taxonomy; optional spaCy NER augmentation.
- **Profile analysis:** Resume/JD comparison, ranked skill gaps, role prediction when a trained classifier is available, and a learning roadmap.
- **Evidence-grounded AI explanation:** Separately requested LLM analysis. Returned quotes are checked against the supplied resume and job description; unverified claims are not presented as sourced evidence.
- **Hybrid job search:** Persistent ChromaDB dense retrieval combined with BM25 keyword search and reciprocal-rank fusion.
- **GitHub profile signals:** Public repository metadata, languages, dependency manifests, and README mentions. These are signals, not proof of skill proficiency.
- **Career tools:** STAR-style bullet rewrites, mock interview practice, and optional grounded job recommendations.
- **Model development:** Human-reviewed role-label workflow, classifier training, spaCy NER training, evaluation scripts, and MLflow tracking.

## Quickstart

### Requirements

- Python 3.10 or newer
- [Ollama](https://ollama.com/) for AI explanations, resume rewrites, interview practice, and LLM job recommendations
- Tesseract OCR with English language data only if you need OCR for scanned PDFs

### Install

From the project directory, create and activate a virtual environment, then install the project:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
python -m spacy download en_core_web_sm
Copy-Item .env.example .env
```

The default `.env.example` configures Ollama with `gemma:2b` at `http://localhost:11434/v1`. Start Ollama and download the model before using the generative features:

```powershell
ollama pull gemma:2b
```

If Ollama is already running as a desktop service, leave it running. Otherwise start it with `ollama serve` in a separate terminal. The first run may also download the configured sentence-transformer embedding model.

### Run the app

Start the API and dashboard in separate terminals from the project directory:

```powershell
# Terminal 1: FastAPI
uvicorn career_intel.api.main:app --reload
```

```powershell
# Terminal 2: Streamlit
streamlit run frontend/app.py
```

Open the Streamlit URL printed in the terminal (normally `http://localhost:8501`). The API is normally at `http://localhost:8000`; interactive API documentation is at [`/docs`](http://localhost:8000/docs).

Run the complete resume and job analysis first. The basic `/analyze/complete` route does not call an LLM, so it remains usable without Ollama. The **Explain my profile with AI** action calls `/analyze/explanation` separately and can take noticeably longer with a local model. Other generative tools also require Ollama.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API health check |
| `POST` | `/resume/upload` | Parse a PDF, DOCX, or TXT resume |
| `POST` | `/analyze/complete` | Skill comparison, ranked gaps, and roadmap |
| `POST` | `/analyze/explanation` | Optional source-grounded LLM explanation |
| `POST` | `/search/hybrid` | Hybrid vector and keyword job retrieval |
| `POST` | `/search/recommend` | Optional LLM recommendations for retrieved jobs |
| `POST` | `/github/profile` | Analyze public GitHub profile signals |
| `POST` | `/genai/rewrite-bullets` | Generate STAR-style resume bullet rewrites |
| `POST` | `/genai/interview-prep` | Generate interview practice questions |

See [docs/api_reference.md](docs/api_reference.md) for all endpoints and response details, and [docs/architecture.md](docs/architecture.md) for the system design.

## Data and model workflows

### Job data and role labels

Small project-generated demo CSVs are included for validating data pipelines; they are not suitable for training or reporting model quality. Third-party datasets are downloaded locally and are not committed.

The [Djinni English job dataset](https://huggingface.co/datasets/lang-uk/recruitment-dataset-job-descriptions-english) and [candidate profile dataset](https://huggingface.co/datasets/lang-uk/recruitment-dataset-candidate-profiles-english) are useful for development. The associated [dataset paper](https://aclanthology.org/2024.unlp-1.2/) describes its collection and de-identification process. Import a bounded sample with:

```powershell
python scripts/import_djinni.py --limit 1000
```

Imported role suggestions are hints, not labels. Prepare the review file, manually approve suitable labels, then export approved rows before training:

```powershell
python scripts/prepare_role_review.py
# Review data/processed/djinni_en/role_label_review.csv
python scripts/finalize_role_labels.py --minimum-per-role 5
python scripts/train_pipeline.py --input data/processed/djinni_en/job_descriptions_labeled.csv
```

Index job postings for hybrid retrieval with:

```powershell
python scripts/index_job_descriptions.py --input data/processed/djinni_en/job_descriptions.csv
```

### O*NET reference data

O*NET is an occupational reference, not a vacancy-level job-posting corpus. Download the O*NET 31.0 text database from [O*NET Database](https://www.onetcenter.org/database.html) to `data/external/onet_db_31_0_text.zip`, then run:

```powershell
python scripts/import_onet.py
python scripts/build_onet_role_crosswalk.py
```

O*NET database content is licensed under [CC BY 4.0](https://www.onetcenter.org/license_db.html). Attribute the U.S. Department of Labor, Employment and Training Administration, link the license, and identify modifications when redistributing derived content. Review approximate and one-to-many crosswalk matches before using them as labels.

### Skill NER

Phrase-based taxonomy matching works without a trained project-specific NER model. To train NER, prepare separate human-annotated JSONL training and validation files; the example file under `data/annotations/` documents the format but is not a training set. Evaluate only against independently reviewed validation annotations:

```powershell
python scripts/train_skill_ner.py --train data/annotations/skill_train.jsonl --validation data/annotations/skill_validation.jsonl
```

## Configuration

Copy `.env.example` to `.env` and adjust settings as needed. Common options include:

- `LLM_PROVIDER`, `LLM_MODEL`, and `OLLAMA_BASE_URL` for local Ollama or an OpenAI-compatible provider.
- `MAX_RESUME_BYTES`, `RESUME_OCR_ENABLED`, and `TESSERACT_CMD` for resume parsing and OCR.
- `CHROMA_DB_DIR` and `EMBEDDING_MODEL_NAME` for local job indexing and retrieval.
- `GITHUB_TOKEN` for optional authenticated GitHub API access.

Do not commit `.env`, private resumes, annotations, downloaded datasets, or model artifacts. These are intended to remain local and are excluded by `.gitignore`.

Docker Compose defines the API, PostgreSQL, and MLflow services; it does not start Ollama. When using containers with Ollama running on the host, configure `OLLAMA_BASE_URL` to a host-reachable address such as `http://host.docker.internal:11434/v1`.

## Evaluation and limitations

- The skill-match score is a weighted coverage heuristic, not a hiring probability or calibrated suitability score.
- A skill gap means the skill was not detected in the submitted text; it does not establish that a person lacks the skill.
- Skill-extraction confidence tiers are heuristic, not calibrated probabilities.
- Classifier and NER quality depends on human-reviewed labels and independent held-out data. Do not report meaningful model quality until those datasets exist.
- Search quality metrics such as Precision@K and Recall@K require human-judged query/job relevance pairs.
- GitHub README mentions, topics, languages, and manifests are contextual evidence, not proof of individual ownership or proficiency.
- Local LLM inference can be slow and its output is advisory. Verify generated resume content before using it.

Resume content is sent to the configured API and LLM provider. With the default local setup, the API, Ollama, and stored vector index run on your machine; optional GitHub lookups and initial model downloads use external services. Review privacy, licensing, and data-protection requirements before using real candidate data or deploying the app.

## Development

Run tests from the project root:

```powershell
pytest -q
```

Launch the MLflow UI for local experiment tracking:

```powershell
mlflow ui --backend-store-uri ./mlruns
```

## Project structure

```text
config/                 Skill taxonomy, roles, resources, and settings
data/                   Local datasets and annotations (mostly git-ignored)
docs/                   Architecture and API reference
frontend/               Streamlit dashboard
scripts/                Import, indexing, labeling, and training commands
src/career_intel/       FastAPI app and Python package
tests/                  Unit and API tests
docker-compose.yml      API, PostgreSQL, and MLflow services
```
