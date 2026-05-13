# Datasets

This directory stores benchmark adapters and local JSONL task files.

Each JSONL row should match the `RTLTask` schema:

```json
{
  "task_id": "and_gate",
  "prompt": "Implement a 1-bit AND gate.",
  "module_signature": "module top_module(input a, input b, output y);",
  "testbench": "optional Verilog testbench",
  "metadata": {"category": "combinational"}
}
```

Large benchmark downloads should stay out of git unless explicitly needed.
