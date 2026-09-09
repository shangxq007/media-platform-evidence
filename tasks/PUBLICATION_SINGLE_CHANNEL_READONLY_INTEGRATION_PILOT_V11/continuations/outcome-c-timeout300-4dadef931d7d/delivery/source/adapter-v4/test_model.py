import copy
import base64
import json
import unittest
from dataclasses import replace
from urllib.parse import quote

from model import Config, Failure, PENDING, PostizProjector, ensure_redacted
from wire import build_request, parse_response


SCOPE = {"principalId": "owner", "tenantId": None, "sessionId": "session", "workspaceId": "w", "projectId": "p", "sourceId": "external-observation"}
BINDING = {"scope": SCOPE, "ownerId": "host1"}
START = "2026-09-01T00:00:00Z"
END = "2026-10-01T00:00:00Z"
LOCAL = "synthetic-local-token-123"
UPSTREAM = "synthetic-upstream-key-456"


def raw_config(**changes):
    # Pure URL fixture only; transport tests always replace this with the OS-assigned upstream port.
    value = {
        "provider": "postiz", "instance_id": "postiz-v11-synthetic", "base": "http://127.0.0.1:49152/public/v1",
        "approved_ip": "127.0.0.1", "version": "v2.23.0", "binding": copy.deepcopy(BINDING),
        "external_account_id": "account1", "start_inclusive": START, "end_exclusive": END,
        "organization_read_consent": True, "synthetic": True, "content_allowed": False,
    }
    value.update(changes)
    return value


def post(**changes):
    value = {"id": "post1", "content": "Synthetic copy", "integration": {"id": "account1"}, "state": "QUEUE", "publishDate": "2026-09-09T12:00:00Z", "intervalInDays": None}
    value.update(changes)
    return value


class ConfigurationAndRequestTests(unittest.TestCase):
    def test_configuration_is_exactly_typed_and_fail_closed(self):
        for changes in (
            {"synthetic": 1}, {"max_records": True}, {"timeout_seconds": 1.5},
            {"organization_read_consent": "yes"}, {"unknown": "field"}, {"binding": []},
        ):
            with self.subTest(changes=changes), self.assertRaises(Failure):
                Config.from_mapping(raw_config(**changes))

    def test_destination_and_header_injection_are_rejected(self):
        unsafe = (
            "http://127.0.0.1:49152/public/v1%0d%0aX-Evil:yes",
            "http://user:pass@127.0.0.1:49152/public/v1",
            "http://127.0.0.1:49152/public/v1?next=https://evil.invalid",
            "https://127.0.0.1:49152/public/v1",
            "http://127.0.0.1:49152/other",
        )
        for base in unsafe:
            with self.subTest(base=base), self.assertRaises(Failure):
                Config.from_mapping(raw_config(base=base))
        config = Config.from_mapping(raw_config())
        for secret in ("short", "valid-token-12345\r\nX-Evil: yes", "valid token with spaces"):
            with self.subTest(secret=secret), self.assertRaises(Failure):
                build_request(config, "integrations", secret)

    def test_fixed_requests_use_raw_authorization_and_half_open_translation(self):
        config = Config.from_mapping(raw_config())
        request = build_request(config, "posts", UPSTREAM).decode("ascii")
        self.assertIn("GET /public/v1/posts?", request)
        self.assertIn("startDate=2026-09-01T00%3A00%3A00Z", request)
        self.assertIn("endDate=2026-09-30T23%3A59%3A59.999Z", request)
        self.assertIn(f"Authorization: {UPSTREAM}\r\n", request)
        self.assertNotIn("Bearer", request)
        self.assertNotIn("limit=", request)
        with self.assertRaises(Failure):
            build_request(config, "caller-url", UPSTREAM)

    def test_response_parser_never_includes_upstream_body_in_failure(self):
        sentinel = b"PRIVATE_ERROR synthetic-upstream-key-456"
        with self.assertRaises(Failure) as caught:
            parse_response(500, {"content-type": "text/plain"}, sentinel, 1024)
        self.assertEqual(str(caught.exception), "UPSTREAM_FAILURE")
        self.assertNotIn("PRIVATE", str(caught.exception))


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.config = Config.from_mapping(raw_config())
        self.projector = PostizProjector(self.config, LOCAL, UPSTREAM)
        self.accounts = [{"id": "account1", "name": "Synthetic channel", "identifier": "synthetic", "disabled": False}]

    def project(self, posts):
        return self.projector.project(self.accounts, {"posts": posts}, "request1", "2026-09-09T13:00:00Z")

    def test_scoped_external_references_remain_unbound_without_synthetic_graph(self):
        result = self.project([post(releaseId="supplied-release")])
        observation = result["observations"][0]
        self.assertEqual(observation["externalReferences"], {"provider": "postiz", "instance": "postiz-v11-synthetic", "account": "account1", "post": "post1"})
        self.assertEqual(observation["coreBinding"], {"status": PENDING})
        self.assertTrue(all(value == {"status": PENDING} for value in observation["relationships"].values()))
        self.assertFalse({"id", "projectId", "accountId", "planId", "attemptId", "publishedAt", "actualDate", "releaseId"} & set(observation))
        self.assertEqual(result["access"]["scope"], "narrower-than-platform-effective-access")
        self.assertEqual(result["window"]["semantics"], "half-open")
        self.assertEqual(result["completeness"], "bounded")
        self.assertEqual(result["evidence"], "pure-synthetic-projection")

    def test_unknown_and_error_provider_states_are_safe_observations(self):
        result = self.project([post(id="one", state="FUTURE_STATE"), post(id="two", state="ERROR")])
        self.assertEqual([row["displayStatus"] for row in result["observations"]], ["unknown", "unknown"])
        self.assertEqual([row["statusMapping"] for row in result["observations"]], ["unmapped", "unmapped"])
        self.assertTrue(all("failure" not in json.dumps(row).lower() for row in result["observations"]))

    def test_end_is_exclusive_and_omissions_make_partial_without_query_failure(self):
        result = self.project([
            post(id="inside", publishDate="2026-09-30T23:59:59.999Z"),
            post(id="end", publishDate=END),
            post(id="recurring", intervalInDays=1),
        ])
        self.assertEqual([row["externalReferences"]["post"] for row in result["observations"]], ["inside"])
        self.assertEqual(result["omissions"], {"recurrence": 1, "outsideWindow": 1, "recordCap": 0})
        self.assertEqual(result["completeness"], "partial")

    def test_no_actual_time_attempt_result_or_known_empty_relation_is_invented(self):
        result = self.project([post(state="PUBLISHED")])
        observation = result["observations"][0]
        self.assertEqual(observation["displayStatus"], "published")
        self.assertEqual(observation["timeField"], "unknown")
        encoded = json.dumps(observation)
        for forbidden in ("publishedAt", "attempts\": []", "externalOutcomes\": []", "artifacts\": []"):
            self.assertNotIn(forbidden, encoded)

    def test_raw_encoded_and_escaped_credentials_are_rejected_from_output(self):
        encodings = (
            LOCAL,
            quote(LOCAL, safe=""),
            base64.b64encode(LOCAL.encode()).decode(),
            LOCAL.encode().hex(),
            "".join(f"\\u{ord(char):04x}" for char in LOCAL),
        )
        for leaked in encodings:
            with self.subTest(leaked=leaked), self.assertRaises(Failure) as caught:
                ensure_redacted({"value": leaked}, (LOCAL, UPSTREAM), 1_048_576)
            self.assertEqual(caught.exception.code, "REDACTION_REJECTED")

    def test_content_projection_rejects_encoded_secret_and_duplicate_post_refs(self):
        content_config = Config.from_mapping(raw_config(content_allowed=True))
        projector = PostizProjector(content_config, LOCAL, UPSTREAM)
        with self.assertRaises(Failure):
            projector.project(self.accounts, {"posts": [post(content=base64.b64encode(UPSTREAM.encode()).decode())]}, "request1", "2026-09-09T13:00:00Z")
        with self.assertRaises(Failure) as caught:
            self.project([post(), post()])
        self.assertEqual(caught.exception.code, "DUPLICATE_EXTERNAL_POST_ID")


if __name__ == "__main__":
    unittest.main()
