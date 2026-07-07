import os
import json
import subprocess
from github import Github

from tremor.datahub_client import DataHubClient
from tremor.risk import rank_downstream
from tremor.pr_comment import build_comment


def get_changed_files():
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        capture_output=True, text=True
    )
    return [f.strip() for f in result.stdout.splitlines() if f.strip()]


def load_manifest(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def main():
    server = os.environ["DATAHUB_SERVER"]
    token = os.environ["DATAHUB_TOKEN"]
    gh_token = os.environ["GITHUB_TOKEN"]
    threshold = int(os.environ.get("RISK_THRESHOLD", "40"))
    manifest_path = os.environ.get("MANIFEST_PATH", "tremor.manifest.json")

    manifest = load_manifest(manifest_path)
    changed_files = get_changed_files()
    urns = [manifest[f] for f in changed_files if f in manifest]

    if not urns:
        print("no mapped datasets changed, nothing to check")
        return

    client = DataHubClient(server, token)
    all_comments = []

    for urn in urns:
        downstream = client.get_downstream(urn)
        ranked = rank_downstream(downstream, threshold)
        comment = build_comment(urn, ranked)
        if comment:
            all_comments.append(comment)
            summary = f"{len(ranked)} risky downstream asset(s) flagged"
            top_score = ranked[0][0] if ranked else 0
            pr_url = os.environ.get("GITHUB_SERVER_URL", "") + "/" + os.environ.get("GITHUB_REPOSITORY", "") + "/pull/" + os.environ.get("PR_NUMBER", "")
            client.write_risk_review(urn, pr_url, top_score, summary)

    if not all_comments:
        print("no risky downstream impact found")
        return

    repo_name = os.environ["GITHUB_REPOSITORY"]
    pr_number = int(os.environ["PR_NUMBER"])
    gh = Github(gh_token)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    pr.create_issue_comment("\n\n---\n\n".join(all_comments))


if __name__ == "__main__":
    main()