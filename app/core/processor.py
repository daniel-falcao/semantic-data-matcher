"""
Processes input files (Excel or CSV), runs semantic matching per row,
and writes results back to output files with enriched columns.
"""

import time
import pandas as pd
from pathlib import Path
from tqdm import tqdm

from app.core.matcher import SemanticMatcher
from app.core.domain import DomainLoader
from app.utils.logger import get_logger

NOT_FOUND_MARKER = '#NOTFOUND'

logger = get_logger(__name__)


def _read_file(path: Path) -> pd.DataFrame:
    """Reads an Excel or CSV file into a DataFrame."""
    suffix = path.suffix.lower()
    if suffix == '.xlsx':
        return pd.read_excel(path)
    elif suffix == '.csv':
        return pd.read_csv(path)
    raise ValueError(f'Unsupported input format: {suffix}')


def _save_file(df: pd.DataFrame, path: Path) -> None:
    """Saves a DataFrame to Excel or CSV based on output path extension."""
    suffix = path.suffix.lower()
    if suffix == '.xlsx':
        df.to_excel(path, index=False)
    elif suffix == '.csv':
        df.to_csv(path, index=False)
    else:
        raise ValueError(f'Unsupported output format: {suffix}')


def process_file(
    input_path: Path,
    output_path: Path,
    source_column: str,
    matcher: SemanticMatcher,
    domain: DomainLoader,
    threshold: float = 0.75,
) -> dict:
    """
    Reads a file, applies semantic matching on `source_column`,
    appends result columns, and saves to `output_path`.

    Returns a stats dictionary for reporting.
    """
    start = time.time()

    df = _read_file(input_path)
    total_rows = len(df)

    if source_column not in df.columns:
        raise ValueError(
            f'Column {source_column} not found in {input_path.name}. '
            f'Available columns: {list(df.columns)}'
        )

    matched_codes = []
    matched_descriptions = []
    similarity_scores = []
    matched = 0
    not_found = 0

    for value in tqdm(df[source_column].astype(str), desc=input_path.name, unit='row'):
        idx, score = matcher.find_best_match(value, threshold=threshold)
        if idx is not None:
            row = domain.get_row(idx)
            matched_codes.append(row['code_c'])
            matched_descriptions.append(row['description_d'])
            similarity_scores.append(round(score, 4))
            matched += 1
        else:
            matched_codes.append(NOT_FOUND_MARKER)
            matched_descriptions.append(NOT_FOUND_MARKER)
            similarity_scores.append(round(score, 4))
            not_found += 1

    df['matched_code'] = matched_codes
    df['matched_description'] = matched_descriptions
    df['similarity_score'] = similarity_scores

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _save_file(df, output_path)

    elapsed = time.time() - start
    success_rate = round((matched / total_rows) * 100, 2) if total_rows else 0.0

    stats = {
        'file': input_path.name,
        'total_rows': total_rows,
        'matched': matched,
        'not_found': not_found,
        'success_rate_pct': success_rate,
        'elapsed_seconds': round(elapsed, 2),
        'elapsed_minutes': round(elapsed / 60, 2),
    }

    logger.info(
        f'{input_path.name} → {matched}/{total_rows} matched '
        f'({success_rate}%) in {stats['elapsed_minutes']} min'
    )
    return stats
