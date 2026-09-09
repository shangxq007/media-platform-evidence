"""Pure Postiz v2.23.0 projection into unresolved external observations.

This module owns no transport and makes no HTTP claim. Provider identifiers remain
scoped external references and are never promoted into media-platform core IDs.
"""

from __future__ import annotations

import base64
import html
import ipaddress
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence
from urllib.parse import quote, quote_plus, unquote, urlsplit

CONTRACT = "external-publication-observation-v2"
PINNED_VERSION = "v2.23.0"
PINNED_SOURCE_COMMIT = "1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9"
PENDING = "PENDING_CORE_CONTRACT"
SCOPE_KEYS = frozenset({"principalId", "tenantId", "sessionId", "workspaceId", "projectId", "sourceId"})
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,179}$")
HEADER_VALUE = re.compile(r"^[\x21-\x7e]{16,4096}$")
INSTANT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z$")


class Failure(Exception):
    """A bounded, value-free failure safe for local classification."""

    def __init__(self, code: str, status: int = 422):
        self.code = code
        self.status = status
        super().__init__(code)


def identifier(value: Any) -> str:
    if type(value) is not str or not IDENTIFIER.fullmatch(value):
        raise Failure("INVALID_IDENTIFIER")
    return value


def _instant(value: Any) -> datetime:
    if type(value) is not str or not INSTANT.fullmatch(value):
        raise Failure("INVALID_TIME")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise Failure("INVALID_TIME") from None
    if parsed.tzinfo != timezone.utc:
        raise Failure("INVALID_TIME")
    return parsed


def _exact_bool(value: Any, code: str) -> bool:
    if type(value) is not bool:
        raise Failure(code)
    return value


def _exact_int(value: Any, code: str) -> int:
    if type(value) is not int:
        raise Failure(code)
    return value


def _safe_header_credential(value: Any) -> str:
    if type(value) is not str or not HEADER_VALUE.fullmatch(value):
        raise Failure("INVALID_CREDENTIAL_CONFIGURATION", 403)
    return value


def secret_variants(secret: str) -> frozenset[str]:
    """Representations rejected from output, including nested encoding/escaping."""

    raw = secret.encode("utf-8")
    variants = {
        secret,
        quote(secret, safe=""),
        quote_plus(secret, safe=""),
        json.dumps(secret, ensure_ascii=True)[1:-1],
        base64.b64encode(raw).decode("ascii"),
        base64.urlsafe_b64encode(raw).decode("ascii"),
        raw.hex(),
        "".join(f"\\u{byte:04x}" for byte in raw),
        "".join(f"\\u{byte:04X}" for byte in raw),
        "".join(f"\\x{byte:02x}" for byte in raw),
        "".join(f"&#{byte};" for byte in raw),
        "".join(f"&#x{byte:x};" for byte in raw),
    }
    variants.update(value.replace("\\", "\\\\") for value in tuple(variants))
    return frozenset(value for value in variants if value)


def _contains_secret(value: str, secrets: Sequence[str]) -> bool:
    candidates = {value, unquote(value), html.unescape(value)}
    for candidate in tuple(candidates):
        candidates.add(unquote(html.unescape(candidate)))
    return any(variant in candidate for secret in secrets for variant in secret_variants(secret) for candidate in candidates)


def safe_text(value: Any, secrets: Sequence[str], *, limit: int = 4000) -> str:
    if type(value) is not str or not value or len(value) > limit or _contains_secret(value, secrets):
        raise Failure("UNSAFE_UPSTREAM_TEXT")
    return value


def ensure_redacted(value: Mapping[str, Any], secrets: Sequence[str], max_bytes: int) -> None:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > max_bytes:
        raise Failure("RESPONSE_TOO_LARGE")
    # Inspect structural strings before serialization adds another escape layer.
    # This also rejects secrets used as object keys, not only projected values.
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, Mapping):
            pending.extend(item.keys())
            pending.extend(item.values())
        elif isinstance(item, (list, tuple)):
            pending.extend(item)
        elif isinstance(item, str) and _contains_secret(item, secrets):
            raise Failure("REDACTION_REJECTED")
    if _contains_secret(encoded, secrets):
        raise Failure("REDACTION_REJECTED")


@dataclass(frozen=True)
class Config:
    provider: str
    instance_id: str
    base: str
    approved_ip: str
    version: str
    binding: Mapping[str, Any]
    external_account_id: str
    start_inclusive: str
    end_exclusive: str
    organization_read_consent: bool
    synthetic: bool = False
    content_allowed: bool = False
    max_bytes: int = 1_048_576
    timeout_seconds: int = 5
    max_reads: int = 60
    max_records: int = 200

    @classmethod
    def from_mapping(cls, raw: Any) -> "Config":
        if type(raw) is not dict:
            raise Failure("INVALID_CONFIGURATION", 403)
        required = {
            "provider", "instance_id", "base", "approved_ip", "version", "binding",
            "external_account_id", "start_inclusive", "end_exclusive", "organization_read_consent",
        }
        optional = {"synthetic", "content_allowed", "max_bytes", "timeout_seconds", "max_reads", "max_records"}
        if not required.issubset(raw) or set(raw) - required - optional:
            raise Failure("INVALID_CONFIGURATION", 403)
        return cls(**raw).validate()

    def validate(self) -> "Config":
        if type(self.provider) is not str or self.provider != "postiz":
            raise Failure("INVALID_PROVIDER", 403)
        identifier(self.instance_id)
        identifier(self.external_account_id)
        if type(self.version) is not str or self.version != PINNED_VERSION:
            raise Failure("INVALID_VERSION", 403)
        _exact_bool(self.organization_read_consent, "INVALID_CONSENT")
        _exact_bool(self.synthetic, "INVALID_CONFIGURATION")
        _exact_bool(self.content_allowed, "INVALID_CONFIGURATION")
        if not self.organization_read_consent:
            raise Failure("NOT_AUTHORIZED", 403)
        if type(self.base) is not str or any(ord(char) < 33 or ord(char) == 127 for char in self.base):
            raise Failure("INVALID_DESTINATION", 403)
        try:
            parsed = urlsplit(self.base)
            port = parsed.port
        except ValueError:
            raise Failure("INVALID_DESTINATION", 403) from None
        if (
            parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment
            or parsed.path not in {"/public/v1", "/api/public/v1"}
            or not parsed.hostname or "%" in self.base or "\\" in self.base
        ):
            raise Failure("INVALID_DESTINATION", 403)
        try:
            parsed.hostname.encode("ascii")
            approved_ip = ipaddress.ip_address(self.approved_ip) if type(self.approved_ip) is str else None
        except (UnicodeEncodeError, ValueError):
            raise Failure("INVALID_DESTINATION", 403) from None
        if not re.fullmatch(r"[A-Za-z0-9.-]+|[0-9A-Fa-f:]+", parsed.hostname):
            raise Failure("INVALID_DESTINATION", 403)
        if approved_ip is None or port is not None and not 1 <= port <= 65535:
            raise Failure("INVALID_DESTINATION", 403)
        if self.synthetic:
            if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or str(approved_ip) != "127.0.0.1":
                raise Failure("INVALID_DESTINATION", 403)
        elif parsed.scheme != "https":
            raise Failure("INVALID_DESTINATION", 403)
        if type(self.binding) is not dict or set(self.binding) != {"scope", "ownerId"}:
            raise Failure("INVALID_BINDING", 403)
        scope = self.binding.get("scope")
        if type(scope) is not dict or set(scope) != SCOPE_KEYS:
            raise Failure("INVALID_BINDING", 403)
        identifier(self.binding.get("ownerId"))
        for key, value in scope.items():
            if key == "tenantId" and value is None:
                continue
            identifier(value)
        start, end = _instant(self.start_inclusive), _instant(self.end_exclusive)
        if not start < end or end - start > timedelta(days=31):
            raise Failure("INVALID_WINDOW")
        for value, low, high in (
            (_exact_int(self.max_bytes, "INVALID_LIMITS"), 1024, 1_048_576),
            (_exact_int(self.timeout_seconds, "INVALID_LIMITS"), 1, 10),
            (_exact_int(self.max_reads, "INVALID_LIMITS"), 1, 60),
            (_exact_int(self.max_records, "INVALID_LIMITS"), 1, 200),
        ):
            if not low <= value <= high:
                raise Failure("INVALID_LIMITS")
        return self

    @property
    def upstream_end_inclusive(self) -> str:
        end = _instant(self.end_exclusive) - timedelta(milliseconds=1)
        return end.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @property
    def endpoint(self) -> tuple[str, str, int, str]:
        parsed = urlsplit(self.base)
        return parsed.scheme, parsed.hostname or "", parsed.port or (443 if parsed.scheme == "https" else 80), parsed.path


class PostizProjector:
    """Projects supplied JSON values without creating platform-owned entities."""

    def __init__(self, config: Config, local_token: Any, upstream_key: Any):
        self.config = config.validate()
        self.local_token = _safe_header_credential(local_token)
        self.upstream_key = _safe_header_credential(upstream_key)
        if self.local_token == self.upstream_key:
            raise Failure("INVALID_CREDENTIAL_CONFIGURATION", 403)
        self._secrets = (self.local_token, self.upstream_key)

    def _external_refs(self, post_id: str) -> dict[str, str]:
        return {
            "provider": self.config.provider,
            "instance": self.config.instance_id,
            "account": self.config.external_account_id,
            "post": post_id,
        }

    @staticmethod
    def _display_status(raw_status: Any) -> tuple[str, bool]:
        mapping = {"QUEUE": "scheduled", "DRAFT": "draft", "PUBLISHED": "published"}
        if type(raw_status) is not str:
            return "unknown", True
        return mapping.get(raw_status, "unknown"), raw_status not in mapping

    def project(self, integrations: Any, posts_response: Any, request_id: Any, observed_at: Any) -> dict[str, Any]:
        request_id = identifier(request_id)
        observed_at_value = _instant(observed_at).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        if type(integrations) is not list or type(posts_response) is not dict or type(posts_response.get("posts")) is not list:
            raise Failure("INVALID_UPSTREAM_CONTRACT")
        matches = [row for row in integrations if type(row) is dict and row.get("id") == self.config.external_account_id]
        if len(matches) != 1 or matches[0].get("disabled") is not False:
            raise Failure("EXTERNAL_ACCOUNT_UNAVAILABLE", 403)
        account = matches[0]
        account_projection = {
            "externalReferences": {
                "provider": self.config.provider,
                "instance": self.config.instance_id,
                "account": self.config.external_account_id,
            },
            "label": safe_text(account.get("name"), self._secrets, limit=240),
            "providerLabel": safe_text(account.get("identifier"), self._secrets, limit=120),
            "coreBinding": {"status": PENDING},
        }
        start, end = _instant(self.config.start_inclusive), _instant(self.config.end_exclusive)
        observations: list[dict[str, Any]] = []
        seen: set[str] = set()
        omissions = {"recurrence": 0, "outsideWindow": 0, "recordCap": 0}
        for raw in posts_response["posts"]:
            if type(raw) is not dict or type(raw.get("integration")) is not dict:
                raise Failure("INVALID_UPSTREAM_CONTRACT")
            identifier(raw["integration"].get("id"))
            if raw["integration"].get("id") != self.config.external_account_id:
                continue
            post_id = identifier(raw.get("id"))
            if post_id in seen:
                raise Failure("DUPLICATE_EXTERNAL_POST_ID")
            seen.add(post_id)
            if raw.get("intervalInDays") is not None or raw.get("actualDate") is not None:
                omissions["recurrence"] += 1
                continue
            supplied_time = _instant(raw.get("publishDate"))
            if not start <= supplied_time < end:
                omissions["outsideWindow"] += 1
                continue
            display_status, unmapped = self._display_status(raw.get("state"))
            observation: dict[str, Any] = {
                "kind": "external-publication-observation",
                "externalReferences": self._external_refs(post_id),
                "coreBinding": {"status": PENDING},
                "displayStatus": display_status,
                "statusMapping": "unmapped" if unmapped else "bounded-display-only",
                "timeField": "scheduledAt" if raw.get("state") == "QUEUE" else "unscheduled" if raw.get("state") == "DRAFT" else "unknown",
                "relationships": {
                    "project": {"status": PENDING},
                    "artifacts": {"status": PENDING},
                    "attempts": {"status": PENDING},
                    "externalOutcomes": {"status": PENDING},
                },
            }
            if raw.get("state") == "QUEUE":
                observation["scheduledAt"] = supplied_time.isoformat(timespec="milliseconds").replace("+00:00", "Z")
            if self.config.content_allowed:
                observation["summary"] = safe_text(raw.get("content"), self._secrets)
            observations.append(observation)
        observations.sort(key=lambda row: tuple(row["externalReferences"][key] for key in ("provider", "instance", "account", "post")))
        omissions["recordCap"] = max(0, len(observations) - self.config.max_records)
        result = {
            "contract": CONTRACT,
            "status": "ok",
            "requestId": request_id,
            "binding": self.config.binding,
            "access": {
                "authority": "owner-local-single-user",
                "scope": "narrower-than-platform-effective-access",
                "list": True,
                "content": self.config.content_allowed,
            },
            "providerVersion": PINNED_VERSION,
            "providerSourceCommit": PINNED_SOURCE_COMMIT,
            "evidence": "pure-synthetic-projection" if self.config.synthetic else "supplied-read-values",
            "window": {
                "semantics": "half-open",
                "startInclusive": self.config.start_inclusive,
                "endExclusive": self.config.end_exclusive,
                "upstreamEndInclusive": self.config.upstream_end_inclusive,
            },
            "observedAt": observed_at_value,
            "completeness": "partial" if any(omissions.values()) else "bounded",
            "omissions": omissions,
            "externalAccount": account_projection,
            "observations": observations[: self.config.max_records],
        }
        ensure_redacted(result, self._secrets, self.config.max_bytes)
        return result


__all__ = [
    "CONTRACT", "PINNED_VERSION", "PINNED_SOURCE_COMMIT", "PENDING", "Config", "Failure",
    "PostizProjector", "ensure_redacted", "identifier", "safe_text", "secret_variants",
]
