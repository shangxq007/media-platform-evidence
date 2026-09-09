"""Identity accounting required before an external29 qualification is accepted."""
from collections import Counter

REQUIRED_AFFECTED_CONTROLS = frozenset({
    "test_r12_actual_prepare.R12ActualPrepareConsumerControls.test_actual_cli_prepare_identity_contract_and_negative_matrix",
    "test_r11_diagnostic_emission.R11ActualDiagnosticEmissionControls.test_actual_acquisition_and_marker_then_stderr_write_failure_saved",
    "test_r11_diagnostic_emission.R11ActualDiagnosticEmissionControls.test_actual_native_gate_and_marker_then_stderr_flush_failure_saved",
    "test_r10_final_boundary.R10ActualFinalBoundaryControls.test_actual_final_failure_writer_fault_keeps_original_in_saved_formal_receipt",
    "test_r10_final_boundary.R10ActualFinalBoundaryControls.test_production_main_saved_stderr_has_structured_original_and_both_sink_failures",
    "test_r10_final_boundary.R10ActualFinalBoundaryControls.test_unavailable_stderr_returns_false_without_persistence_claim",
    "test_r9_preflight_persistence.R9ActualPreflightPersistenceControls.test_actual_preflight_write_failure_is_secondary_to_original_disposition",
    "test_r9_preflight_persistence.R9ActualPreflightPersistenceControls.test_final_failure_sink_fault_retains_available_original_and_secondaries",
    "test_r9_preflight_persistence.R9ActualPreflightPersistenceControls.test_original_preflight_failure_alone_has_real_saved_final_readback",
    "test_r8_transport.R8ActualTransportControls.test_actual_engine_reject_and_marker_fault_keep_decision_in_saved_driver_failure",
    "test_r8_transport.R8ActualTransportControls.test_nested_actual_durability_failure_keeps_occurrences_and_context_topology",
    "test_r8_transport.R8ActualTransportControls.test_actual_preflight_wiring_propagates_native_and_evidence_causes_to_formal_failure",
    "test_conformance_corrections.Group1ContinuousAndTemp.test_external_file_moved_into_usage_is_rejected_by_real_observer",
    "test_conformance_corrections.Group1ContinuousAndTemp.test_bad_mode_short_lived_temp_is_rejected_by_real_observer",
    "test_conformance_corrections.Group1ContinuousAndTemp.test_temp_moved_outside_without_usage_target_is_rejected",
    "test_conformance_corrections.Group1ContinuousAndTemp.test_outer_fixture_exercises_continuous_ancestor_rejection",
    "test_conformance_corrections.Group2TimeAndFraming.test_future_ledger_timestamp_rejected_against_actual_capture_end",
    "test_conformance_corrections.Group2TimeAndFraming.test_crlf_ledger_record_rejected_as_raw_framing",
    "test_conformance_corrections.Group2TimeAndFraming.test_escaped_cr_is_distinct_from_raw_cr",
    "test_conformance_corrections.Group2TimeAndFraming.test_boundary_receipt_binds_actual_wall_and_monotonic_window",
    "test_conformance_corrections.Group2TimeAndFraming.test_wall_clock_rollback_from_previous_accepted_boundary_rejects",
    "test_conformance_corrections.Group3IdentityAndProvenance.test_mandatory_affected_controls_are_fixed_independently",
    "test_conformance_corrections.Group3IdentityAndProvenance.test_missing_duplicate_unexpected_and_skip_are_all_rejected",
    "test_conformance_corrections.Group3IdentityAndProvenance.test_dependency_source_closure_and_private_hashes_are_mandatory",
    "test_conformance_corrections.Group3IdentityAndProvenance.test_private_eligibility_must_hash_bind_to_reviewed_applicability",
    "test_conformance_corrections.Group3IdentityAndProvenance.test_second_formal_run_id_is_exact_not_a_family",
    "test_conformance_corrections.Group4LatchDurabilityAndBounds.test_evidence_failure_does_not_commit_engine_state",
    "test_conformance_corrections.Group4LatchDurabilityAndBounds.test_failure_marker_fsyncs_file_and_parent_directory",
    "test_conformance_corrections.Group4LatchDurabilityAndBounds.test_adapter_latches_after_actual_evidence_path_failure",
    "test_conformance_corrections.Group4LatchDurabilityAndBounds.test_event_flood_is_bounded_during_real_drain",
    "test_conformance_corrections.Group4LatchDurabilityAndBounds.test_slow_regular_file_read_is_interrupted_inside_loop",
    "test_conformance_corrections.Group4LatchDurabilityAndBounds.test_outer_fixture_failure_latch_blocks_success_final",
    "test_approved_contract.PositiveControls.test_multiple_and_previous_prefix_ledger_appends_pass",
    "test_external29_integration.External29IntegrationControls.test_fixture_never_marks_formal_or_product_execution",
    "test_conformance_corrections.PreformalActualRed.test_ar001_final_receipt_contains_write_during_seal_capture",
    "test_conformance_corrections.PreformalActualRed.test_ar002_formal_seed_accepts_visible_legal_temp_without_keyerror",
    "test_conformance_corrections.PreformalActualRed.test_ar007_unknown_actual_status_cannot_pass_identity_accounting",
    "test_conformance_corrections.PreformalActualRed.test_ar007_candidate_consumer_claim_is_checked_against_real_bytes",
    "test_conformance_corrections.PreformalActualRed.test_ar007_instruction_selection_origin_hash_is_verified",
    "test_conformance_corrections.PreformalActualRed.test_ar008_transient_live_state_parse_failure_irreversibly_latches",
    "test_conformance_corrections.PreformalActualRed.test_ar008_consume_write_failure_cannot_be_resurrected",
    "test_conformance_corrections.PreformalActualRed.test_ar008_outer_observer_failure_latches_same_adapter",
    "test_conformance_corrections.PreformalActualRed.test_ar009_strict_decision_creation_fsyncs_publishing_runtime_directory",
    "test_conformance_corrections.PreformalActualRed.test_ar010_blocking_initial_fstat_is_interrupted_and_cleaned_up",
    "test_conformance_corrections.PreformalActualRed.test_ar010_temp_metadata_stat_is_bounded_inside_real_drain",
    "test_conformance_corrections.PostfixIntegratedControls.test_final_combined_seal_rejects_memory_write_and_closes_observation",
    "test_conformance_corrections.PostfixIntegratedControls.test_seed_observer_rebind_accepts_legal_visible_temp_rename",
    "test_conformance_corrections.PostfixIntegratedControls.test_current_dependency_evidence_validates_real_r2_sources",
    "test_conformance_corrections.PostfixIntegratedControls.test_duplicate_expected_identity_is_explicitly_rejected",
    "test_conformance_corrections.PostfixIntegratedControls.test_postread_path_stat_is_deadline_guarded",
    "test_conformance_corrections.PostfixIntegratedControls.test_real_sustained_growth_is_bounded",
    "test_conformance_corrections.PostfixIntegratedControls.test_directory_over_capacity_rejects",
    "test_conformance_corrections.PostfixIntegratedControls.test_strict_acquisition_failure_latches_actual_adapter",
    "test_r3_remaining.RemainingProductionPathControls.test_ar001_event_queued_during_last_identity_check_is_rejected_before_endpoint",
    "test_r3_remaining.RemainingProductionPathControls.test_ar002_actual_observer_seed_rebind_accepts_legal_temp_rename",
    "test_r3_remaining.RemainingProductionPathControls.test_ar007_r2_declarative_graph_is_rejected_for_missing_actual_vite_edge",
    "test_r3_remaining.RemainingProductionPathControls.test_ar007_loader_rejects_extra_qualification_flag_with_other_bindings_valid",
    "test_r3_remaining.RemainingProductionPathControls.test_ar008_actual_run_gate_caught_failure_latches_before_post_command_boundary",
    "test_r3_remaining.RemainingProductionPathControls.test_ar009_actual_gate_and_sealed_copy_publish_parent_chain_durably",
    "test_r3_remaining.RemainingProductionPathControls.test_ar010_actual_native_final_stat_is_guarded_and_resources_close",
    "test_r3_remaining.RemainingProductionPathControls.test_ar010_boundary_observer_inventory_failure_closes_constructor_fd",
    "test_r4_remaining.R4ProductionPathControls.test_ar007_current_finite_vite_parser_graph_is_complete_and_missing_edges_reject",
    "test_r4_remaining.R4ProductionPathControls.test_ar008_actual_outer_termination_retains_independent_protection_timeout_and_exit_causes",
    "test_r4_remaining.R4ProductionPathControls.test_ar009_actual_vite_failure_log_uses_durable_stream",
    "test_r4_remaining.R4ProductionPathControls.test_ar009_cleanup_preimage_is_durable_before_unlink_and_failed_gate_is_sealed",
    "test_r4_remaining.R4ProductionPathControls.test_ar010_strict_baseline_failed_handoff_closes_watch_and_preserves_cleanup_failure",
    "test_r5_remaining.R5FailureTransitionControls.test_driver_marker_failure_preserves_gate_primary_and_secondary",
    "test_r5_remaining.R5FailureTransitionControls.test_final_receipt_failure_reaches_driver_with_prior_native_and_parser_facts",
    "test_r5_remaining.R5FailureTransitionControls.test_formal_cleanup_attempts_observer_after_continuous_close_failure",
    "test_r5_remaining.R5FailureTransitionControls.test_formal_cleanup_retains_original_and_cleanup_causes",
    "test_r5_remaining.R5FailureTransitionControls.test_native_observer_exception_retains_executed_child_and_compound_causes",
    "test_r5_remaining.R5FailureTransitionControls.test_postseal_failure_uses_bound_immutable_supplement",
    "test_r5_remaining.R5FailureTransitionControls.test_runner_parser_evidence_exception_is_not_product_failure",
    "test_r5_remaining.R5FailureTransitionControls.test_runner_product_assertion_remains_separate",
    "test_r5_remaining.R5FailureTransitionControls.test_supplement_persistence_failure_stays_secondary_and_never_success",
    "test_r5_remaining.R5FailureTransitionControls.test_vite_helper_nonzero_is_process_not_product_failure",
    "test_r5_remaining.R5FailureTransitionControls.test_vite_launch_failure_is_environment_not_product",
    "test_r5_remaining.R5FailureTransitionControls.test_vite_log_fsync_failure_is_evidence_not_product",
    "test_r5_remaining.R5FailureTransitionControls.test_watch_constructor_cleanup_failure_preserves_original_cause",
    "test_r6_remaining.R6ExceptionCompositionControls.test_attached_receipt_plus_marker_failure_reaches_final_gate_result",
    "test_r6_remaining.R6ExceptionCompositionControls.test_boundary_observer_constructor_retains_primary_and_close_failure",
    "test_r6_remaining.R6ExceptionCompositionControls.test_capture_file_body_and_fd_close_failure_are_both_reported",
    "test_r6_remaining.R6ExceptionCompositionControls.test_durable_stream_attempts_flush_stream_fd_and_parent_cleanup_independently",
    "test_r6_remaining.R6ExceptionCompositionControls.test_durable_stream_fdopen_failure_releases_owned_raw_fd_and_syncs_parent",
    "test_r6_remaining.R6ExceptionCompositionControls.test_exception_after_exited_parent_terminates_actual_owned_descendant",
    "test_r6_remaining.R6ExceptionCompositionControls.test_owned_descendant_unknown_permission_and_timeout_are_distinct",
    "test_r6_remaining.R6ExceptionCompositionControls.test_parent_fd_attempts_every_ancestor_close_and_keeps_body_failure",
    "test_r6_remaining.R6ExceptionCompositionControls.test_vite_helper_primary_and_real_stream_fsync_failure_both_survive",
    "test_r7_remaining.R7ReviewerFindingControls.test_actual_adapter_composed_marker_failure_reaches_driver_final_diagnostic",
    "test_r7_remaining.R7ReviewerFindingControls.test_capture_preservation_boundary_adapter_driver_saved_receipt_keeps_leaf_causes",
    "test_r7_remaining.R7ReviewerFindingControls.test_keyboard_interrupt_after_actual_fd_acquisition_releases_and_retains_both_causes",
    "test_r7_remaining.R7ReviewerFindingControls.test_known_owned_descendants_are_isolated_when_one_identity_query_fails",
    "test_r7_remaining.R7ReviewerFindingControls.test_memory_error_after_actual_fd_acquisition_releases_and_retains_both_causes",
    "test_r7_runner_supplement.R7RunnerSupplementControl.test_real_runner_supplement_keeps_every_composed_persistence_leaf",
})


def identity_accounting(expected, rows):
    if not isinstance(expected, list) or any(not isinstance(item, str) or not item for item in expected):
        raise RuntimeError("QUALIFICATION_EXPECTED_IDENTITIES_INVALID")
    expected_counts = Counter(expected)
    expected_duplicates = sorted(item for item, count in expected_counts.items() if count > 1)
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    counts = Counter(ids)
    expected_set = set(expected)
    actual_set = {item for item in ids if isinstance(item, str)}
    duplicates = sorted(item for item, count in counts.items() if isinstance(item, str) and count > 1)
    statuses = {name: sorted(row["id"] for row in rows if row.get("actual") == name)
                for name in ("PASS", "FAIL", "ERROR", "SKIP")}
    invalid_rows = [index for index, row in enumerate(rows)
                    if not isinstance(row, dict) or not isinstance(row.get("id"), str) or
                    row.get("actual") not in statuses]
    result = {"expected": len(expected), "executed": len(rows),
              "passed": statuses["PASS"], "failed": statuses["FAIL"],
              "errored": statuses["ERROR"], "skipped": statuses["SKIP"],
              "missing": sorted(expected_set - actual_set),
              "unexpected": sorted(actual_set - expected_set), "duplicates": duplicates,
              "expected_duplicates": expected_duplicates, "invalid_status_rows": invalid_rows}
    result["result"] = ("PASS" if not any((result["failed"], result["errored"], result["skipped"],
                                             result["missing"], result["unexpected"], duplicates,
                                             expected_duplicates, invalid_rows))
                        and len(rows) == len(expected) and result["passed"] == sorted(expected)
                        else "REJECT")
    return result


def validate(result, expected):
    accounting = identity_accounting(expected, result.get("controls", []))
    if accounting["result"] != "PASS":
        raise RuntimeError("QUALIFICATION_IDENTITY_ACCOUNTING_REJECT")
    if not REQUIRED_AFFECTED_CONTROLS <= set(expected):
        raise RuntimeError("MANDATORY_AFFECTED_CONTROLS_MISSING")
    if result.get("tests") != len(expected) or result.get("unique") != len(expected):
        raise RuntimeError("QUALIFICATION_TOTAL_ACCOUNTING_REJECT")
    if any(result.get(key) for key in ("failures", "errors", "skipped", "duplicates")):
        raise RuntimeError("QUALIFICATION_STATUS_ACCOUNTING_REJECT")
    return accounting
