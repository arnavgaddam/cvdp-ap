from rtl_harness.config import load_config


def test_load_final_configs():
    baseline = load_config("configs/final_baseline.yaml")
    repair = load_config("configs/final_sim_repair.yaml")
    assert baseline.dataset == repair.dataset == "datasets/cvdp/cvdp_v1_1_0_nonagentic_no_commercial_subset.jsonl"
    assert baseline.dataset_format == repair.dataset_format == "cvdp"
    assert baseline.harness == "baseline"
    assert repair.harness == "sim_repair"
    assert repair.max_repair_iters == 1
    assert repair.verifier["type"] == "cvdp_docker"
