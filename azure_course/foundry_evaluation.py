"""Actual SDK judge call requires explicit effects admission; never fixture truth."""
import json
import os
from pathlib import Path
from .cloud_guard import require_effects, endpoint


def main() -> None:
    require_effects()
    from azure.identity import ManagedIdentityCredential
    from azure.ai.evaluation import evaluate, GroundednessEvaluator
    data = Path(os.environ["EVALUATION_DATA"])
    if data.is_symlink() or not data.is_file() or data.stat().st_size > 1024 * 1024:
        raise ValueError("regular, bounded reviewed evaluation set required")
    rows = [json.loads(line) for line in data.read_text(encoding="utf-8").splitlines()]
    if not rows or len(rows) > 100:
        raise ValueError("1..100 cases required")
    if any(not all(isinstance(r.get(k), str) and r[k] for k in
                   ("query", "response", "context", "ground_truth")) for r in rows):
        raise ValueError("complete reviewed cases required")
    credential = ManagedIdentityCredential(client_id=os.environ["AZURE_CLIENT_ID"])
    judge = GroundednessEvaluator(model_config={
        "azure_endpoint": endpoint("AZURE_OPENAI_ENDPOINT", ".openai.azure.com"),
        "azure_deployment": os.environ["APPROVED_JUDGE_DEPLOYMENT"],
        "api_version": "2024-10-21",
    }, credential=credential, threshold=3)
    out = Path("results")
    out.mkdir(exist_ok=True)
    evaluate(data=str(data), evaluators={"groundedness": judge},
             evaluator_config={"groundedness": {"column_mapping": {
                 "query": "${data.query}", "response": "${data.response}",
                 "context": "${data.context}"}}},
             output_path=str(out / "groundedness.json"))
    # No promotion here. Calibrate judge vs blinded human labels, preserve errors,
    # then compose policy.Evidence from exact complete candidate/baseline runs.
    print("Judge request finished; inspect rows/calibration before any release decision")


if __name__ == "__main__":
    main()
