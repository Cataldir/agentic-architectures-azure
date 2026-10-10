# Parameter files and runner bindings

Copy the relevant labNN.parameters.example.json into a protected labNN.parameters.json and replace every owner placeholder with an approved value. A placeholder is a stop condition, never a deployable default. Review exact resource IDs and what-if with the accepted target owner. The parameter file contains identifiers, not tokens/keys; keep credentials in the runner's secure facilities. Lab38 reuses the accepted lab14 shape as lab38.parameters.json.

The azd azure.yaml selects infra/main.bicep. Explicit mapping to the accepted azd environment/parameters is required before provision/deploy; no environment or credentials are bundled. The main template intentionally consumes an existing private landing zone and immutable worker image. It does not create networks, DNS links, registry secrets or Foundry projects.

Runtime bindings:
- Local reference: no Azure environment required.
- Cosmos/read tool: effect guard, AZURE_CLIENT_ID of an attached identity, COSMOS_ENDPOINT and COURSE_TENANT; seed order1 with id/tenant/status through the admitted data owner.
- ACA Dapr: dedicated DAPR_STATE_STORE from worker.bicep; SERVICEBUS_FQDN/QUEUE; tenant and MI. The named component is scoped to the unique app ID.
- Queue producer/session saga: namespace, tenant, attached identity with only the required queue roles; saga also requires Cosmos endpoint and COURSE_SAGA_ID/COURSE_FAILURE.
- Search workflow: SEARCH_ENDPOINT/INDEX, tenant, explicit approved Azure inference endpoint/deployment. Hybrid mode additionally needs a valid reviewed embedding vector and matching EMBEDDING_DIMENSIONS; no fake vectors.
- Judge: protected EVALUATION_DATA, approved judge deployment and endpoint, MI, dataset/call budget. The synthetic schema fixture is excluded from the public code projection.
- Event Hubs: approved namespace, course-audit consumer group, telemetry hub and scoped checkpoints Blob URL/identity; private source and a60-second timer. Actual termination/checkpoint behavior still requires runner verification.

Exact CLI/package versions, rights, actual subscription/private network, quotas and telemetry configuration remain independently qualified. No “export these variables” step supplies authority.

