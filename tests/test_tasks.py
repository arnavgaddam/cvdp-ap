import json
from pathlib import Path

from rtl_harness.tasks import load_cvdp_tasks


def test_cvdp_subset_preserves_harnesses():
    path = Path("datasets/cvdp/cvdp_v1_1_0_nonagentic_no_commercial_subset.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 15
    assert all(row["id"].startswith("cvdp_") for row in rows)
    assert all(row["input"]["prompt"] for row in rows)
    assert all("easy" in row["categories"] for row in rows)
    assert all(not row["input"].get("context") for row in rows)
    assert all(len(row["output"]["context"]) == 1 for row in rows)
    assert all("files" in row["harness"] and row["harness"]["files"] for row in rows)


def test_load_cvdp_tasks():
    tasks = load_cvdp_tasks("datasets/cvdp/cvdp_v1_1_0_nonagentic_no_commercial_subset.jsonl")
    assert len(tasks) == 15
    assert tasks[0].task_id.startswith("cvdp_")
    assert tasks[0].prompt
    assert tasks[0].output_path.startswith("rtl/")
    assert tasks[0].harness_files
    assert tasks[0].metadata["source"] == "cvdp"
