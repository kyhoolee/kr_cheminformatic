"""Fingerprint helpers (Morgan/ECFP) and similarity utilities."""

from __future__ import annotations

import base64
from typing import Optional

import numpy as np


def _require_rdkit():
    try:
        from rdkit import Chem  # type: ignore
        from rdkit import DataStructs  # type: ignore
        from rdkit.Chem import AllChem  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise ImportError(
            "rdkit is required for chemcore.fingerprint. Install via conda: "
            "`conda install -c conda-forge rdkit`."
        ) from exc
    return Chem, AllChem, DataStructs


def morgan_fingerprint(
    mol,
    radius: int = 2,
    n_bits: int = 2048,
    use_chirality: bool = True,
    use_features: bool = False,
):
    """Compute a Morgan/ECFP bit vector from an RDKit Mol."""
    _, AllChem, _ = _require_rdkit()
    return AllChem.GetMorganFingerprintAsBitVect(
        mol,
        radius,
        nBits=n_bits,
        useChirality=use_chirality,
        useFeatures=use_features,
    )


def fingerprint_to_numpy(fp) -> np.ndarray:
    """Convert RDKit ExplicitBitVect to a numpy uint8 array."""
    _, _, DataStructs = _require_rdkit()
    arr = np.zeros((fp.GetNumBits(),), dtype=np.uint8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr


def fingerprint_to_base64(fp) -> str:
    """Serialize a fingerprint to a compact base64 string (useful for storage)."""
    _, _, DataStructs = _require_rdkit()
    binary = DataStructs.BitVectToBinaryText(fp)
    return base64.b64encode(binary).decode("ascii")


def base64_to_fingerprint(encoded: str):
    """Deserialize a base64-encoded fingerprint back to ExplicitBitVect."""
    _, _, DataStructs = _require_rdkit()
    binary = base64.b64decode(encoded.encode("ascii"))
    return DataStructs.CreateFromBinaryText(binary)


def tanimoto_similarity(fp_a, fp_b) -> float:
    """Tanimoto similarity between two fingerprints."""
    _, _, DataStructs = _require_rdkit()
    return float(DataStructs.TanimotoSimilarity(fp_a, fp_b))
