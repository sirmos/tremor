# Tremor

A pull request touching a dbt model rarely stays contained to that model. It ripples into dashboards, ML features, and other pipelines downstream. Most teams find out after merge, when something breaks.

Tremor reads a PR's diff, walks the DataHub lineage graph to find what's downstream of the tables that changed, and judges which of those downstream assets are actually worth worrying about, not just everything technically connected. It posts the risky ones as a PR comment with owners tagged, and writes the decision back onto the asset in DataHub, so the next PR touching the same table inherits that history instead of starting from zero.

## Why not just list every downstream table

Because that's noise. A table with a dozen downstream consumers doesn't need a dozen lines in a PR comment. Tremor scores each downstream asset using signals already in DataHub: whether it's a BI-facing asset (Power BI, Tableau, Looker), ownership, criticality tags, and recent quality health. Only assets above a risk threshold get surfaced, and repeated assets with the same name are collapsed into a single row with a count.

## How it works

1. Tremor reads the PR diff and maps changed files to DataHub dataset URNs, using a manifest file (`tremor.manifest.json`) that maps repo paths to URNs.
2. It queries DataHub's GraphQL API for downstream lineage of each changed dataset.
3. Each downstream asset gets a risk score based on platform (BI tools score higher), ownership, criticality tags, and quality signal health.
4. Assets above the risk threshold are grouped and posted as a PR comment.
5. Tremor writes a `Tremor Risk Review` structured property back onto the changed dataset in DataHub, recording the PR link, the risk score, and a short summary. The next agent or person that looks at that table sees the history instead of starting cold.

## Setup

### 1. Register the structured property (one-time, per DataHub instance)

Tremor writes its findings back using a custom structured property. Register it once:

```bash
datahub properties upsert -f setup/tremor_property.yaml
```

### 2. Add the GitHub Actions workflow

Add a workflow like `.github/workflows/example-usage.yml` (included in this repo) that triggers on `pull_request` and calls this action.

### 3. Set repository secrets

- `DATAHUB_SERVER` — your DataHub GMS endpoint
- `DATAHUB_TOKEN` — a personal access token with read and write access

### 4. Add a manifest file

Create `tremor.manifest.json` at your repo root, mapping file paths to DataHub dataset URNs:

```json
{
  "models/order_details.sql": "urn:li:dataset:(urn:li:dataPlatform:snowflake,your_db.schema.table,PROD)"
}
```

## Local testing

A standalone test script is included in `setup/test_run.py`, useful for testing the DataHub query and risk scoring directly without needing a real PR diff:

```bash
pip install -r requirements.txt
export DATAHUB_SERVER="http://localhost:8080"
export DATAHUB_TOKEN="your-token"
export RISK_THRESHOLD="40"
python3 -m setup.test_run
```

## What Tremor is not

It's not a replacement for DataHub's lineage UI or the Analytics Agent. It's a narrow tool for one moment: the point right before you hit merge, when you actually have a chance to stop a break before it ships.

## License

Apache 2.0