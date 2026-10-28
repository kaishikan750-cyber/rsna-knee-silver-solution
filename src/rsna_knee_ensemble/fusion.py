"""Per-finding percentile-rank fusion; no model weights or patient data included."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

STAGES = ("raptor384", "raptor224", "r6", "s6", "reader")
ID_COLUMN = "StudyInstanceUID"


def load_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_config(config)
    return config


def validate_config(config: Mapping) -> None:
    labels = config["target_order"]
    if not isinstance(labels, list) or len(labels) != 12 or len(set(labels)) != 12:
        raise ValueError("target_order must contain 12 distinct finding names")
    for field in ("raptor_weights", "reader_weights"):
        if set(config[field]) != set(labels):
            raise ValueError(f"{field} must specify exactly the configured findings")
        values = np.array([config[field][label] for label in labels], dtype=float)
        if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
            raise ValueError(f"{field} must be finite and within [0, 1]")
    for field in ("raptor384_share", "s6_share"):
        value = config[field]
        if isinstance(value, bool) or not np.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"{field} must be within [0, 1]")
    if not isinstance(config.get("base_float32_csv_roundtrip"), bool):
        raise ValueError("base_float32_csv_roundtrip must be explicit true or false")


def percentile_rank(scores: np.ndarray) -> np.ndarray:
    """Rank each finding across cases, using average ties and percentiles 1/N..1."""
    values = np.asarray(scores, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] < 2 or values.shape[1] == 0:
        raise ValueError("scores must be a 2D array containing at least two cases")
    if not np.isfinite(values).all():
        raise ValueError("scores must be finite")
    return pd.DataFrame(values).rank(method="average", pct=True).to_numpy()


def blend_scores(stages: Mapping[str, np.ndarray], config: Mapping) -> np.ndarray:
    """Return the V38 final rank scores for five already-TTA-aggregated branches.

    The float32 -> CSV -> float64 step intentionally follows the saved notebook:
    it can affect near-ties and must precede ranking the group-weighted base.
    """
    validate_config(config)
    if set(stages) != set(STAGES):
        raise ValueError(f"exactly five branches are required: {STAGES}")
    arrays = {name: np.asarray(stages[name], dtype=np.float64) for name in STAGES}
    shape = arrays[STAGES[0]].shape
    if len(shape) != 2 or shape[0] < 2 or shape[1] != len(config["target_order"]):
        raise ValueError("branch arrays must have shape (N >= 2, 12)")
    for name, values in arrays.items():
        if values.shape != shape:
            raise ValueError(f"shape mismatch in {name}")
        if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
            raise ValueError(f"invalid probabilities in {name}; expected finite [0, 1]")

    ranked = {name: percentile_rank(values) for name, values in arrays.items()}
    a, b = config["raptor384_share"], config["s6_share"]
    raptor = a * ranked["raptor384"] + (1.0 - a) * ranked["raptor224"]
    compact = (1.0 - b) * ranked["r6"] + b * ranked["s6"]
    labels = config["target_order"]
    weights = np.array([config["raptor_weights"][label] for label in labels])
    reader_share = np.array([config["reader_weights"][label] for label in labels])
    base = weights * raptor + (1.0 - weights) * compact
    if config["base_float32_csv_roundtrip"]:
        buffer = io.StringIO(pd.DataFrame(base.astype(np.float32)).to_csv(index=False))
        base = pd.read_csv(buffer).to_numpy()
    return percentile_rank(
        (1.0 - reader_share) * percentile_rank(base) + reader_share * ranked["reader"]
    )


def combine_stage_frames(stages: Mapping[str, pd.DataFrame], config: Mapping) -> pd.DataFrame:
    """Align unique study IDs to the first branch, then apply column-wise fusion."""
    validate_config(config)
    if set(stages) != set(STAGES):
        raise ValueError(f"exactly five branches are required: {STAGES}")
    labels = config["target_order"]
    indexed = {}
    for name in STAGES:
        frame = stages[name]
        if frame.columns.duplicated().any() or set(frame.columns) != {ID_COLUMN, *labels}:
            raise ValueError(f"{name} must contain the ID column and exactly 12 findings")
        if frame[ID_COLUMN].isna().any():
            raise ValueError(f"missing study ID in {name}")
        ids = frame[ID_COLUMN].astype(str)
        if ids.str.strip().eq("").any() or ids.duplicated().any():
            raise ValueError(f"empty or duplicate study ID in {name}")
        indexed[name] = frame.assign(**{ID_COLUMN: ids}).set_index(ID_COLUMN)
    reference = indexed[STAGES[0]].index
    for name in STAGES[1:]:
        if set(indexed[name].index) != set(reference):
            raise ValueError(f"different study IDs in {name}")
    arrays = {name: frame.loc[reference, labels].to_numpy(dtype=np.float64)
              for name, frame in indexed.items()}
    result = pd.DataFrame(blend_scores(arrays, config), columns=labels)
    result.insert(0, ID_COLUMN, reference.to_numpy())
    return result
