from __future__ import annotations

import json
import sys
from pathlib import Path


SOURCE_URL = (
    "https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset/raw/main/"
    "cvdp_v1.1.0_nonagentic_code_generation_no_commercial.jsonl"
)

SELECTED_IDS = [
    "cvdp_copilot_8x3_priority_encoder_0001",
    "cvdp_copilot_Carry_Lookahead_Adder_0001",
    "cvdp_copilot_barrel_shifter_0001",
    "cvdp_copilot_bcd_counter_0001",
    "cvdp_copilot_bcd_to_excess_3_0001",
    "cvdp_copilot_binary_to_one_hot_decoder_0001",
    "cvdp_copilot_reverse_bits_0001",
    "cvdp_copilot_edge_detector_0001",
    "cvdp_copilot_64b66b_decoder_0001",
    "cvdp_copilot_Attenuator_0001",
    "cvdp_copilot_bcd_adder_0001",
    "cvdp_copilot_binary_to_BCD_0001",
    "cvdp_copilot_binary_to_gray_0001",
    "cvdp_copilot_gray_to_binary_0001",
    "cvdp_copilot_flop_0001",
]

TASK_STYLE_BY_ID = {
    "cvdp_copilot_8x3_priority_encoder_0001": "description_to_rtl",
    "cvdp_copilot_Carry_Lookahead_Adder_0001": "description_to_rtl",
    "cvdp_copilot_barrel_shifter_0001": "description_to_rtl",
    "cvdp_copilot_bcd_counter_0001": "description_to_rtl",
    "cvdp_copilot_bcd_to_excess_3_0001": "description_to_rtl",
    "cvdp_copilot_binary_to_one_hot_decoder_0001": "description_to_rtl",
    "cvdp_copilot_reverse_bits_0001": "description_to_rtl",
    "cvdp_copilot_edge_detector_0001": "description_to_rtl",
    "cvdp_copilot_64b66b_decoder_0001": "code_completion",
    "cvdp_copilot_Attenuator_0001": "code_completion",
    "cvdp_copilot_bcd_adder_0001": "code_completion",
    "cvdp_copilot_binary_to_BCD_0001": "code_completion",
    "cvdp_copilot_binary_to_gray_0001": "code_completion",
    "cvdp_copilot_gray_to_binary_0001": "code_completion",
    "cvdp_copilot_flop_0001": "code_completion",
}


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/select_cvdp_subset.py /path/to/cvdp_v1.1.0_nonagentic_code_generation_no_commercial.jsonl")

    source_path = Path(sys.argv[1])
    rows_by_id = {}
    with source_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            rows_by_id[row["id"]] = row

    missing = [problem_id for problem_id in SELECTED_IDS if problem_id not in rows_by_id]
    if missing:
        raise SystemExit(f"missing selected CVDP ids: {missing}")

    selected_rows = [rows_by_id[problem_id] for problem_id in SELECTED_IDS]
    if any("easy" not in row["categories"] for row in selected_rows):
        raise SystemExit("selected subset must contain only easy CVDP rows")
    if any(row["input"].get("context") for row in selected_rows):
        raise SystemExit("selected subset must not require input context files")

    difficulty_counts = {
        difficulty: sum(difficulty in row["categories"] for row in selected_rows)
        for difficulty in ["easy", "medium", "hard"]
    }
    task_style_counts = {
        style: sum(TASK_STYLE_BY_ID[row["id"]] == style for row in selected_rows)
        for style in ["description_to_rtl", "code_completion"]
    }
    output_dir = Path("datasets/cvdp")
    output_dir.mkdir(parents=True, exist_ok=True)

    subset_path = output_dir / "cvdp_v1_1_0_nonagentic_no_commercial_subset.jsonl"
    with subset_path.open("w", encoding="utf-8") as fh:
        for row in selected_rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    manifest = {
        "source": "nvidia/cvdp-benchmark-dataset",
        "source_url": SOURCE_URL,
        "source_file": "cvdp_v1.1.0_nonagentic_code_generation_no_commercial.jsonl",
        "subset_file": str(subset_path),
        "selection_criteria": [
            "non-commercial CVDP code-generation problems",
            "easy-labeled problems only for shorter, lower-cost experiments",
            "mix of description-to-RTL and prompt-contained code-completion tasks",
            "single RTL output file",
            "no input context files required",
            "open-source simulation harness in the CVDP row",
            "mix of combinational, arithmetic, coding, and sequential RTL tasks",
        ],
        "difficulty_counts": difficulty_counts,
        "task_style_counts": task_style_counts,
        "task_style_by_id": TASK_STYLE_BY_ID,
        "selected_ids": SELECTED_IDS,
    }
    manifest_path = output_dir / "cvdp_subset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(subset_path)
    print(manifest_path)


if __name__ == "__main__":
    main()
