import copy
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from rsna_knee_ensemble import blend_scores, combine_stage_frames, load_config, percentile_rank
from rsna_knee_ensemble.__main__ import main, synthetic_frames
from rsna_knee_ensemble.fusion import ID_COLUMN, STAGES


@pytest.fixture
def config():
    return load_config(Path(__file__).parents[1] / "configs/v38.json")


def test_average_ties_are_percentiles_across_cases():
    np.testing.assert_allclose(percentile_rank(np.array([[3, 1], [1, 1], [1, 9]])),
                               [[1, .5], [.5, .5], [.5, 1]])


def test_identical_branches_reduce_to_their_ranks(config):
    values = np.tile(np.arange(1, 8)[:, None] / 8, (1, 12))
    result = blend_scores({name: values for name in STAGES}, config)
    np.testing.assert_allclose(result, percentile_rank(values))


def test_reference_formula_and_csv_precision(config):
    rng = np.random.default_rng(61)
    arrays = {name: rng.uniform(size=(91, 12)) for name in STAGES}
    rank = lambda x: pd.DataFrame(x).rank(method="average", pct=True).to_numpy()
    r = .65 * rank(arrays["raptor384"]) + .35 * rank(arrays["raptor224"])
    c = .65 * rank(arrays["r6"]) + .35 * rank(arrays["s6"])
    w = np.array([config["raptor_weights"][x] for x in config["target_order"]])
    lam = np.array([config["reader_weights"][x] for x in config["target_order"]])
    base = w * r + (1 - w) * c
    base = pd.read_csv(io.StringIO(pd.DataFrame(base.astype(np.float32)).to_csv(index=False))).to_numpy()
    reference = rank((1 - lam) * rank(base) + lam * rank(arrays["reader"]))
    np.testing.assert_array_equal(blend_scores(arrays, config), reference)


def test_monotone_probability_rescaling_does_not_change_fusion(config):
    rng = np.random.default_rng(62)
    stages = {name: rng.uniform(.02, .98, (55, 12)) for name in STAGES}
    transformed = {name: np.sqrt(values) for name, values in stages.items()}
    np.testing.assert_array_equal(blend_scores(stages, config), blend_scores(transformed, config))


def test_csv_rows_align_by_study_id(config):
    frames = synthetic_frames(config)
    expected = combine_stage_frames(frames, config)
    for stage in STAGES[1:]:
        frames[stage] = frames[stage].iloc[::-1].reset_index(drop=True)
    pd.testing.assert_frame_equal(combine_stage_frames(frames, config), expected)


@pytest.mark.parametrize("problem", ["duplicate", "missing", "empty", "different", "missing_column"])
def test_invalid_csv_identity_is_rejected(config, problem):
    frames = synthetic_frames(config)
    f = frames["r6"]
    if problem == "duplicate":
        f.loc[0, ID_COLUMN] = f.loc[1, ID_COLUMN]
    elif problem == "missing":
        f.loc[0, ID_COLUMN] = None
    elif problem == "empty":
        f.loc[0, ID_COLUMN] = " "
    elif problem == "different":
        f.loc[0, ID_COLUMN] = "not-the-same-case"
    else:
        frames["r6"] = f.drop(columns=[config["target_order"][0]])
    with pytest.raises(ValueError):
        combine_stage_frames(frames, config)


@pytest.mark.parametrize("value", [np.nan, np.inf, -.01, 1.01])
def test_invalid_branch_probabilities_are_rejected(config, value):
    frames = synthetic_frames(config)
    frames["reader"].loc[0, config["target_order"][0]] = value
    with pytest.raises(ValueError):
        combine_stage_frames(frames, config)


def test_missing_branch_and_single_case_are_rejected(config):
    arrays = {name: np.full((2, 12), .5) for name in STAGES}
    with pytest.raises(ValueError):
        blend_scores({k: v for k, v in arrays.items() if k != "s6"}, config)
    with pytest.raises(ValueError):
        blend_scores({k: v[:1] for k, v in arrays.items()}, config)


def test_invalid_weights_are_rejected(config):
    invalid = copy.deepcopy(config)
    invalid["reader_weights"][config["target_order"][0]] = 1.1
    with pytest.raises(ValueError):
        blend_scores({name: np.full((3, 12), .5) for name in STAGES}, invalid)


def test_demo_and_blend_cli_agree(config, tmp_path):
    config_path = Path(__file__).parents[1] / "configs/v38.json"
    assert main(["demo", "--config", str(config_path), "--output-dir", str(tmp_path)]) == 0
    output = tmp_path / "recomputed.csv"
    args = ["blend", "--config", str(config_path), "--output", str(output)]
    for name in STAGES:
        args += ["--" + name, str(tmp_path / (name + ".csv"))]
    assert main(args) == 0
    pd.testing.assert_frame_equal(pd.read_csv(output), pd.read_csv(tmp_path / "synthetic_submission.csv"))
