"""Compute top-K Tanimoto neighbors for a cleaned ChEMBL subset."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Sequence

import numpy as np
import pandas as pd
from tqdm import tqdm

from chemcore import fingerprint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).parent / "outputs" / "chembl36_clean.pkl",
        help="Path to cleaned dataframe (pickle/csv/parquet).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "outputs" / "chembl36_topk.csv",
        help="Where to write the neighbor table (CSV).",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of nearest neighbors per molecule (self excluded).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N rows (useful for quick tests).",
    )
    return parser.parse_args()


def load_df(path: Path, limit: int | None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".pkl", ".pickle"}:
        df = pd.read_pickle(path)
    elif suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported input format: {path}")
    if limit is not None:
        df = df.iloc[:limit].reset_index(drop=True)
    return df


def decode_fps(fp_b64_series: Sequence[str]) -> List:
    fps = []
    for fp in fp_b64_series:
        if pd.isna(fp):
            fps.append(None)
        else:
            fps.append(fingerprint.base64_to_fingerprint(fp))
    return fps


def topk_neighbors(fps: List, k: int) -> List[List[tuple[int, float]]]:
    from rdkit import DataStructs  # type: ignore

    n = len(fps)
    neighbors: List[List[tuple[int, float]]] = []
    for i in tqdm(range(n), desc="Top-K search"):
        fp_i = fps[i]
        if fp_i is None:
            neighbors.append([])
            continue
        sims = DataStructs.BulkTanimotoSimilarity(fp_i, fps)
        sims[i] = -1.0  # remove self
        arr = np.asarray(sims)
        top_idx = np.argpartition(-arr, kth=k)[:k]
        sorted_idx = top_idx[np.argsort(-arr[top_idx])]
        neighbors.append([(int(j), float(arr[j])) for j in sorted_idx if arr[j] >= 0])
    return neighbors


def build_neighbor_df(df: pd.DataFrame, neighbors: List[List[tuple[int, float]]]) -> pd.DataFrame:
    records = []
    ids = df["chembl_id"].tolist()
    for i, neighs in enumerate(neighbors):
        for j, sim in neighs:
            records.append(
                {
                    "query_idx": i,
                    "query_chembl_id": ids[i],
                    "neighbor_idx": j,
                    "neighbor_chembl_id": ids[j],
                    "tanimoto": sim,
                }
            )
    return pd.DataFrame(records)


def main() -> None:
    args = parse_args()
    df = load_df(args.input, args.limit)
    print(f"Loaded {len(df):,} rows from {args.input}")

    fps = decode_fps(df["fp_b64"])
    neighbors = topk_neighbors(fps, args.k)
    out_df = build_neighbor_df(df, neighbors)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(args.output, index=False)
    print(f"Saved {len(out_df):,} neighbor pairs to {args.output}")
    print("Sample:")
    print(out_df.head())


if __name__ == "__main__":  # pragma: no cover
    main()
