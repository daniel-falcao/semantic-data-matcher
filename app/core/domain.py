"""
Loads and validates the domain reference table from an Excel or CSV file.
"""

import pandas as pd
from pathlib import Path


REQUIRED_COLUMNS = ["description", "code_b", "code_c", "description_d"]


class DomainLoader:
    """Loads the reference domain table used for semantic matching."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.df: pd.DataFrame = self._load()

    def _load(self) -> pd.DataFrame:
        suffix = self.path.suffix.lower()
        if suffix == ".xlsx":
            df = pd.read_excel(self.path, header=None, usecols="A:D")
        elif suffix == ".csv":
            df = pd.read_csv(self.path, header=None, usecols=[0, 1, 2, 3])
        else:
            raise ValueError(f"Unsupported domain file format: {suffix}. Use .xlsx or .csv")

        df.columns = REQUIRED_COLUMNS
        df = df.dropna(subset=["description"])
        df = df.reset_index(drop=True)

        if df.empty:
            raise ValueError("Domain file has no valid rows after dropping empty descriptions.")

        return df

    @property
    def descriptions(self) -> list[str]:
        return self.df["description"].tolist()

    def get_row(self, index: int) -> dict:
        return self.df.iloc[index].to_dict()
