from rtl_harness.config import load_config


def test_load_baseline_config():
    config = load_config("configs/baseline.yaml")
    assert config.harness == "baseline"
    assert config.dataset == "datasets/custom/sample.jsonl"
