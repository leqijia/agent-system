"""Example evaluator: recompute the score from the runner's raw output.

Keeping the scorer separate from the runner means an agent can be allowed to edit the
runner while the definition of "better" stays fixed.
"""

import json
import os
from pathlib import Path

TARGET = [1.0, -2.0, 0.5, 3.0, -1.5]


def main() -> None:
    run_dir = Path(os.environ["LAB_RUN_DIR"])
    x = json.loads((run_dir / "result.json").read_text())["x"]
    loss = sum((xi - ti) ** 2 for xi, ti in zip(x, TARGET, strict=True))
    (run_dir / "metrics.json").write_text(json.dumps({"loss": loss}))
    print(f"loss={loss:.6g}")


if __name__ == "__main__":
    main()
