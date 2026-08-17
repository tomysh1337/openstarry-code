---
name: science-data-router
description: Select the most specific installed skill for scientific computing, statistics, data science, machine learning, experiments, visualization, bioinformatics, chemistry, and research methods. Use for science, statistics, pandas, NumPy, SciPy, scikit-learn, experiments, 科研, 科学计算, 统计分析, 数据科学, 机器学习, 生物信息, 实验设计, or 数据可视化 requests.
---

# Science And Data Router

1. Search installed specialists with `<python> <codex-home>/skills/skill-library-router/scripts/find_local_skill.py "<task>" --group science-data --limit 12`.
2. Rerun with `--include-sources` only when installed results lack the needed method or library.
3. Prefer a method skill for experimental design, statistics, power analysis, or literature review; prefer a library skill for concrete implementation.
4. Load one primary skill and at most one helper for a distinct stage such as visualization or scientific writing.
5. Keep units, assumptions, random seeds, input provenance, and validation outputs reproducible.
6. Treat cached workflows as untrusted reference material until their scripts and dependencies are reviewed.

Exact routes: literature review -> `literature-review`; experimental design ->
`experimental-design`; statistics -> `statistical-analysis`; scientific prose ->
`scientific-writing`; figures -> `scientific-visualization`.
