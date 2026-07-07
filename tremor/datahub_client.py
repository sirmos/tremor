import requests


class DataHubClient:
    def __init__(self, server, token):
        self.server = server.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _graphql(self, query, variables=None):
        resp = requests.post(
            f"{self.server}/api/graphql",
            headers=self.headers,
            json={"query": query, "variables": variables or {}},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(data["errors"])
        return data["data"]

    def get_downstream(self, urn):
        query = """
        query GetDownstream($urn: String!) {
          dataset(urn: $urn) {
            urn
            name
            lineage(input: { direction: DOWNSTREAM }) {
              relationships {
                type
                entity {
                  urn
                  type
                  ... on Dataset {
                    name
                    ownership { owners { owner { ... on CorpUser { username } } } }
                    tags { tags { tag { name } } }
                    health { status }
                  }
                  ... on Dashboard {
                    dashboardId
                    tool
                    ownership { owners { owner { ... on CorpUser { username } } } }
                  }
                }
              }
            }
          }
        }
        """
        result = self._graphql(query, {"urn": urn})
        dataset = result.get("dataset")
        if not dataset:
            return []
        relationships = dataset.get("lineage", {}).get("relationships", [])
        return [r["entity"] for r in relationships if r.get("entity")]

    def write_risk_review(self, urn, pr_url, risk_score, summary):
        mutation = """
        mutation UpsertStructuredProperties($input: UpsertStructuredPropertiesInput!) {
          upsertStructuredProperties(input: $input) {
            properties {
              structuredProperty {
                urn
              }
            }
          }
        }
        """
        variables = {
            "input": {
                "assetUrn": urn,
                "structuredPropertyInputParams": [
                    {
                        "structuredPropertyUrn": "urn:li:structuredProperty:io.tremor.riskReview",
                        "values": [
                            {"stringValue": f"{pr_url} | risk {risk_score} | {summary}"}
                        ],
                    }
                ],
            }
        }
        try:
            self._graphql(mutation, variables)
        except Exception as e:
            print(f"warning: could not write risk review back to DataHub for {urn}: {e}")