# Datasets

This directory stores the CVDP subset used by the final experiment.

Large benchmark downloads should stay out of git unless explicitly needed.

## CVDP Subset

`cvdp/cvdp_v1_1_0_nonagentic_no_commercial_subset.jsonl` contains 15 selected problems from NVIDIA's public CVDP v1.1.0 non-agentic, non-commercial code-generation split. All selected rows are easy-labeled tasks, split across 8 description-to-RTL tasks and 7 prompt-contained code-completion tasks. The rows preserve the original CVDP schema, including the prompt, output RTL file target, and CVDP harness files.

Selection metadata and source URL are in `cvdp/cvdp_subset_manifest.json`. Recreate the subset from the downloaded CVDP source file with:

```bash
python3 scripts/select_cvdp_subset.py /path/to/cvdp_v1.1.0_nonagentic_code_generation_no_commercial.jsonl
```

These rows are not hand-generated tasks. The final experiment configs load them with `dataset_format: "cvdp"` and score candidates with the Docker-backed CVDP verifier.
