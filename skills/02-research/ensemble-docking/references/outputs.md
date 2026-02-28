# Output Specifications

## Directory Structure

```
results/
├── job_manifest.json        # Job metadata
├── stage1_unidock/          # Fast scan results
│   ├── scores.csv
│   └── poses/
├── stage2_diffdock/         # Deep dock results
│   ├── confidence.csv
│   └── poses/
├── consensus/               # Final ranking
│   ├── ranked_hits.json
│   └── summary.csv
└── poses/                   # Best poses
    └── *.pdb
```

## File Formats

### ranked_hits.json
```json
{
  "hits": [
    {"rank": 1, "id": "cpd_0042", "score": 0.92, "pose": "poses/cpd_0042.pdb"}
  ]
}
```

### summary.csv
```csv
rank,ligand_id,unidock,diffdock,consensus,pose_path
1,compound_0042,-9.2,0.89,0.92,poses/compound_0042.pdb
```
