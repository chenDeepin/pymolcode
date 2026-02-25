# External MCP Servers

> DrugCLIP and RDKit integration via MCP (Planned)

## Status

These are **planned integrations**. Current implementations are stubs for development.

## DrugCLIP Server (Planned)

Molecular retrieval and similarity search using DrugCLIP embeddings.

### Planned API

```python
encode_molecules(molecules: List[str], encoding: str = "smiles") -> List[str]
retrieve_molecules(query: str, k: int = 10) -> List[str]
```

## RDKit Server (Planned)

Cheminformatics toolkit for molecule manipulation and analysis.

### Planned API

```python
encode_molecules(molecules: List[str], encoding: str = "fingerprint") -> List[str]
calculate_similarity(mol_a: str, mol_b: str, metric: str = "tanimoto") -> float
descriptors(molecule: str) -> Dict[str, float]
```

## Planned Configuration

```yaml
# ~/.config/pymolcode/config.yaml (not yet supported)
mcp:
  servers:
    - name: drugclip
      command: python -m drugclip_mcp_server
      enabled: true
    - name: rdkit
      command: python -m rdkit_mcp_server
      enabled: true
```

## Current Workaround

For now, use RDKit directly in Python:

```python
from rdkit import Chem
from rdkit.Chem import Descriptors

mol = Chem.MolFromSmiles('CCO')
mw = Descriptors.MolWt(mol)
```

## See Also

- [MCP Integration](./mcp.md) - MCP architecture overview
- [API Reference](./api.md) - Available tools and methods
