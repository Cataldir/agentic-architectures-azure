# Learner distribution provenance

Source-qualified on 2026-10-10 by reading exact publisher release pages and relevant official SDK contracts. No download, install, import, resolution, test, cloud/API request or security/license closure occurred. These chosen reference versions are not asserted to be the latest.

- azure-identity==1.26.0: [exact release](https://pypi.org/project/azure-identity/1.26.0/).
- aiohttp==3.13.3: [exact release](https://pypi.org/project/aiohttp/3.13.3/).
- azure-cosmos==4.17.1: [exact release](https://pypi.org/project/azure-cosmos/4.17.1/).
- azure-servicebus==7.15.0: [exact release](https://pypi.org/project/azure-servicebus/7.15.0/).
- azure-eventhub==5.15.1: [exact release](https://pypi.org/project/azure-eventhub/5.15.1/).
- azure-eventhub-checkpointstoreblob==1.2.0: [exact release](https://pypi.org/project/azure-eventhub-checkpointstoreblob/1.2.0/).
- azure-search-documents==11.6.0: [exact release](https://pypi.org/project/azure-search-documents/11.6.0/).
- azure-ai-evaluation==1.18.8: [exact release](https://pypi.org/project/azure-ai-evaluation/1.18.8/).
- agent-framework-core==1.21.0: [exact release](https://pypi.org/project/agent-framework-core/1.21.0/).
- agent-framework-openai==1.16.0: [exact release](https://pypi.org/project/agent-framework-openai/1.16.0/).
- mcp==1.29.0: [exact release](https://pypi.org/project/mcp/1.29.0/).
- setuptools==80.9.0: [exact release](https://pypi.org/project/setuptools/80.9.0/).

The local exercise runtime has no third-party runtime dependencies. Editable packaging uses the explicit setuptools backend and package allowlist. Cloud SDK/direct pins require an approved resolved/hash-qualified transitive lock and private runner before execution. Async Azure identity needs aiohttp. Current Agent Framework generic OpenAIChatClient is explicitly routed to the approved Azure endpoint/credential; no ambient-provider fallback.

CPython 3.13.14 is parent-relayed reference metadata, not a verified installed runtime/release. CLI2.77.0, Bicep0.37.4 and azd1.20.0 are chosen source-qualified historical tool releases; actual command compatibility, binary hashes, environment, identity and ARM/readback remain pending. Workflow actions are immutable source revisions in an inert example; enabling them is separate approval.

The one-row private evaluation JSONL fixture is excluded from this code-only public projection. It is not calibrated truth. Unit tests contain original synthetic constants only. License selection, dependency license/security review, secret scan and anonymous clone/install qualification remain release requirements, with no completion claimed.

