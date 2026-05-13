from rtl_harness.tasks import load_jsonl_tasks


def test_load_sample_tasks():
    tasks = load_jsonl_tasks("datasets/custom/sample.jsonl")
    assert len(tasks) == 1
    assert tasks[0].task_id == "and_gate"
