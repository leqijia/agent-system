"""Example runner: gradient descent on a 5-dimensional quadratic bowl.

A runner reads its config from $LAB_CONFIG, does the work, and writes raw output into
$LAB_RUN_DIR. It does not score itself; the evaluator does that.
"""

import json
import os
import random
from pathlib import Path

TARGET = [1.0, -2.0, 0.5, 3.0, -1.5]


def main() -> None:
    run_dir = Path(os.environ["LAB_RUN_DIR"])
    settings = json.loads(Path(os.environ["LAB_CONFIG"]).read_text())
    config, seed = settings["config"], settings["seed"]

    rng = random.Random(seed)
    x = [rng.uniform(-5, 5) for _ in TARGET]
    for step in range(int(config["steps"])):
        gradient = [2 * (xi - ti) for xi, ti in zip(x, TARGET, strict=True)]
        x = [xi - config["lr"] * gi for xi, gi in zip(x, gradient, strict=True)]
        if step % 50 == 0:
            print(f"step {step}: x[0]={x[0]:.4f}")

    (run_dir / "result.json").write_text(json.dumps({"x": x}))
    print("wrote result.json")


if __name__ == "__main__":
    main()
