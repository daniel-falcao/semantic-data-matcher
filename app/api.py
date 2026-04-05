"""
FastAPI application exposing the semantic matcher as a REST API.

Endpoints:
  POST /match/text    — match a single text string
  POST /match/file    — upload a file and match all rows
  GET  /health        — liveness probe
"""

import io
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Annotated
import pandas as pd

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.domain import DomainLoader
from app.core.matcher import SemanticMatcher
from app.core.processor import NOT_FOUND_MARKER
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Shared state ────────────────────────────────────────────────────────
_domain: DomainLoader | None = None
_matcher: SemanticMatcher | None = None


def _bootstrap():
    global _domain, _matcher
    domain_path = os.getenv('DOMAIN_PATH')
    if not domain_path:
        raise RuntimeError('DOMAIN_PATH environment variable is required.')
    model_name = os.getenv('MODEL_NAME', SemanticMatcher.DEFAULT_MODEL)
    # logger.info(f'Loading domain from {domain_path}…')
    logger.info('Loading domain from %s…', domain_path)
    _domain = DomainLoader(domain_path)
    logger.info('Loading NLP model %s…', model_name)
    _matcher = SemanticMatcher(_domain.descriptions, model_name=model_name)
    logger.info('Semantic matcher ready.')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """async context manager to handle startup and shutdown events
    of the FastAPI app. On startup, it bootstraps the domain and matcher.
    On shutdown, it can be used to clean up resources if needed."""
    _bootstrap()
    yield


# ── App ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title='Semantic Data Matcher API',
    description=(
        'Match free-text descriptions against a reference domain table '
        'using multilingual semantic similarity (NLP).'
    ),
    version='1.0.0',
    lifespan=lifespan,
)


# ── Schemas ─────────────────────────────────────────────────────────────
class TextMatchRequest(BaseModel):
    """Defines the structure of the request for a text match."""
    text: str
    threshold: float = 0.75


class TextMatchResponse(BaseModel):
    """Defines the structure of the response for a text match request."""
    input_text: str
    matched_code: str | None
    matched_description: str | None
    similarity_score: float
    matched: bool


# ── Endpoints ───────────────────────────────────────────────────────────
@app.get('/health', tags=['Monitoring'])
def health():
    """Status to check if the service is up and the matcher is ready."""
    return {'status': 'ok', 'model_loaded': _matcher is not None}


@app.post('/match/text', response_model=TextMatchResponse, tags=['Matching'])
def match_text(payload: TextMatchRequest):
    """Match a single text string against the domain table."""
    if _matcher is None or _domain is None:
        raise HTTPException(status_code=503, detail='Matcher not initialised.')

    idx, score = _matcher.find_best_match(payload.text,
                                          threshold=payload.threshold)
    if idx is not None:
        row = _domain.get_row(idx)
        return TextMatchResponse(
            input_text=payload.text,
            matched_code=str(row['code_c']),
            matched_description=str(row['description_d']),
            similarity_score=round(score, 4),
            matched=True,)
    return TextMatchResponse(
        input_text=payload.text,
        matched_code=None,
        matched_description=None,
        similarity_score=round(score, 4),
        matched=False,)


@app.post('/match/file', tags=['Matching'])
async def match_file(
    file: Annotated[UploadFile,
                    File(description='Excel (.xlsx) or CSV (.csv) file')],
    source_column: Annotated[str, Form(
        description='Column name containing the text to match')],
    threshold: Annotated[float, Form(
        description='Minimum similarity score (0–1)')] = 0.75,):
    """
    Upload an Excel or CSV file. Each row in `source_column` is matched
    against the domain. Returns the enriched file for download.
    """
    if _matcher is None or _domain is None:
        raise HTTPException(status_code=503, detail='Matcher not initialised.')

    filename = file.filename or 'upload'
    suffix = Path(filename).suffix.lower()
    if suffix not in {'.xlsx', '.csv'}:
        raise HTTPException(status_code=400,
                            detail='Only .xlsx and .csv files are supported.')

    contents = await file.read()
    try:
        if suffix == '.xlsx':
            df = pd.read_excel(io.BytesIO(contents))
        else:
            df = pd.read_csv(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400,
                            detail=f'Could not parse file: {exc}') from exc

    if source_column not in df.columns:
        raise HTTPException(
            status_code=422,
            detail=f'Column '{source_column}' not found. Available: {list(df.columns)}',)

    codes, descriptions, scores = [], [], []
    for value in df[source_column].astype(str):
        idx, score = _matcher.find_best_match(value, threshold=threshold)
        if idx is not None:
            row = _domain.get_row(idx)
            codes.append(str(row['code_c']))
            descriptions.append(str(row['description_d']))
        else:
            codes.append(NOT_FOUND_MARKER)
            descriptions.append(NOT_FOUND_MARKER)
        scores.append(round(score, 4))

    df['matched_code'] = codes
    df['matched_description'] = descriptions
    df['similarity_score'] = scores

    # Return the enriched file in the same format it was uploaded
    buf = io.BytesIO()
    if suffix == '.xlsx':
        df.to_excel(buf, index=False)
        media_type = 'application/\
vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    else:
        df.to_csv(buf, index=False)
        media_type = 'text/csv'
    buf.seek(0)

    out_name = f'matched_{filename}'
    return StreamingResponse(
        buf,
        media_type=media_type,
        headers={'Content-Disposition': f'attachment; filename='{out_name}''},)
