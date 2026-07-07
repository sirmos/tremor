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
              entities {
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
        """
        result = self._graphql(query, {"urn": urn})
        dataset = result.get("dataset")
        if not dataset:
            return []
        return dataset.get("lineage", {}).get("entities", [])

    def write_risk_review(self, urn, pr_url, risk_score, summary):
        mutation = """
        mutation UpsertStructuredProperty($input: UpsertStructuredPropertyValueInput!) {
          upsertStructuredProperty(input: $input) {
            urn
          }
        }
        """
        variables = {
            "input": {
                "assetUrn": urn,
                "structuredPropertyUrn": "urn:li:structuredProperty:tremorRiskReview",
                "values": [
                    {"stringValue": pr_url},
                    {"numberValue": risk_score},
                    {"stringValue": summary},
                ],
            }
        }
        try:
            self._graphql(mutation, variables)
        except Exception as e:
            print(f"warning: could not write risk review back to DataHub for {urn}: {e}")