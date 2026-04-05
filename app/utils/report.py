"""
Generates a summary Excel report from per-file processing statistics.
"""

import pandas as pd
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)


def save_report(stats_list: list[dict], output_path: Path) -> None:
    """
    Saves a summary Excel report with one row per processed file.

    Args:
        stats_list: List of stats dicts returned by process_file().
        output_path: Path where the .xlsx report will be saved.
    """
    if not stats_list:
        logger.warning('No stats to save — report skipped.')
        return

    df = pd.DataFrame(stats_list)
    df.columns = [
        'File',
        'Total Rows',
        'Matched',
        'Not Found',
        'Success Rate (%)',
        'Elapsed (s)',
        'Elapsed (min)',
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    logger.info(f'Report saved → {output_path}')
