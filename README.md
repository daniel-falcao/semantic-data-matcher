# 🔍 Semantic Data Matcher

> Match free-text descriptions against a reference domain table using **multilingual NLP and semantic similarity** — no exact string match required.

[![CI](https://github.com/YOUR_USERNAME/semantic-data-matcher/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/semantic-data-matcher/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Overview

**Semantic Data Matcher** solves a common data engineering problem: you have a column of messy, free-text descriptions (job titles, product names, categories) and need to standardise them against an official reference table — without relying on brittle keyword rules.

This project uses a **multilingual sentence-transformer model** to compute semantic similarity between each input text and every entry in your domain table. The best match above a configurable threshold is written back as new columns in your output file.

**Supports Excel (`.xlsx`) and CSV (`.csv`) for both input and domain files.**

---

## ✨ Features

| Feature | Details |
|---|---|
| 🧠 NLP-powered matching | `paraphrase-multilingual-MiniLM-L12-v2` — works in Portuguese, English, Spanish and 50+ languages |
| 📄 Multi-format support | Reads and writes `.xlsx` and `.csv` |
| 🔁 Batch CLI | Process an entire folder of files with one command |
| 🌐 REST API | FastAPI with `/match/text` and `/match/file` endpoints |
| 📊 Auto-report | Excel summary report with match rate and timing per file |
| 📝 Logging | Timestamped log file + console output |
| 🚀 Railway-ready | Dockerfile + `railway.toml` for free cloud deployment |
| ✅ CI/CD | GitHub Actions workflow included |

---

## 🗂️ Project Structure

```
semantic-data-matcher/
│
├── app/
│   ├── core/
│   │   ├── domain.py       # Loads and validates the reference domain table
│   │   ├── matcher.py      # NLP model + cosine similarity logic
│   │   └── processor.py    # Per-file processing pipeline
│   ├── utils/
│   │   ├── logger.py       # Centralized logging (console + file)
│   │   └── report.py       # Excel summary report generator
│   ├── api.py              # FastAPI app (REST endpoints)
│   └── config.py           # Settings via environment variables / .env
│
├── tests/
│   └── test_matcher.py     # Unit tests (pytest)
│
├── sample_data/
│   ├── domain_sample.csv   # Example domain reference table
│   └── input_sample.csv    # Example input file
│
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions CI pipeline
│
├── run_batch.py            # CLI entrypoint for batch processing
├── run_api.py              # API server entrypoint
├── Dockerfile              # Container definition
├── railway.toml            # Railway deployment config
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/semantic-data-matcher.git
cd semantic-data-matcher
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set DOMAIN_PATH to your domain file
```

### 3a. Batch CLI — process a folder

```bash
python run_batch.py \
  --domain  sample_data/domain_sample.csv \
  --input   sample_data/ \
  --output  data/output/ \
  --column  description \
  --threshold 0.75
```

Output files are saved with a `matched_` prefix. A summary report is written to `logs/REPORT.xlsx`.

### 3b. API server — run locally

```bash
python run_api.py
# API docs at: http://localhost:8000/docs
```

---

## 🌐 API Endpoints

### `POST /match/text`
Match a single text string.

```json
// Request
{ "text": "python developer", "threshold": 0.75 }

// Response
{
  "input_text": "python developer",
  "matched_code": "TI-001",
  "matched_description": "Senior Software Engineer",
  "similarity_score": 0.8741,
  "matched": true
}
```

### `POST /match/file`
Upload an Excel or CSV file and receive the enriched file as a download.

```bash
curl -X POST http://localhost:8000/match/file \
  -F "file=@input_sample.csv" \
  -F "source_column=description" \
  -F "threshold=0.75" \
  --output matched_input_sample.csv
```

### `GET /health`
Liveness probe — returns `{ "status": "ok", "model_loaded": true }`.

Interactive docs available at `/docs` (Swagger UI) and `/redoc`.

---

## 🏗️ Domain File Format

The domain reference file must have **4 columns with no header** (or use the CSV with a header row matching the sample):

| Column | Description |
|--------|-------------|
| A / 1 | `description` — text used for semantic matching |
| B / 2 | `code_b` — auxiliary code |
| C / 3 | `code_c` — output code written to result |
| D / 4 | `description_d` — output description written to result |

See [`sample_data/domain_sample.csv`](sample_data/domain_sample.csv) for a working example.

---

## ☁️ Deploy to Railway (Free)

Railway offers a free hobby plan suitable for this project.

### Step-by-step

1. Push your code to GitHub.
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
3. Select this repository. Railway auto-detects the `Dockerfile`.
4. Add the required environment variable:

| Variable | Value |
|----------|-------|
| `DOMAIN_PATH` | `/app/sample_data/domain_sample.csv` (or mount your own) |

5. Click **Deploy**. Railway builds the Docker image, downloads the NLP model, and starts the API.
6. Go to **Settings → Networking → Generate Domain** to get your public URL.

> **Tip:** The first build takes ~5 minutes because it downloads the sentence-transformers model (~120 MB). Subsequent deploys are faster thanks to Docker layer caching.

### Persistent domain file

To use your own domain file without committing it to the repo, use Railway's **Volume** feature:
- Create a volume and mount it to `/data`
- Upload your domain file and set `DOMAIN_PATH=/data/DOMAIN.xlsx`

---

## ⚙️ Configuration Reference

All settings can be set via environment variables or in a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DOMAIN_PATH` | *(required)* | Path to the domain reference file |
| `INPUT_FOLDER` | `data/input` | Folder scanned for input files (batch mode) |
| `OUTPUT_FOLDER` | `data/output` | Where enriched files are saved |
| `LOGS_FOLDER` | `logs` | Log and report output folder |
| `MODEL_NAME` | `paraphrase-multilingual-MiniLM-L12-v2` | HuggingFace model |
| `THRESHOLD` | `0.75` | Minimum cosine similarity (0–1) |
| `SOURCE_COLUMN` | `description` | Column name to match in input files |
| `PORT` | `8000` | API server port |

---

## 🧪 Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## 🛠️ Tech Stack

- **[sentence-transformers](https://www.sbert.net/)** — semantic embeddings
- **[FastAPI](https://fastapi.tiangolo.com/)** — async REST API
- **[pandas](https://pandas.pydata.org/)** — tabular data processing
- **[PyTorch](https://pytorch.org/)** — tensor operations for similarity scoring
- **[Railway](https://railway.app/)** — cloud deployment platform

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
