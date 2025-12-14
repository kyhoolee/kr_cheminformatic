"""I/O helpers for reading public chemistry datasets."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence

import pandas as pd

DEFAULT_CHEMBL_COLUMNS: List[str] = [
    "chembl_id",
    "canonical_smiles",
    "standard_inchi",
    "standard_inchi_key",
]


def read_chembl_chemreps(
    path: str | Path,
    limit: Optional[int] = None,
    columns: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Load the ChEMBL `chemreps` TSV into a DataFrame."""
    resolved_path = Path(path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Could not find input file: {resolved_path}")

    usecols = list(columns) if columns is not None else DEFAULT_CHEMBL_COLUMNS
    return pd.read_csv(
        resolved_path,
        sep="\t",
        nrows=limit,
        usecols=usecols,
        dtype=str,
        engine="c",
    )


def iter_chembl_chemreps(
    path: str | Path, limit: Optional[int] = None
) -> Iterator[Dict[str, str]]:
    """Stream records from the ChEMBL `chemreps` TSV without loading all into RAM."""
    resolved_path = Path(path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Could not find input file: {resolved_path}")

    with resolved_path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for idx, row in enumerate(reader):
            if limit is not None and idx >= limit:
                break
            yield row
