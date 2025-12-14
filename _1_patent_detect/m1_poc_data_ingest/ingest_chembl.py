"""Quick-and-dirty ingestion script for ChEMBL chemreps -> clean canonical set."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from tqdm import tqdm

from chemcore import fingerprint, loader, prep


@dataclass
class PipelineStats:
    total_rows: int = 0
    invalid_smiles: int = 0
    removed_by_salts: int = 0
    missing_inchikey: int = 0

    def summary(self) -> Dict[str, int]:
        return {
            "total_rows": self.total_rows,
            "processed_rows": self.total_rows
            - self.invalid_smiles
            - self.removed_by_salts
            - self.missing_inchikey,
            "invalid_smiles": self.invalid_smiles,
            "removed_by_salts": self.removed_by_salts,
            "missing_inchikey": self.missing_inchikey,
        }


def _default_input() -> Path:
    here = Path(__file__).resolve()
    return here.parent.parent / "m1_data" / "chembl_36_chemreps.txt"


def _default_output() -> Path:
    here = Path(__file__).resolve()
    return here.parent / "outputs" / "chembl_36_clean.pkl"


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=_default_input(),
        help="Path to chembl_36_chemreps.txt (TSV, tab separated).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_output(),
        help="Where to save the processed dataframe (supports .pkl, .csv, .parquet).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of rows (useful for quick local tests).",
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=2,
        help="Morgan fingerprint radius.",
    )
    parser.add_argument(
        "--n-bits",
        type=int,
        default=2048,
        help="Morgan fingerprint length.",
    )
    parser.add_argument(
        "--skip-fingerprints",
        action="store_true",
        help="Only clean SMILES/InChIKey, skip fingerprint generation.",
    )
    parser.add_argument(
        "--dedupe",
        action="store_true",
        help="Drop duplicate InChIKeys after cleaning.",
    )
    return parser.parse_args(argv)


def _save_dataframe(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix in {".pkl", ".pickle"}:
        df.to_pickle(path)
    elif suffix == ".csv":
        df.to_csv(path, index=False)
    elif suffix == ".parquet":
        try:
            df.to_parquet(path, index=False)
        except ImportError as exc:
            raise RuntimeError(
                "pyarrow or fastparquet is required for parquet output. "
                "Install via `pip install pyarrow` or change --output to .pkl/.csv."
            ) from exc
    else:
        raise ValueError(f"Unsupported output format for {path}")


def process_dataframe(
    df: pd.DataFrame,
    radius: int,
    n_bits: int,
    skip_fingerprints: bool,
) -> tuple[pd.DataFrame, PipelineStats]:
    stats = PipelineStats(total_rows=len(df))
    cleaned_records: List[Dict[str, object]] = []

    for row in tqdm(df.itertuples(index=False), total=len(df), desc="Processing"):
        smiles = getattr(row, "canonical_smiles", None)
        chembl_id = getattr(row, "chembl_id", None)
        raw_inchikey = getattr(row, "standard_inchi_key", None)

        mol = prep.smiles_to_mol(smiles)
        if mol is None:
            stats.invalid_smiles += 1
            continue

        mol = prep.strip_salts(mol)
        if mol is None:
            stats.removed_by_salts += 1
            continue

        canonical_smiles = prep.canonicalize_mol(mol)
        inchikey = prep.mol_to_inchikey(mol) or raw_inchikey
        if not inchikey:
            stats.missing_inchikey += 1
            continue

        fp_b64: Optional[str] = None
        if not skip_fingerprints:
            fp = fingerprint.morgan_fingerprint(
                mol,
                radius=radius,
                n_bits=n_bits,
            )
            fp_b64 = fingerprint.fingerprint_to_base64(fp)

        cleaned_records.append(
            {
                "chembl_id": chembl_id,
                "canonical_smiles": canonical_smiles,
                "inchikey": inchikey,
                "fp_b64": fp_b64,
            }
        )

    cleaned_df = pd.DataFrame(cleaned_records)
    return cleaned_df, stats


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    print(f"Loading data from {args.input} ...")
    raw_df = loader.read_chembl_chemreps(args.input, limit=args.limit)
    print(f"Loaded {len(raw_df):,} rows")

    cleaned_df, stats = process_dataframe(
        raw_df,
        radius=args.radius,
        n_bits=args.n_bits,
        skip_fingerprints=args.skip_fingerprints,
    )

    if args.dedupe and not cleaned_df.empty:
        before = len(cleaned_df)
        cleaned_df = cleaned_df.drop_duplicates(subset=["inchikey"]).reset_index(drop=True)
        after = len(cleaned_df)
        print(f"Dedupe by InChIKey: {before:,} -> {after:,}")

    _save_dataframe(cleaned_df, args.output)
    print(f"Saved {len(cleaned_df):,} cleaned rows to {args.output}")
    print("Stats:", stats.summary())


if __name__ == "__main__":  # pragma: no cover
    main()
