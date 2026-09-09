"""Non-consuming admission for the one newly authorized formal opportunity."""
from __future__ import annotations

from pathlib import Path
import json

import durability
import eligibility_coherence as coherence

FORBIDDEN_BEFORE_CONSUME = (
    "FORMAL_ATTEMPT.json", "BASELINE_ATTEMPT.json", "LAUNCHER_ATTEMPT.json",
    "baseline.json", "seal.json", "runtime/START.json",
)


def _require(condition, reason):
    if not condition:
        raise coherence.CoherenceError(reason)


def _write(path, value, mode=0o400):
    raw = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()
    durability.exclusive_bytes(path, raw, mode)


def validate_admission_receipt(path, *, config, contract, review, control):
    value = coherence.load(path)
    required = {
        "schema", "result", "formal_attempt", "formal_budget_consumed", "run_id",
        "contract_id", "contract_sha256", "binding_sha256", "review_sha256",
        "control_plane_evidence_sha256", "preparation", "comparison",
        "new_allowance_total", "new_allowance_used", "global_ordinal",
    }
    _require(isinstance(value, dict) and set(value) == required, "ADMISSION_RECEIPT_SCHEMA")
    _require(value.get("schema") == "ep19-preconsumption-admission-v1" and value.get("result") == "PASS",
             "ADMISSION_RECEIPT_NOT_PASS")
    _require(value.get("formal_attempt") is False and value.get("formal_budget_consumed") is False and
             value.get("new_allowance_total") == 1 and value.get("new_allowance_used") == 0 and
             value.get("global_ordinal") == 3, "ADMISSION_RECEIPT_CONSUMPTION_REJECT")
    _require(value.get("run_id") == config["run_id"] == contract["attempt_authority"]["run_id"],
             "ADMISSION_RUN_ID_REJECT")
    _require(value.get("contract_id") == contract["contract_id"] and
             value.get("contract_sha256") == coherence.identity(contract) == config["eligibility_contract_sha256"],
             "ADMISSION_CONTRACT_BINDING_REJECT")
    _require(value.get("binding_sha256") == config["binding_sha256"] and
             value.get("review_sha256") == coherence.digest(review) and
             value.get("control_plane_evidence_sha256") == coherence.digest(control),
             "ADMISSION_VERSION_BINDING_REJECT")
    comparison = value.get("comparison")
    _require(isinstance(comparison, dict) and comparison.get("result") == "PASS" and
             comparison.get("phase") == "PRECONSUMPTION_ADMISSION" and
             comparison.get("capture_complete") is True and not comparison.get("differences"),
             "ADMISSION_COHERENCE_NOT_PASS")
    return value


def admit(*, config, binding, contract_path, review, control, run, output,
          allow_fixture=False, verify_preparation=None):
    """Validate all eligibility inputs and persist a PASS without consuming budget."""
    binding = Path(binding).absolute(); contract_path = Path(contract_path).absolute()
    review = Path(review).absolute(); control = Path(control).absolute()
    run = Path(run).absolute(); output = Path(output).absolute()
    _require(config.get("binding_sha256") == coherence.digest(binding), "ADMISSION_BINDING_CHANGED")
    contract = coherence.validate_contract(coherence.load(contract_path), allow_fixture=allow_fixture)
    _require(config.get("eligibility_contract") == str(contract_path) and
             config.get("eligibility_contract_sha256") == coherence.identity(contract),
             "ADMISSION_ELIGIBILITY_BINDING_REJECT")
    _require(config.get("run_id") == contract["attempt_authority"]["run_id"] == run.name,
             "ADMISSION_RUN_ID_REJECT")
    _require(not any((run / name).exists() for name in FORBIDDEN_BEFORE_CONSUME),
             "ADMISSION_AFTER_CONSUMPTION_FORBIDDEN")
    coherence.validate_review(review)
    coherence.validate_control_plane(contract, control, allow_fixture=allow_fixture)
    coherence.validate_version_chain(contract, config, review)
    preparation = (verify_preparation(contract, run) if verify_preparation is not None
                   else coherence.validate_preparation(contract, run))
    capture = coherence.capture_actual(contract, "PRECONSUMPTION_ADMISSION")
    private_path = output / "COHERENCE_CAPTURE.private.json"
    public_path = output / "COHERENCE_COMPARISON.json"
    public = coherence.evaluate_capture(contract, capture, private_path, public_path)
    _require(not any((run / name).exists() for name in FORBIDDEN_BEFORE_CONSUME),
             "ADMISSION_CONCURRENT_CONSUMPTION_REJECT")
    receipt = {
        "schema": "ep19-preconsumption-admission-v1", "result": "PASS",
        "formal_attempt": False, "formal_budget_consumed": False,
        "run_id": run.name, "contract_id": contract["contract_id"],
        "contract_sha256": coherence.identity(contract),
        "binding_sha256": config["binding_sha256"], "review_sha256": coherence.digest(review),
        "control_plane_evidence_sha256": coherence.digest(control),
        "preparation": preparation, "comparison": public,
        "new_allowance_total": 1, "new_allowance_used": 0, "global_ordinal": 3,
    }
    _write(output / "ADMISSION.json", receipt)
    return receipt
