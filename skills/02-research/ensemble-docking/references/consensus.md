# Consensus Scoring Methodology

## Formula

```
consensus = 0.4 × normalize(-unidock_affinity) + 0.6 × diffdock_confidence
```

## Normalization

```python
def normalize_score(score, min_val=-15, max_val=0):
    """Normalize Vina-style score to [0,1]"""
    return (score - min_val) / (max_val - min_val)
```

## Weighted Combination

| Engine   | Weight | Rationale |
|----------|--------|-----------|
| Uni-Dock | 0.4    | Speed screening |
| DiffDock | 0.6    | Accuracy priority |
| GNINA    | 0.3*   | Fallback only |

*GNINA weight replaces Uni-Dock when GPU unavailable.

## Rank Aggregation

1. Score each engine separately
2. Normalize to [0,1]
3. Apply weights
4. Sort by consensus
5. Return top N
