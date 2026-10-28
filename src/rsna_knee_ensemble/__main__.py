"""Command-line fusion and a reproducible, synthetic-data demonstration."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .fusion import ID_COLUMN, STAGES, combine_stage_frames, load_config


def synthetic_frames(config, rows=48, seed=42):
    rng = np.random.default_rng(seed)
    labels = config["target_order"]
    frames = {}
    for name in STAGES:
        frame = pd.DataFrame(rng.uniform(0.01, 0.99, (rows, len(labels))), columns=labels)
        frame.insert(0, ID_COLUMN, [f"synthetic-{i:04d}" for i in range(rows)])
        frames[name] = frame
    return frames


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    blend = commands.add_parser("blend", help="Fuse five authorized, local branch CSVs")
    blend.add_argument("--config", type=Path, default=Path("configs/v38.json"))
    for stage in STAGES:
        blend.add_argument("--" + stage, type=Path, required=True)
    blend.add_argument("--output", type=Path, required=True)
    demo = commands.add_parser("demo", help="Run with generated synthetic cases only")
    demo.add_argument("--config", type=Path, default=Path("configs/v38.json"))
    demo.add_argument("--output-dir", type=Path, default=Path("artifacts/demo"))
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if args.command == "demo":
            frames = synthetic_frames(config)
            args.output_dir.mkdir(parents=True, exist_ok=True)
            for stage, frame in frames.items():
                frame.to_csv(args.output_dir / (stage + ".csv"), index=False)
            output = args.output_dir / "synthetic_submission.csv"
        else:
            frames = {stage: pd.read_csv(getattr(args, stage), dtype={ID_COLUMN: str})
                      for stage in STAGES}
            output = args.output
        result = combine_stage_frames(frames, config)
        output.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(output, index=False)
    except (ValueError, KeyError, OSError, TypeError) as error:
        parser.error(str(error))
    kind = "synthetic demonstration" if args.command == "demo" else "local branch fusion"
    print(f"Completed {kind}: {len(result)} cases, 12 findings; wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
