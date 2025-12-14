"""Molecule preparation helpers (SMILES -> Mol, salt stripping, canonicalization)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

_SALT_REMOVER = None


@dataclass
class StandardizedMol:
    mol: Any
    canonical_smiles: str
    inchikey: Optional[str]


def _require_rdkit():
    try:
        from rdkit import Chem  # type: ignore
        from rdkit.Chem import SaltRemover  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise ImportError(
            "rdkit is required for chemcore.prep. Install via conda: "
            "`conda install -c conda-forge rdkit`."
        ) from exc
    return Chem, SaltRemover


def smiles_to_mol(smiles: str, sanitize: bool = True):
    """Convert a SMILES string to an RDKit Mol."""
    Chem, _ = _require_rdkit()
    if not smiles:
        return None
    return Chem.MolFromSmiles(smiles, sanitize=sanitize)


def strip_salts(mol):
    """Remove common salts/solvents from the molecule."""
    global _SALT_REMOVER
    Chem, SaltRemover = _require_rdkit()
    if _SALT_REMOVER is None:
        _SALT_REMOVER = SaltRemover.SaltRemover()
    cleaned = _SALT_REMOVER.StripMol(mol, dontRemoveEverything=True)
    return cleaned if cleaned is not None and cleaned.GetNumAtoms() > 0 else None


def canonicalize_mol(mol, *, raise_on_error: bool = False) -> Optional[str]:
    """Return canonical (isomeric) SMILES; None if RDKit cannot kekulize/serialize."""
    Chem, _ = _require_rdkit()
    try:
        return Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
    except Exception as exc:
        if raise_on_error:
            raise
        return None


def mol_to_inchikey(mol) -> Optional[str]:
    """Return InChIKey derived from the molecule (None if InChI support is missing)."""
    Chem, _ = _require_rdkit()
    try:
        return Chem.inchi.MolToInchiKey(mol)
    except Exception:
        return None


def standardize_smiles(
    smiles: str, remove_salts: bool = True, sanitize: bool = True
) -> Optional[StandardizedMol]:
    """Best-effort pipeline: SMILES -> Mol -> salt stripping -> canonical SMILES + InChIKey."""
    mol = smiles_to_mol(smiles, sanitize=sanitize)
    if mol is None:
        return None

    if remove_salts:
        mol = strip_salts(mol)
        if mol is None:
            return None

    canonical = canonicalize_mol(mol)
    inchikey = mol_to_inchikey(mol)
    return StandardizedMol(mol=mol, canonical_smiles=canonical, inchikey=inchikey)
