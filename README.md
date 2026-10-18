# Smell-Aware-EA-Mining

# Smell-Aware EA Mining

This repository contains the artifacts for **A Smell-Aware Refinement Framework for Enterprise Architecture Mining**. The framework parses ArchiMate models, detects Enterprise Architecture (EA) smells, estimates their severity, and supports evidence-aware model refinement.

## Quick Start

### Requirements

- Python 3.10+
- `networkx`
- `openpyxl`
- A directory containing ArchiMate `.archimate` models

### Installation

```bash
python -m pip install networkx openpyxl
```

### Usage

Set `MODELS_FOLDER` and `REPORT_OUTPUT` in `src/ea_smell_detector/ea_smell_catalog_detector.py`, then run:

```bash
python src/ea_smell_detector/ea_smell_catalog_detector.py
```

The detector searches the input directory recursively and writes:

- `ea_smell_results.json` — detailed evidence and severity for each instance
- `ea_smell_results.csv` — tabular results
- `ea_smell_results.xlsx` — results and summary worksheets
- `ea_smell_summary.json` — per-model smell counts

## Supported smells

The implementation includes 42 EA-smell detectors from the RWTH Aachen catalogue, covering dependency, modularity, service, data, lifecycle, naming, documentation, and layering smells.

Severity is computed as:

```text
severity = 0.7 × rule_strength + 0.3 × structural_importance
```

## Evaluation Summary

- **Smell-count agreement:** 279 detected vs. 293 expected instances; precision 0.832, recall 0.792, F1-like score 0.811.
- **Model refinement:** aggregate F1 increased from 0.696 to 0.857 across four primary models.
- **Scalability:** 961 models analysed; median time 0.088 s and 95th-percentile time 4.536 s.

The count-based smell score compares smell counts rather than matched occurrences. Refinement results are therefore preliminary evidence and should be interpreted with the evaluation scope described in the paper.

## Repository Structure

```text
src/ea_smell_detector/   detector and smell rules
models/                  ArchiMate input models
evaluation 1/            smell-count evaluation
evaluation 2/            refinement evaluation
evaluation 3/            scalability evaluation
```

## Citation

```bibtex
@article{mohammadinezhad2026smellaware,
  title  = {A Smell-Aware Refinement Framework for Enterprise Architecture Mining},
  author = {Mohammadinezhad, Mohsen and Shams Aliee, Fereidoon}
}
```

## License

MIT License. See [LICENSE](LICENSE).

