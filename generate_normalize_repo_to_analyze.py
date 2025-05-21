import time

import pandas as pd
import requests

from github_config import HEADERS, SEARCH_URL
from logger_config import get_logger

"""
Module for identifying GitHub repositories that use two specified programming languages.

Environment:
    - Requires the 'GITHUB_TOKEN_GITCOLLABCOLLECTOR' environment variable to be set with a valid GitHub token.

Globals:
    - LANG_URL_TEMPLATE (str): GitHub API endpoint to retrieve languages used in a repository.
    - MAX_REPOS (int): Maximum number of repositories fetched per language (default: 150).
    - MIN_STARS (int): Minimum number of stars a repository must have to be considered (default: 3).
    - THRESHOLD (float): Maximum collaboration score to retain a language pair (default: 0.4).
    - logger (logging.Logger): Logger configured at INFO level.
    - github_langs (dict[str, str]): Dictionary mapping normalized language names to GitHub language identifiers.
"""
LANG_URL_TEMPLATE = "https://api.github.com/repos/{full_name}/languages"
MAX_REPOS = 150
MIN_STARS = 3
THRESHOLD = 0.4

logger = get_logger(__name__)

github_langs = {
    "Scheme": "Scheme",
    "ML": "ML",
    "Prolog": "Prolog",
    "Curry": "Curry",
    "Haskell": "Haskell",
    "OCaml": "OCaml",
    "Erlang": "Erlang",
    "C": "C",
    "Occam": "Occam",
    "Java": "Java",
    "CLU": "CLU",
    "E": "E",
}


def get_total_repo_count(lang1, lang2, stars=MIN_STARS):
    """
        Returns the total number of GitHub repositories matching two languages and a minimum star count.

        Parameters:
            lang1 (str): First programming language.
            lang2 (str): Second programming language.
            stars (int): Minimum number of stars. Default is MIN_STARS.

        Returns:
            int | None: The total count of matching repositories, or None on error.
    """
    query = f"language:{lang1} language:{lang2} stars:>={stars}"
    params = {"q": query}
    response = requests.get(SEARCH_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json().get("total_count", 0)
    else:
        logger.error(f"Error while counting repos for {lang1}-{lang2}: {response.status_code}")
        return None


def normalize_and_filter_pairs(csv_path: str, threshold: float = THRESHOLD) -> pd.DataFrame:
    """
        Normalizes language pairs from a CSV file and filters them by collaboration score threshold.

        Parameters:
            csv_path (str): Path to the CSV file with columns 'Language1', 'Language2', and 'CollaborationScore'.
            threshold (float): Maximum collaboration score to keep a pair. Default is THRESHOLD.

        Returns:
            pd.DataFrame: DataFrame with columns 'Lang1_norm' and 'Lang2_norm' for valid pairs.
    """
    df = pd.read_csv(csv_path, sep=';')
    df['Lang1_norm'] = df['Language1'].map(github_langs)
    df['Lang2_norm'] = df['Language2'].map(github_langs)
    df = df.dropna(subset=['Lang1_norm', 'Lang2_norm'])
    df = df[df['CollaborationScore'] <= threshold]
    logger.info(f"{len(df)} pairs retained with a score ≤ {threshold}")
    return df[['Lang1_norm', 'Lang2_norm']]


def fetch_repos_for_lang(lang: str, stars: int = MIN_STARS, max_repos: int = MAX_REPOS):
    """
        Fetches a list of GitHub repository full names for a given language, sorted by recent updates.

        Parameters:
            lang (str): Programming language to search for.
            stars (int): Minimum number of stars. Default is MIN_STARS.
            max_repos (int): Maximum number of repositories to return. Default is MAX_REPOS.

        Returns:
            list[str]: List of repository full names (e.g., "owner/repo").
    """
    query = f"language:{lang} stars:>={stars}"
    params = {
        "q": query,
        "sort": "updated",
        "order": "desc",
        "per_page": min(max_repos, 100)
    }
    try:
        response = requests.get(SEARCH_URL, headers=HEADERS, params=params)
        if response.status_code != 200:
            logger.error(f"Error fetching repositories for {lang}: {response.status_code} - {response.text}")
            return []
        return [repo["full_name"] for repo in response.json().get("items", [])]
    except Exception as e:
        logger.exception(f"Exception while fetching repositories for {lang}: {e}")
        return []


def repo_uses_both_languages(full_name: str, lang1: str, lang2: str) -> bool:
    """
        Checks if a GitHub repository uses both specified programming languages.

        Parameters:
            full_name (str): Repository full name (e.g., "owner/repo").
            lang1 (str): First language to check.
            lang2 (str): Second language to check.

        Returns:
            bool: True if both languages are used in the repo, False otherwise or on error.
    """
    url = LANG_URL_TEMPLATE.format(full_name=full_name)
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            logger.error(f"Error fetching languages for {full_name}: {response.status_code}")
            return False
        languages = response.json().keys()
        return lang1 in languages and lang2 in languages
    except Exception as e:
        logger.exception(f"Exception while checking languages for {full_name}: {e}")
        return False


def collect_all_repos(filtered_df: pd.DataFrame, output_csv: str = "repos_to_analyze.csv"):
    """
        Collects GitHub repositories using both languages from each normalized pair in the DataFrame.

        Parameters:
            filtered_df (pd.DataFrame): DataFrame with columns 'Lang1_norm' and 'Lang2_norm'.
            output_csv (str): Path to the output CSV file. Default is "repos_to_analyze.csv".

        Returns:
            None: Writes a CSV file with valid repositories.
    """
    all_repos = []

    for _, row in filtered_df.iterrows():
        lang1, lang2 = row['Lang1_norm'], row['Lang2_norm']
        logger.info(f"|-> Searching repositories for language pair: {lang1} – {lang2}")

        repos1 = fetch_repos_for_lang(lang1)
        time.sleep(1)
        repos2 = fetch_repos_for_lang(lang2)
        time.sleep(1)

        candidate_repos = list(set(repos1 + repos2))

        for full_name in candidate_repos:
            if repo_uses_both_languages(full_name, lang1, lang2):
                logger.info(f"{full_name} uses both {lang1} and {lang2}")
                all_repos.append({
                    "FullName": full_name,
                    "Lang1": lang1,
                    "Lang2": lang2
                })
            else:
                logger.debug(f"{full_name} does not use both {lang1} and {lang2}")

            time.sleep(0.5)

    if all_repos:
        df_out = pd.DataFrame(all_repos)
        df_out.to_csv(output_csv, index=False)
        logger.info(f"{len(df_out)} valid repositories saved to {output_csv}")
    else:
        logger.warning("No repositories retained after language check.")
