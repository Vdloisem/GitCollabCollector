# GitHub Cross-Language Collaboration Analyzer

This project aims to **identify and analyze technical difficulties** in GitHub repositories that use **two different programming languages**. It computes metrics of inter-language collaboration difficulty based on the presence of interoperability-related keywords found in:

- Pull Requests (PRs)
- Issues
- README files

## Features

- Automatically selects GitHub repositories with two languages based on low collaboration score.
- Fetches README, PRs, and issues using the GitHub API.
- Scans for keywords indicating interoperability difficulties (e.g., FFI, JNI, GraalVM, etc.).
- Generates detailed and summary CSV reports.
- Filters out repositories with insufficient PRs or issues (< 5 each).
- Ready for empirical validation of a collaboration metric.

## Repository Structure

- `collab_difficulty_scanner.py` — Main analysis engine  
- `generate_normalize_repo_to_analyze.py` — Language pair filtering and repo collection  
- `github_config.py` — GitHub token and API headers  
- `logger_config.py` — Logger setup  
- `repo_difficulty_detail.csv` — Output: per-repository difficulty analysis  
- `lang_pair_difficulty_summary.csv` — Output: aggregated difficulty statistics  
- `CollaborationMetric_Languages_Cleaned.csv` — Input: language pairs and collaboration scores  

## Setup

### Prerequisites

- Python 3.9+
- GitHub API token set as an environment variable:
```bash
export GITHUB_TOKEN_GITCOLLABCOLLECTOR="your_token_here"
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

Prepare a CSV file named `CollaborationMetric_Languages_Cleaned.csv` with the columns:

- `Language1`
- `Language2`
- `CollaborationScore`

You have two options to obtain this file:

1. **Generate the report yourself** using the Haskell program available at:  
   -> https://github.com/Vdloisem/MCC.git  
   This tool computes collaboration scores between pairs of programming languages based on a formal taxonomy.

2. **Download the already generated report** from Zenodo (recommended for quick start):  
   -> [Zenodo Record](https://zenodo.org/records/11077187?token=eyJhbGciOiJIUzUxMiJ9.eyJpZCI6IjQ3MDAxNTQ1LTNmYzUtNDFmOC05ZTIwLTA0ZWVmZWE1Y2FiOSIsImRhdGEiOnt9LCJyYW5kb20iOiIxZTA2MzEzZmUxYjQzMWY2MWFkMDhiYjY0ODBmMmVjOCJ9.wQQVUC4AWlVStEtY7zSoEIAGh6wOHHrlrH6AtI3VpODXTJQCCLj4DYAuOkCPF6lkTLNQSjC9D_Cv9yhMm6iLmQ)


Run the main analysis:

```bash
python main.py
```

This will:

- Normalize language pairs  
- Collect repositories with both languages  
- Analyze cross-language integration issues  
- Export two reports:
  - `repo_difficulty_detail.csv`
  - `lang_pair_difficulty_summary.csv`

## Output

### `repo_difficulty_detail.csv`

Contains the following fields:

- `Lang1`, `Lang2`, `FullName`
- `artifacts_analyzed`
- `difficulty_keywords_found`
- `difficulty_density`
- `repo_has_difficulty` (boolean)
- `keywords_detected` (semicolon-separated list)

### `lang_pair_difficulty_summary.csv`

Contains:

- `Lang1`, `Lang2`
- `total_repos`
- `repos_with_difficulty`
- `avg_difficulty_density`
- `avg_artifacts_analyzed`
- `difficulty_rate`
- `true_total_available` (GitHub)
- `rarity_score` (based on GitHub visibility)

## License

This project is licensed under the MIT License — see `LICENSE` for details.

## Author

**Mikel Vandeloise** — [GitHub](https://github.com/mikelvandeloise)
