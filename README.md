## Quick start (data ingest POC)

The sample ChEMBL dump lives at `_1_patent_detect/m1_data/chembl_36_chemreps.txt`.

1. Install micromamba (lightweight mamba) and hook it into bash:
   ```bash
   # Linux/macOS (installs to ~/.local/bin)
   curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C ~/ --strip-components=1 bin/micromamba
   # if macOS on arm64, swap linux-64 -> osx-arm64
   export PATH="$HOME/bin:$HOME/.local/bin:$PATH"  # adjust if you extracted elsewhere
   # Initialize bash (writes hook to ~/.bashrc). Newer micromamba uses --root-prefix.
   micromamba shell init --shell bash --root-prefix ~/.micromamba
   exec "$SHELL"  # reload shell once to activate hook
   ```
2. Create an env with RDKit:
   ```bash
   micromamba create -y -n chemcore -c conda-forge python=3.10 rdkit pandas numpy tqdm
   micromamba activate chemcore
   ```
2. Run the ingest script (limit keeps it snappy):
   ```bash
   python -m _1_patent_detect.m1_poc_data_ingest.ingest_chembl \
     --limit 5000 \
     --output _1_patent_detect/m1_poc_data_ingest/outputs/chembl36_clean.pkl \
     --dedupe \
     --compute-inchikey  # optional; source file already has InChIKey
     # --error-report _1_patent_detect/m1_poc_data_ingest/outputs/chembl36_errors.csv  # optional log of failures
   ```

Output columns:
- `chembl_id`
- `canonical_smiles` (salt-stripped, RDKit canonical)
- `inchikey`
- `fp_b64` (Morgan/ECFP bit vector serialized as base64; omit with `--skip-fingerprints`)

Use `.csv`/`.parquet` suffixes on `--output` if you prefer other formats (requires `pyarrow` for parquet).
