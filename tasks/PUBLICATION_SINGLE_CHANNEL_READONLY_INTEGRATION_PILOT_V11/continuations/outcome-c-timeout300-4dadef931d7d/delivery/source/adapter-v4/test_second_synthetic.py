import unittest

from model import PENDING
from second_synthetic import map_delivery_jobs


class SecondSyntheticMappingTests(unittest.TestCase):
    def test_distinct_layout_stays_unresolved_and_scopes_colliding_external_refs(self):
        payload = {"deliveryJobs": [{"externalNumber": 7, "phase": "waiting"}], "receiptEvents": {"7": {"kind": "accepted-only"}}}
        left = map_delivery_jobs(payload, "synthetic-a", "instance-a", "account-a")[0]
        right = map_delivery_jobs(payload, "synthetic-b", "instance-b", "account-b")[0]
        self.assertEqual(left["externalReferences"]["post"], right["externalReferences"]["post"])
        self.assertNotEqual(left["externalReferences"], right["externalReferences"])
        self.assertEqual(left["coreBinding"], {"status": PENDING})
        self.assertEqual(left["diagnostics"], {"receiptEventPresence": "supplied-unbound"})
        self.assertFalse({"id", "projectId", "accountId", "planId", "attemptId", "resultId"} & set(left))

    def test_unrecognized_phase_is_unknown_not_a_failure_or_result(self):
        row = map_delivery_jobs({"deliveryJobs": [{"externalNumber": 9, "phase": "novel"}], "receiptEvents": {}}, "synthetic-a", "instance-a", "account-a")[0]
        self.assertEqual(row["displayStatus"], "unknown")
        self.assertEqual(row["statusMapping"], "unmapped")
        self.assertEqual(row["timeField"], "unknown")


if __name__ == "__main__":
    unittest.main()
