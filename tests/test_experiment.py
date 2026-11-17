import pytest

from labkit import experiment, registry
from labkit.config import BudgetError, LabError


def load(project, *sets, seed=None):
    spec = experiment.load_spec(project.root / "toy.toml")
    experiment.apply_overrides(spec, list(sets), seed)
    return spec


def test_run_records_metrics_and_artifacts(project):
    record = experiment.run_spec(project, load(project))

    assert record["status"] == "ok"
    assert record["metrics"] == {"loss": 9}
    run_dir = project.root / record["run_dir"]
    assert (run_dir / "log.txt").is_file()
    assert (run_dir / "identity.json").is_file()
    assert registry.read(project.path("registry")) == [record]


def test_identical_run_is_served_from_cache(project, calls):
    first = experiment.run_spec(project, load(project))
    second = experiment.run_spec(project, load(project))

    assert second["cached"] is True
    assert second["run_id"] == first["run_id"]
    assert calls() == 1
    assert len(registry.read(project.path("registry"))) == 1


def test_config_seed_and_code_each_change_the_identity(project):
    base = experiment.run_spec(project, load(project))["run_id"]
    other_config = experiment.run_spec(project, load(project, "x=4"))["run_id"]
    other_seed = experiment.run_spec(project, load(project, seed=1))["run_id"]
    runner = project.root / "runner.py"
    runner.write_text(runner.read_text() + "\n# edited\n")
    other_code = experiment.run_spec(project, load(project))["run_id"]

    assert len({base, other_config, other_seed, other_code}) == 4


def test_out_of_bounds_config_is_rejected_before_running(project, calls):
    with pytest.raises(LabError, match="outside allowed range"):
        experiment.run_spec(project, load(project, "x=99"))
    assert calls() == 0


def test_unknown_override_key_is_rejected(project):
    with pytest.raises(LabError, match="not in \\[config\\]"):
        load(project, "learning_rate=1")


def test_failed_run_is_recorded_with_log_and_not_cached(project, calls):
    spec = load(project, "fail=true")
    record = experiment.run_spec(project, spec)

    assert record["status"] == "failed"
    assert "boom" in experiment.summarize(project, spec, record)
    experiment.run_spec(project, load(project, "fail=true"))
    assert calls() == 2


def test_timeout_kills_the_run(project):
    spec = load(project, "sleep=30")
    spec.timeout_s = 0.5
    record = experiment.run_spec(project, spec)

    assert record["status"] == "timeout"
    assert record["seconds"] < 10


def test_exit_zero_without_metrics_is_not_a_success(project):
    record = experiment.run_spec(project, load(project, "silent=true"))

    assert record["status"] == "no_metrics"
    assert "metrics.json" in record["note"]


def test_spec_run_cap_stops_the_search(project):
    for x in range(5):
        experiment.run_spec(project, load(project, f"x={x}"))
    with pytest.raises(BudgetError, match="max_runs=5"):
        experiment.run_spec(project, load(project, "x=7"))


def test_daily_run_cap(project):
    project.data["budgets"]["runs_per_day"] = 1
    experiment.run_spec(project, load(project))
    with pytest.raises(BudgetError, match="daily run cap"):
        experiment.run_spec(project, load(project, "x=4"))


def test_screening_skips_the_full_run_when_out_of_bounds(project, calls):
    spec = load(project, "x=9")
    spec.screen = {"overrides": {}, "bounds": {"loss": [0, 50]}}
    record = experiment.run_spec(project, spec)

    assert record["status"] == "screened_out"
    assert "loss=81" in record["note"]
    assert calls() == 1  # only the screening run started


def test_screening_pass_then_full_run(project, calls):
    spec = load(project, "x=2")
    spec.screen = {"overrides": {"x": 1}, "bounds": {"loss": [0, 50]}}
    record = experiment.run_spec(project, spec)

    assert record["status"] == "ok"
    assert record["stage"] == "full"
    assert record["metrics"] == {"loss": 4}
    assert calls() == 2


def test_best_run_respects_direction(project):
    for x in (3, 1, 2):
        experiment.run_spec(project, load(project, f"x={x}"))
    records = registry.read(project.path("registry"))

    assert experiment.best_run(records, "toy", "loss", "min")["metrics"]["loss"] == 1
    assert experiment.best_run(records, "toy", "loss", "max")["metrics"]["loss"] == 9
