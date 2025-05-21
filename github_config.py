import os

"""
Module for GitHub API authentication and base configuration.

Environment:
    - Requires the 'GITHUB_TOKEN_GITCOLLABCOLLECTOR' environment variable to be set with a valid GitHub token.

Globals:
    - GITHUB_TOKEN (str): GitHub personal access token retrieved from environment variable.
    - HEADERS (dict): Authorization headers to be used in GitHub API requests.
    - SEARCH_URL (str): GitHub Search API endpoint for repositories.
"""
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN_GITCOLLABCOLLECTOR")
if not GITHUB_TOKEN:
    raise ValueError("The GitHub token is not defined in the GITHUB_TOKEN_GITCOLLABCOLLECTOR environment variable.")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
SEARCH_URL = "https://api.github.com/search/repositories"
