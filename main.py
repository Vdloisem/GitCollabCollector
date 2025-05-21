import collab_difficulty_scanner
import generate_normalize_repo_to_analyze

if __name__ == '__main__':
    filtered_pairs = generate_normalize_repo_to_analyze.normalize_and_filter_pairs(
        "CollaborationMetric_Languages_Cleaned.csv")
    generate_normalize_repo_to_analyze.collect_all_repos(filtered_pairs, "repos_to_analyze.csv")
    collab_difficulty_scanner.analyze_all(
        csv_path="repos_to_analyze.csv",
        detailed_output="repo_difficulty_detail.csv",
        summary_output="lang_pair_difficulty_summary.csv",
        max_repos=150
    )
