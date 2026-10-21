"""Deterministic synthetic data generation for orderops-agent.

Everything the agent sees is produced here. Two rules make the dataset
trustworthy:

1. **Deterministic.** The same seed must produce byte-identical output, so
   that an evaluation result can always be reproduced and a diff always means
   a real change.
2. **Labelled.** Every order carries a ground truth root cause. That label is
   the only thing the evaluator compares against - the agent's tools must never
   be able to reach it.

Implementation lives in `orderops_synthetic.generator`; see the module
docstring there for the contract, and `tests/test_generator.py` for the
acceptance suite.
"""

from orderops_synthetic.generator import DatasetConfig, OrderDataset, generate_dataset

__all__ = ["DatasetConfig", "OrderDataset", "generate_dataset"]
