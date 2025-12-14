## Quick start (data ingest POC)

The sample ChEMBL dump lives at `_1_patent_detect/m1_data/chembl_36_chemreps.txt`.

1. Create an env with RDKit (conda is easiest):
   ```bash
   mamba create -n chemcore -c conda-forge python=3.10 rdkit pandas numpy tqdm
   conda activate chemcore
   ```
2. Run the ingest script (limit keeps it snappy):
   ```bash
   python -m _1_patent_detect.m1_poc_data_ingest.ingest_chembl \
     --limit 5000 \
     --output _1_patent_detect/m1_poc_data_ingest/outputs/chembl36_clean.pkl \
     --dedupe
   ```

Output columns:
- `chembl_id`
- `canonical_smiles` (salt-stripped, RDKit canonical)
- `inchikey`
- `fp_b64` (Morgan/ECFP bit vector serialized as base64; omit with `--skip-fingerprints`)

Use `.csv`/`.parquet` suffixes on `--output` if you prefer other formats (requires `pyarrow` for parquet).
