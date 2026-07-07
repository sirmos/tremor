import os
from tremor.datahub_client import DataHubClient
from tremor.risk import rank_downstream
from tremor.pr_comment import build_comment

server = os.environ["DATAHUB_SERVER"]
token = os.environ["DATAHUB_TOKEN"]
threshold = int(os.environ.get("RISK_THRESHOLD", "20"))

urn = "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.analytics.order_details,PROD)"

client = DataHubClient(server, token)
downstream = client.get_downstream(urn)

print(f"found {len(downstream)} downstream entities")
for e in downstream:
    print(" -", e.get("name") or e.get("dashboardId") or e.get("urn"), "| type:", e.get("type"))

ranked = rank_downstream(downstream, threshold)
print(f"\n{len(ranked)} passed the risk threshold of {threshold}")
for score, entity in ranked:
    print(f"  risk {score}: {entity.get('name') or entity.get('dashboardId')}")

comment = build_comment(urn, ranked)
print("\n--- PR comment preview ---\n")
print(comment)
