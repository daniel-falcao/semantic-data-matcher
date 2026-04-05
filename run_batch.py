"""
Command-line interface for batch processing.

Usage:
    python run_batch.py --domain data/domain/DOMAIN.xlsx \
                        --input  data/input/ \
                        --output data/output/ \
                        --column description \
                        --threshold 0.75
"""

import argparse
import sys
from pathlib import Path

from app.core.domain import DomainLoader
from app.core.matcher import SemanticMatcher
from app.core.processor import process_file
from app.utils.logger import get_logger
from app.utils.report import save_report

logger = get_logger(__name__, log_file='logs/batch.log')

SUPPORTED_EXTENSIONS = {'.xlsx', '.csv'}


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Semantic Data Matcher — batch processor'
    )
    parser.add_argument('--domain', required=True,
                        help='Path to domain file (.xlsx or .csv)')
    parser.add_argument('--input', required=True,
                        help='Folder containing input files')
    parser.add_argument('--output', required=True,
                        help='Folder to save enriched output files')
    parser.add_argument(
        '--column', default='description',
        help='Name of the column to match (default: description)'
    )
    parser.add_argument(
        '--threshold', type=float, default=0.75,
        help='Minimum similarity score 0–1 (default: 0.75)'
    )
    parser.add_argument(
        '--model', default=SemanticMatcher.DEFAULT_MODEL,
        help='HuggingFace sentence-transformers model name'
    )
    parser.add_argument(
        '--report', default='logs/REPORT.xlsx',
        help='Path for the summary report (default: logs/REPORT.xlsx)'
    )
    return parser.parse_args()


def main():
    """Main function to run the batch processing."""
    args = parse_args()

    input_folder = Path(args.input)
    output_folder = Path(args.output)
    report_path = Path(args.report)

    if not input_folder.is_dir():
        logger.error('Input folder not found: %s', input_folder)
        sys.exit(1)

    files = [
        f for f in input_folder.iterdir()
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
        and not f.stem.startswith('matched_')
    ]

    if not files:
        logger.warning('No supported files found in %s', input_folder)
        sys.exit(0)

    logger.info('Found %d file(s) to process.', len(files))

    # Load domain and model once
    logger.info('Loading domain table…')
    domain = DomainLoader(args.domain)

    logger.info('Loading NLP model '%s'…', args.model)
    matcher = SemanticMatcher(domain.descriptions, model_name=args.model)

    # Process each file
    all_stats = []
    for file in files:
        try:
            out_path = output_folder / f'matched_{file.name}'
            stats = process_file(
                input_path=file,
                output_path=out_path,
                source_column=args.column,
                matcher=matcher,
                domain=domain,
                threshold=args.threshold,
            )
            all_stats.append(stats)
        except Exception as exc:
            logger.error('Failed to process %s: %s', file.name, exc)

    save_report(all_stats, report_path)
    logger.info('Batch processing complete.')


if __name__ == '__main__':
    main()
