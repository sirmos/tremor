# Tremor

A pull request touching a dbt model rarely stays contained to that model. It ripples into dashboards, ML features, and other pipelines downstream. Most teams find out after merge, when something breaks.

Tremor reads your PR diff, walks the DataHub lineage graph to find what's downstream of the tables you changed, and judges which of those downstream assets are actually worth worrying about, not just everything technically connected. It posts the risky ones as a PR comment with owners tagged, and writes the decision back to DataHub so the next PR touching the same table inherits that history.

## Why not just list every downstream table

Because that's noise. A table with 40 downstream consumers doesn't need 40 lines in a PR comment. Tremor scores each downstream asset using signals already in DataHub: criticality tags, ownership, recent quality assertion failures, and whether it feeds a dashboard vs a one-off scratch query. Only assets above a risk threshold get surfaced.

## How it works

1. Tremor reads the PR diff and maps changed files to DataHub dataset URNs (via a naming convention or a manifest file you provide).
2. It queries DataHub's GraphQL API for downstream lineage of each changed dataset.
3. Each downstream asset gets a risk score based on ownership, tags, and quality signal freshness.
4. Assets above the risk threshold are grouped by owner and posted as a PR comment.
5. Tremor writes a `TremorRiskReview` structured property back onto the changed dataset in DataHub, recording the PR link, the risk score, and the timestamp. The next agent or person that looks at that table sees the history instead of starting from zero.

## Setup

Add `.github/workflows/tremor.yml` to your repo (see `example-usage.yml` for a working template) and set these repository secrets:

- `DATAHUB_SERVER` - your DataHub GMS endpoint
- `DATAHUB_TOKEN` - a personal access token with read and write access
- `GITHUB_TOKEN` - provided automatically by GitHub Actions

## Local testing

```bash
pip install -r requirements.txt
python -m tremor.main --diff sample.diff --dry-run
```

## What Tremor is not

It's not a replacement for DataHub's lineage UI or the Analytics Agent. It's a narrow tool for one moment: the point right before you hit merge, when you actually have a chance to stop a break before it ships.

## License

Apache 2.0
