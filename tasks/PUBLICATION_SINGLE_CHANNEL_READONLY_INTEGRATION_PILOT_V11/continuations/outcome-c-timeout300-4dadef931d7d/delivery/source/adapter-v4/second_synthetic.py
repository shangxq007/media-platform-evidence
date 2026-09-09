"""A deliberately non-Postiz-shaped pure mapper for replaceability evidence only."""

from __future__ import annotations

from typing import Any

from model import PENDING, Failure, identifier


def map_delivery_jobs(payload: Any, provider: Any, instance: Any, account: Any) -> list[dict[str, Any]]:
    """Map numeric job references without creating plans, attempts, or results."""

    provider_id, instance_id, account_id = identifier(provider), identifier(instance), identifier(account)
    if type(payload) is not dict or set(payload) != {"deliveryJobs", "receiptEvents"}:
        raise Failure("INVALID_SECOND_ADAPTER_CONTRACT")
    jobs, events = payload["deliveryJobs"], payload["receiptEvents"]
    if type(jobs) is not list or type(events) is not dict:
        raise Failure("INVALID_SECOND_ADAPTER_CONTRACT")
    observations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for job in jobs:
        if type(job) is not dict or set(job) != {"externalNumber", "phase"} or type(job["externalNumber"]) is not int or type(job["phase"]) is not str:
            raise Failure("INVALID_SECOND_ADAPTER_CONTRACT")
        post_ref = str(job["externalNumber"])
        identifier(post_ref)
        if post_ref in seen:
            raise Failure("DUPLICATE_EXTERNAL_POST_ID")
        seen.add(post_ref)
        # Receipt events are diagnostic presence only. They are not promoted into a
        # platform attempt/result without an approved binding and event contract.
        has_event = post_ref in events
        observations.append({
            "kind": "external-publication-observation",
            "externalReferences": {"provider": provider_id, "instance": instance_id, "account": account_id, "post": post_ref},
            "coreBinding": {"status": PENDING},
            "displayStatus": "scheduled" if job["phase"] == "waiting" else "unknown",
            "statusMapping": "bounded-display-only" if job["phase"] == "waiting" else "unmapped",
            "timeField": "unknown",
            "relationships": {
                "project": {"status": PENDING},
                "artifacts": {"status": PENDING},
                "attempts": {"status": PENDING},
                "externalOutcomes": {"status": PENDING},
            },
            "diagnostics": {"receiptEventPresence": "supplied-unbound" if has_event else "not-supplied"},
        })
    return observations


__all__ = ["map_delivery_jobs"]
