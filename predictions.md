# Prior Prediction

Date: 2026-05-14

Question: Does simulation feedback repair improve correctness over single shot RTL generation on a set of HDL problems?

Prediction: We expect simulation feedback repair to outperform the single-shot baseline over the selected problems. Before running the full study, our predicted range is that the baseline will pass roughly 25-45% of tasks, while the simulation repair run will pass roughly 40-60%. I expect the improvement to come mostly from fixing interface mistakes, syntax mistakes, and smaller logic errors.