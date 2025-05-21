import time

import pandas as pd
import requests

import generate_normalize_repo_to_analyze
from github_config import HEADERS
from logger_config import get_logger

"""
Module for collecting and analyzing cross-language collaboration issues in GitHub repositories.

Environment:
    - Requires the 'GITHUB_TOKEN_GITCOLLABCOLLECTOR' environment variable to be set with a valid GitHub token.

Globals:
    - MAX_PR_PAGES (int): Max number of pages to fetch for pull requests.
    - MAX_PAGES_ISSUES (int): Max number of pages to fetch for issues.
    - logger (logging.Logger): Logger configured at INFO level.
    - KEYWORDS (list[str]): List of domain-specific keywords related to cross-language integration issues.
"""
MAX_PR_PAGES = 50
MAX_PAGES_ISSUES = 10

logger = get_logger(__name__)

KEYWORDS = [
    # Interop and FFI
    "interop", "interoperability", "cross-language", "multi-language", "multilanguage",
    "foreign function", "foreign function interface", "FFI", "FFI binding", "FFI bindings",
    "FFI bridge", "FFI layer", "FFI wrapper", "ffi", "ffi binding", "ffi bindings", "ffi bridge",
    "ffi layer", "ffi wrapper", "foreign language interface", "foreign function call",
    "foreign code interface", "language binding", "language bindings", "language bridge",
    "interop layer", "native interface", "interop wrapper", "native binding", "native bindings",
    "platform binding", "platform bindings", "interop layer", "interlanguage wrapper",
    "interlanguage adapter", "binding generator", "interop toolkit",

    # Explicit technical integration
    "wrapper", "glue code", "interface adapter", "interface adapters", "custom wrapper",
    "manual wiring", "binding", "bridge", "stub", "interop code", "language integration layer",
    "handwritten adapter", "adapter layer", "interlanguage adapter", "shim layer",
    "compatibility wrapper", "binding layer", "integration scaffold", "integration module",
    "wrapper module", "bridge module", "intermediate wrapper", "proxy layer", "adapter pattern",
    "interop facade", "had to write a wrapper", "had to adapt manually", "manual integration logic",
    "glue logic", "hand-coded adapter", "language glue", "bridge logic",

    # Interlanguage incompatibilities
    "language mismatch", "interface mismatch", "type mismatch", "ABI mismatch",
    "symbol not found", "undefined reference", "signature mismatch",
    "method signature mismatch", "incompatible types", "type coercion failed",
    "binary incompatibility", "calling convention mismatch", "missing symbol", "undefined symbol",
    "unresolved external", "linker error", "linking error", "symbol clash",
    "symbol conflict", "cannot resolve symbol", "failed to link", "undefined identifier",
    "foreign function not found", "module not found", "dll not found", "so not found",
    "missing foreign declaration", "invalid cast", "foreign type error",
    "type conversion error", "wrong arity", "unexpected argument type", "wrong type at runtime",

    # Interoperability frameworks and tools
    "SWIG", "swig", "JNI", "jni", "JNA", "jna", "JPL", "jpl", "JSR223", "jsr223", "jsr",
    "GraalVM", "graalvm", "Truffle", "truffle", "javacall", "Java Native Interface"
    "pybind11", "CFFI", "cffi", "Ctypes", "ctype", "NIF", "nif", "NAPI", "napi",
    "swi-prolog-jpl", "jpl.jar", "SWI", "boost.python", "python-cffi", "python bindings",
    "foreign function interface", "libffi", "dlopen", "dlsym", "ctypeslib", "node-addon-api",
    "nan", "NAN", "node-gyp", "node-ffi", "ffi-napi", "node-FFI", "FFI-napi", "ffi-NAPI", "FFI-NAPI",
    "Native Implemented Function", "native implemented function", "port driver", "Erlang port",
    "C node", "erlang port", "c node", "polyglot context", "GraalVM interop", "Graal interop",
    "graalvm interop", "graal interop", "Graal interoperability", "graalvm interoperability",
    "graal interoperability", "IDL", "idl", "Interface Definition Language", "CORBA", "corba",
    "Thrift", "thrift", "gRPC", "grpc", "protobuf interop", "protobuf interoperability",
    "P/Invoke", "Platform Invocation", "platform invocation", "CLR interop", "clr interop",
    "COM interop", "com interop", "CLR interoperability", "clr interoperability",
    "COM interoperability", "com interoperability", "DllImport", "dllimport",
    "cbindgen", "bindgen", "Rust FFI", "Rust ffi", "rust FFI", "rust ffi",
    "Rust interoperability", "extern \"C\"",

    # Specific issues related to interoperability
    "integration problem", "integration issue", "integration error", "errors integrating",
    "failed integration", "integration fails", "integration failed", "manual override",
    "configuration hell", "multi-build-system", "multiple compilers", "fails to integrate",
    "can't integrate", "unable to integrate", "manual integration", "manual glue", "manual config",
    "manual fix", "manual patch", "manual adjustment", "handwritten interop", "multi-build-system",
    "multiple compilers", "toolchain mismatch",  "fragile integration", "brittle integration",
    "unstable integration", "hard to maintain interop", "interop not scalable",

    # Interface modules or syntaxes
    "foreign predicate", "interface module", "foreign module", "foreign interface",
    "interface declaration", "external interface", "interop declaration",
    "language interface", "bridge module", "interop module",
    "foreign block", "foreign import", "foreign export",
    "native declaration", "foreign definition", "external binding",
    "module binding", "foreign section",
]


def fetch_paginated_artifacts(repo, artifact_type, per_page=100, max_pages=50, skip_condition=None, label="artifact"):
    """
    Fetches paginated artifacts (issues or pull requests) from a GitHub repository.

    Parameters:
        repo (str): Repository full name (e.g., "owner/repo").
        artifact_type (str): "issues" or "pulls", used in the GitHub API endpoint.
        per_page (int): Number of items per page (max 100). Default is 100.
        max_pages (int): Maximum number of pages to fetch. Default is 50.
        skip_condition (callable, optional): Function that returns True for items to skip.
        label (str): Label for logging purposes (e.g., "issue" or "pull request").

    Returns:
        list[dict]: List of artifacts retrieved from the API, filtered if needed.
    """
    all_items = []
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/repos/{repo}/{artifact_type}"
        params = {"state": "all", "per_page": per_page, "page": page}
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code != 200:
            logger.error(f"Error fetching {artifact_type} for {repo}, page {page}: {response.status_code}")
            break

        items = response.json()
        if not items:
            logger.debug(f"No more {label}s found for {repo} at page {page}.")
            break

        for item in items:
            if skip_condition and skip_condition(item):
                continue
            all_items.append(item)

        if len(items) < per_page:
            logger.debug(f"Fetched last page ({page}) of {label}s for {repo}.")
            break

    logger.info(f"Fetched {len(all_items)} {label}s for {repo}")
    return all_items


def fetch_pull_requests(repo, per_page=100, max_pages=50):
    """
        Fetches all pull requests from a GitHub repository using pagination.

        Parameters:
            repo (str): Repository full name (e.g., "owner/repo").
            per_page (int): Number of pull requests per page. Default is 100.
            max_pages (int): Maximum number of pages to fetch. Default is 50.

        Returns:
            list[dict]: List of pull requests retrieved from the API.
    """
    return fetch_paginated_artifacts(repo, "pulls", per_page, max_pages, label="pull request")


def fetch_issues(repo, per_page=100, max_pages=10):
    """
        Fetches all issues (excluding pull requests) from a GitHub repository using pagination.

        Parameters:
            repo (str): Repository full name (e.g., "owner/repo").
            per_page (int): Number of issues per page. Default is 100.
            max_pages (int): Maximum number of pages to fetch. Default is 10.

        Returns:
            list[dict]: List of issues retrieved from the API, excluding pull requests.
        """
    return fetch_paginated_artifacts(repo, "issues", per_page, max_pages, skip_condition=lambda i: "pull_request" in i,
                                     label="issue")


def fetch_readme(repo):
    """
        Fetches and decodes the README file from a GitHub repository.

        Parameters:
            repo (str): Repository full name (e.g., "owner/repo").

        Returns:
            str: The decoded README content as a UTF-8 string, or an empty string on error.
    """
    url = f"https://api.github.com/repos/{repo}/readme"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        logger.error(f"Error fetching README for {repo}: {response.status_code}")
        return ""
    content = response.json().get("content", "")
    encoding = response.json().get("encoding", "base64")
    if encoding == "base64":
        import base64
        try:
            return base64.b64decode(content).decode("utf-8", errors="ignore")
        except Exception as e:
            logger.exception(f"Failed to decode README for {repo}: {e}")
            return ""
    return ""


def analyze_text(text):
    """
        Returns the list of keywords found in the given text.

        Parameters:
            text (str): The text to analyze.

        Returns:
            str: keywords found in the text.
    """
    return [kw for kw in KEYWORDS if kw in text.lower()]


def analyze_repo(repo):
    """
        Analyzes a GitHub repository for occurrences of predefined keywords in pull requests, issues, and README.

        Parameters:
            repo (str): Repository full name (e.g., "owner/repo").

        Returns:
            tuple[int, int, int, int]: (score, total_artifacts, pr_count, issue_count) where:
                - score is the total number of keyword occurrences found,
                - total_artifacts is the number of analyzed elements (PRs + issues + README).
                - pr_count is the count of pull requests
                - issue_count is the count of issues
    """
    prs = fetch_pull_requests(repo)
    issues = fetch_issues(repo)
    readme = fetch_readme(repo)

    pr_count = len(prs)
    issue_count = len(issues)

    matched_keywords = []

    for pr in prs:
        text = (pr.get("title") or "") + " " + (pr.get("body") or "")
        matched_keywords.extend(analyze_text(text))

    for issue in issues:
        if "pull_request" in issue:
            continue
        text = (issue.get("title") or "") + " " + (issue.get("body") or "")
        matched_keywords.extend(analyze_text(text))

    matched_keywords.extend(analyze_text(readme))

    total_artifacts = pr_count + issue_count + 1
    score = len(matched_keywords)
    return score, total_artifacts, pr_count, issue_count, matched_keywords


def analyze_all(csv_path, detailed_output, summary_output, max_repos):
    """
        Analyzes a set of GitHub repositories listed in a CSV file and generates detailed and summary reports.

        Parameters:
            csv_path (str): Path to the CSV file containing repositories with columns 'FullName', 'Lang1', 'Lang2'.
            detailed_output (str): Path to the output CSV file for per-repository analysis.
            summary_output (str): Path to the output CSV file for per-language-pair summary.
            max_repos (int): Maximum number of repositories to consider per language pair (used for rarity score).

        Returns:
            None: Writes two CSV files (detailed and summary) and logs the results.
    """
    df = pd.read_csv(csv_path, sep=',')
    all_results = []
    skipped_repos = 0

    for _, row in df.iterrows():
        repo = row['FullName']
        lang1 = row['Lang1']
        lang2 = row['Lang2']
        logger.info(f"|-> Analysis of {repo} ({lang1}-{lang2})...")

        try:
            score, total_items, pr_count, issue_count, keywords_found = analyze_repo(repo)
        except Exception as e:
            logger.exception(f"Error analysing repository {repo} : {e}")
            continue

        if pr_count < 5 or issue_count < 5:
            logger.debug(f"Skipping {repo} (PRs: {pr_count}, Issues: {issue_count})")
            skipped_repos += 1
            continue

        has_difficulty = score > 0
        difficulty_density = round(score / total_items, 4) if total_items else 0.0

        all_results.append({
            "Lang1": lang1,
            "Lang2": lang2,
            "FullName": repo,
            "artifacts_analyzed": total_items,
            "difficulty_keywords_found": score,
            "difficulty_density": difficulty_density,
            "repo_has_difficulty": has_difficulty,
            "keywords_detected": "; ".join(set(keywords_found))
        })
        time.sleep(0.5)

    logger.info(f"Skipped {skipped_repos} repositories with insufficient PRs or issues.")

    detailed_df = pd.DataFrame(all_results)
    detailed_df.to_csv(detailed_output, sep=';', index=False)
    logger.info(f"Details recorded in {detailed_output}")

    summary = (
        detailed_df
        .groupby(['Lang1', 'Lang2'])
        .agg(
            total_repos=('FullName', 'count'),
            repos_with_difficulty=('repo_has_difficulty', 'sum'),
            avg_difficulty_density=('difficulty_density', 'mean'),
            avg_artifacts_analyzed=('artifacts_analyzed', 'mean')
        )
        .reset_index()
    )
    summary['difficulty_rate'] = summary['repos_with_difficulty'] / summary['total_repos']

    summary['true_total_available'] = summary.apply(
        lambda row_rc: generate_normalize_repo_to_analyze.get_total_repo_count(row_rc['Lang1'], row_rc['Lang2']),
        axis=1
    )

    summary['rarity_score'] = summary.apply(
        lambda row_rs: round(
            1 - (row_rs['total_repos'] / min(row_rs['true_total_available'], (max_repos * 2))), 4
        ) if row_rs['true_total_available'] and row_rs['true_total_available'] > 0 else None,
        axis=1
    )

    time.sleep(1)
    summary.to_csv(summary_output, sep=';', index=False)
    logger.info(f"\nEnriched summary recorded in {summary_output}")
    logger.debug(f"\n{summary.to_string(index=False)}")
