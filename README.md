# Agentic Architectures on Azure — learner code

Public authored source edition for lessons 09, 14, 18, 21, 22, 24–27, 29–32 and 38 in [Cataldir/agentic-architectures-azure](https://github.com/Cataldir/agentic-architectures-azure), repository ID 1413720668. This directory contains manually reviewed original teaching code and synthetic unit fixtures. No clean clone, installation, test, model call or Azure deployment has been observed. Evaluation JSONL/data, model weights, narration, slides, book text, video, private history and credential values are excluded. No code LICENSE or open-source reuse grant has been adopted; external packages retain their own terms.

Start with the deterministic standard-library exercises. They teach decisions and failure states; they do not simulate an Azure credential, a model evaluation or an observed cloud deployment.

Future commands, after interpreter/resource admission:

```powershell
# Source acquisition; no clean clone or execution proof is supplied:
git clone https://github.com/Cataldir/agentic-architectures-azure.git
cd agentic-architectures-azure
# Use an approved project-local CPython 3.13.14 environment.
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m azure_course.local_demo
```

The starter deliberately makes the wrong release decision and loses compensation order. Read `starter/exercises.py`, implement the stated contracts, then compare with `azure_course/policy.py` and `azure_course/saga.py`. The same tests accept `COURSE_IMPLEMENTATION=starter`; the starter is expected to fail. No test has been run during authoring.

Azure path: resolve the direct pins in `requirements-cloud.in` into an approved immutable dependency lock, inspect the lock, install into a separate `.venv-cloud`, and capture `pip freeze`, wheel hashes and interpreter identity before use. Direct pins are not a transitive lock or proof of installability. Read `parameter-guide.md` and `SDK-PROVENANCE.md`; the cloud route still needs independently qualified environment inputs. Cloud modules refuse execution unless `AZURE_COURSE_EFFECTS=approved-disposable-lab`; the flag is a second safeguard, not permission or a budget grant. A private-network runner, tenant/subscription ownership, model/data rights, current quota and spend cap remain necessary.

The infrastructure uses pinned ARM resource API versions. User inputs select a unique resource group and immutable registry image; there is no `latest`, embedded key or automatic subscription selection. Lab14 consumes an approved private Container Apps environment; Lab18 creates isolated Cosmos accounts on an approved PE subnet; Lab22 modifies only named disposable APIM APIs; Lab27 creates a separate queue; Lab32 consumes an already approved Foundry judge and Search index; Lab38 composes these boundaries. No production/brownfield resource deletion is scripted.

Extend by adding a typed invariant, a negative case, then an effect adapter. Keep identity/tenant/release decisions explicit. Never retry an irreversible tool simply because the model endpoint changed. The reviewed workflow example remains under `workflows/`, outside GitHub Actions activation. Dependency/security qualification, anonymous clone/install proof and Azure compatibility checks remain outstanding. A future reusable code license requires a separate owner decision.
