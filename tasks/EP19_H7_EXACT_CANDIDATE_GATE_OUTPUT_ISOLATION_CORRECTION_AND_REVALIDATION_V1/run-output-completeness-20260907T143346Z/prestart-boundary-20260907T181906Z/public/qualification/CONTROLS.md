# External prestart diagnostics controls

Scope: only the private copied runner and decision-evidence helper change. All
original executor dependencies, including observer/preservation, remain identical
to preimages. No product gates, formal prepare/baseline/launch, publication, network,
original executor changes, instruction changes, or preservation exclusions.

Run `qualify.py` using a new output directory. Each attempt retains its source
snapshot, source diff, native unittest log, native process exit, per-test results,
all fixtures (including malformed partial evidence), and dependency digests. Never
reuse an attempt directory. The qualification receipt has a distinct diagnostic
schema and cannot be used as an existing formal qualification receipt.

| Controls (test method suffixes) | Risk and evidence |
| --- | --- |
| real_run_all_positive_prestart_and_final | Real run_all, review/seal checks, execute_graph, START/final paths and real artifact verification. Synthetic technical preflight and gate adapter; owner check mocked. execution.D points to disposable fixture only. |
| real_run_all_protected_drift_before_start; actual_gate_boundary_rejects_before_command | Original mismatch reason, no START or command, decision capture retained at real call sites. Gate boundary uses real run_gate; repository exact checks reduced to empty fixture repository list. |
| actual_preflight_phase_and_rejection; launch_preflight_callsite_labels_and_blocks; final_callsite_drift_rejects_and_keeps_prestart | Actual preflight branches (intentionally unprepared technical fixture), launch phase propagation, final rejection and retained earlier PASS. |
| one_capture_binds_passing_decision_not_later_values; rejection_binds_capture_not_later_restoration; later_decision_cannot_overwrite_prior_receipt | Mutate fixture after actual Collector result; receipt contains original values and raw baseline digest. Unique read-only receipts preserve earlier decisions. No instruction body export. |
| incomplete_capture_preserves_partial_rows_and_errors; capture_exception_retains_accumulated_rows; injected_incomplete_even_equal_entries_rejects | Native missing file, injected EIO after partial result, injected INCOMPLETE with equal rows: all reject. Injections are not claimed as native I/O errors. |
| native_unreadable_capture_rejects_before_start; native_file_mutation_during_capture_unstable_rejects | Real chmod/EACCES and real mutation at an injected scheduling hook. Retain errno and instability details; restore only fixture access for inspection. |
| native_evidence_permission_failure_rejects_launch; injected_partial_write_failure_retained | Native permission-denied storage and injected ENOSPC after a real 64-byte partial write. Exact stderr error; no storage-persistence promise. Partial receipt remains read-only. |
| injected_fsync_failure_rejects_despite_complete_file | Injected fsync EIO after a complete file write still blocks START. Receipt explicitly limits PASS to the comparison and cannot prove writer completion. |
| unreadable_baseline_retains_error_when_scope_allows_evidence; malformed_baseline_retains_raw_identity_and_error | Native baseline EACCES and malformed fixture JSON retain errors; a readable malformed baseline retains its exact raw digest. |
| effective_scope_cannot_remove_stored_overlap | Caller scope additions cannot remove any stored protection during destination validation. |
| protected_permission_change_remains_mismatch; expected_missing_reappearance_is_not_accepted; directory_metadata_fields_remain_compared | Permission fields, expected absence, and complete original directory metadata equality stay strict. |
| observer_directory_entry_rejects_even_metadata_restored_in_fixture; observer_instruction_and_unknown_path_violations | Unchanged native inotify rejects directory entries, instructions and unknown paths. Directory control mocks all endpoint directory metadata back to its original values; real native entry event still rejects. It does not claim ctime can be restored by utime. |
| usage_runtime_protected_member_is_not_excluded; scope_overlap_rejected_without_writing_evidence; baseline_parent_directory_overlap_rejected | Runtime/usage remains compared. Both ancestor and descendant overlap against protected/sealed/frozen/enumeration/captured input scope rejects. No automatic policy repair. |
| output_symlink_rejects_without_following; output_symlink_ancestor_rejects | FD-relative writer refuses destination and ancestor symlinks; no write through either link. |
| successful_shadow_exception_and_exact_check_preserved | Only existing SHADOW PASS omission, and exact() still called and propagated. Exact Git semantics are mocked here and not requalified. Failed SHADOW gets no exception. |
| old_launch_seal_missing_new_helper_rejects; changed_launch_source_rejects_using_disposable_copy; mismatched_candidate_launch_identity_rejects | Actual launch rejects missing new source, changed copied runner and candidate mismatch before START. |
| stale_qualification_helper_universe_rejects; changed_qualification_program_identity_rejects | Real qualification dependency checks reject obsolete helper universe and mutated qualification source in disposable fixtures. |
| unchanged_original_helpers_and_no_removed_sources | Byte comparison of every preserved dependency, including execution, observer, coverage, preservation and frozen Shadow policy. Only runner changes and decision_evidence is added. |

Limits: endpoint captures are sequential, not atomic or gap monitors. Collector
file-scope directories contain metadata, not child inventories, exactly as before.
Native observer controls separately qualify entry-event rejection even with equal
endpoint metadata. No expected baseline refresh occurs. START-file presence does
not prove process history; process status is NOT_ESTABLISHED. Read-only exclusive
receipts are immutable to this writer, not protected against their owner changing
permissions. Existing historical scope may overlap the proposed evidence directory;
that is a blocking rejection, not permission to exclude or relocate inputs.
