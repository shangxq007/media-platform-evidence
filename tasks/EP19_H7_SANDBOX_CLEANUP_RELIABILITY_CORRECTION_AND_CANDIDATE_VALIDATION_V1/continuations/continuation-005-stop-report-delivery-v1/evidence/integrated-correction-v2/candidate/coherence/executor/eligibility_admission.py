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
        "schema", "result", "formal_attempt", "formal_budget_consumed", "run_id", "candidate", "tree",
        "contract_id", "contract_sha256", "binding_sha256", "review_sha256",
        "control_plane_evidence_sha256", "preparation", "comparison",
        "new_allowance_total", "new_allowance_used", "global_ordinal",
        "capture_private", "capture_private_sha256", "comparison_private", "comparison_private_sha256",
        "comparison_public", "comparison_public_sha256",
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
    private_path = Path(value.get("capture_private", ""))
    comparison_private_path = Path(value.get("comparison_private", ""))
    public_path = Path(value.get("comparison_public", ""))
    _require(private_path.is_file() and comparison_private_path.is_file() and public_path.is_file() and
             coherence.digest(private_path) == value.get("capture_private_sha256") and
             coherence.digest(comparison_private_path) == value.get("comparison_private_sha256") and
             coherence.digest(public_path) == value.get("comparison_public_sha256"),
             "ADMISSION_CAPTURE_BYTES_CHANGED")
    capture = coherence.load(private_path)
    recomputed = coherence.compare(contract, capture)
    _require(recomputed.get("result") == "PASS" and
             recomputed == coherence.load(comparison_private_path) and
             coherence.public_projection(recomputed) == coherence.load(public_path) == comparison,
             "ADMISSION_COMPARISON_RECOMPUTATION_REJECT")
    return value


def admit(*, config, binding, contract_path, review, control, run, output,
          allow_fixture=False, verify_preparation=None):
    """Validate all eligibility inputs and persist a PASS without consuming budget."""
    binding = Path(binding).absolute(); contract_path = Path(contract_path).absolute()
    review = Path(review).absolute(); control = Path(control).absolute()
    run = Path(run).absolute(); output = Path(output).absolute()
    if not allow_fixture:
        resolved_run = run.resolve(); resolved_output = output.resolve(strict=False)
        _require(resolved_output.is_relative_to(resolved_run) and resolved_output != resolved_run,
                 "ADMISSION_OUTPUT_OUTSIDE_TASK_PRIVATE_RUN")
    _require(config.get("binding_sha256") == coherence.digest(binding), "ADMISSION_BINDING_CHANGED")
    contract = coherence.validate_contract(coherence.load(contract_path), allow_fixture=allow_fixture)
    _require(config.get("eligibility_contract") == str(contract_path) and
             config.get("eligibility_contract_sha256") == coherence.identity(contract),
             "ADMISSION_ELIGIBILITY_BINDING_REJECT")
    _require(config.get("run_id") == contract["attempt_authority"]["run_id"] == run.name,
             "ADMISSION_RUN_ID_REJECT")
    _require(not any((run / name).exists() for name in FORBIDDEN_BEFORE_CONSUME),
             "ADMISSION_AFTER_CONSUMPTION_FORBIDDEN")
    coherence.validate_review(review, allow_fixture=allow_fixture)
    coherence.validate_control_plane(contract, control, allow_fixture=allow_fixture)
    coherence.validate_version_chain(contract, config, review)
    preparation = (verify_preparation(contract, run) if verify_preparation is not None
                   else coherence.validate_preparation(contract, run))
    capture = coherence.capture_actual(contract, "PRECONSUMPTION_ADMISSION")
    private_path = output / "COHERENCE_CAPTURE.private.json"
    try:
        _write(private_path, capture, 0o600)
    except Exception:
        # The comparison persistence below retains the primary coherence result
        # and both diagnostic sink failures. A PASS can never proceed without
        # the raw capture because the post-evaluation check is fail closed.
        pass
    comparison_private_path = output / "COHERENCE_COMPARISON.private.json"
    public_path = output / "COHERENCE_COMPARISON.json"
    public = coherence.evaluate_capture(contract, capture, comparison_private_path, public_path)
    _require(private_path.is_file() and coherence.load(private_path) == capture,
             "ADMISSION_RAW_CAPTURE_PERSISTENCE_REJECT")
    _require(not any((run / name).exists() for name in FORBIDDEN_BEFORE_CONSUME),
             "ADMISSION_CONCURRENT_CONSUMPTION_REJECT")
    receipt = {
        "schema": "ep19-preconsumption-admission-v1", "result": "PASS",
        "formal_attempt": False, "formal_budget_consumed": False,
        "run_id": run.name, "candidate": contract["candidate_identity"]["candidate"],
        "tree": contract["candidate_identity"]["tree"], "contract_id": contract["contract_id"],
        "contract_sha256": coherence.identity(contract),
        "binding_sha256": config["binding_sha256"], "review_sha256": coherence.digest(review),
        "control_plane_evidence_sha256": coherence.digest(control),
        "preparation": preparation, "comparison": public,
        "capture_private": str(private_path), "capture_private_sha256": coherence.digest(private_path),
        "comparison_private": str(comparison_private_path), "comparison_private_sha256": coherence.digest(comparison_private_path),
        "comparison_public": str(public_path), "comparison_public_sha256": coherence.digest(public_path),
        "new_allowance_total": 1, "new_allowance_used": 0, "global_ordinal": 3,
    }
    _write(output / "ADMISSION.json", receipt)
    return receipt
