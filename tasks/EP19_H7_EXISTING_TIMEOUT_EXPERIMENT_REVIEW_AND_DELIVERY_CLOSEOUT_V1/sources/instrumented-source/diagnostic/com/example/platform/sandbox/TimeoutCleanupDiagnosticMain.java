package com.example.platform.sandbox;

import static com.example.platform.sandbox.DiagnosticJson.object;
import static com.example.platform.sandbox.TimeoutDiagnosticRecorder.writeJson;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.EnumSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;

/** Exactly one owner-consumed real timeout attempt. There is deliberately no self-test mode. */
public final class TimeoutCleanupDiagnosticMain {
    private TimeoutCleanupDiagnosticMain() {}

    public static void main(String[] args) {
        System.exit(run(args));
    }

    private static int run(String[] args) {
        Path directory;
        try {
            if (args.length != 1) throw new IllegalArgumentException("one external runtime directory required");
            directory = Path.of(args[0]).toAbsolutePath().normalize();
            if (!Files.isDirectory(directory, LinkOption.NOFOLLOW_LINKS)
                    || !directory.toRealPath().equals(directory)) {
                throw new IOException("runtime directory must pre-exist without symlink components");
            }
            Path marker = directory.resolve("owner-attempt-consumed");
            if (!Files.isRegularFile(marker, LinkOption.NOFOLLOW_LINKS)) {
                throw new IOException("missing pre-existing owner-attempt-consumed marker; launch refused");
            }
            // CREATE_NEW atomically disallows another invocation in the same consumed attempt.
            Files.writeString(directory.resolve("diagnostic-started"),
                    "single timeout attempt reserved\n", StandardOpenOption.CREATE_NEW);
            for (String name : List.of("timeline.jsonl", "result.json", "teardown.json", "recorder-status.json")) {
                Files.createFile(directory.resolve(name));
            }
        } catch (Exception failure) {
            System.err.println(DiagnosticJson.encode(object("status", "diagnostic_error",
                    "launchAttempted", false, "error", TimeoutDiagnosticRecorder.exception(failure))));
            return 2;
        }

        TimeoutDiagnosticRecorder recorder = null;
        Map<String, Object> original = null;
        Map<String, Object> teardown = object("status", "not_started", "unresolvedRisk", true);
        Object diagnosticFailure = null;
        boolean originalPass = false;
        boolean launchAttempted = false;
        boolean originalFlushed = false;
        long returnedNano = 0;
        try {
            writeJson(directory.resolve("result.json"), envelope(null, null, false, false, null));
            writeJson(directory.resolve("teardown.json"), teardown);
            recorder = new TimeoutDiagnosticRecorder(directory);
            recorder.activate();
            Path workspace = Files.createDirectory(directory.resolve("workspace"));
            Path input = Files.writeString(workspace.resolve("immutable-input.txt"), "immutable",
                    StandardOpenOption.CREATE_NEW);

            Set<SandboxCapability> declared = EnumSet.of(
                    SandboxCapability.PROCESS_TREE_CONTAINMENT,
                    SandboxCapability.WALL_CLOCK_TIMEOUT,
                    SandboxCapability.FILESYSTEM_PATH_VALIDATION,
                    SandboxCapability.FILESYSTEM_ACCESS_ISOLATION,
                    SandboxCapability.NETWORK_NONE,
                    SandboxCapability.ENVIRONMENT_CLEARING,
                    SandboxCapability.BOUNDED_CAPTURE,
                    SandboxCapability.UNPRIVILEGED_EXECUTION,
                    SandboxCapability.HOST_EXPOSURE_DENIAL,
                    SandboxCapability.DEVICE_NONE);
            // Package-private factory is required by the real resolver/launcher; the mechanism
            // and metadata explicitly identify this as a declaration, never a fresh probe.
            SandboxRuntimeCapabilities capabilities = SandboxRuntimeCapabilities.detected(declared,
                    "diagnostic-declarative-not-probed", Instant.EPOCH);
            TimeoutDiagnosticRecorder.mark("scenario", "capabilityEvidence", object(
                    "kind", "diagnostic_declaration", "freshlyProbed", false,
                    "mechanism", capabilities.mechanism(), "observedAt", capabilities.observedAt().toString(),
                    "capabilities", declared.stream().map(Enum::name).sorted().toList()),
                    "command", List.of("/usr/bin/timeout", "30", "/usr/bin/sleep", "30"),
                    "environment", Map.of(), "timeoutMillis", 250, "captureBytes", 1024,
                    "cancellation", "never", "ownerAttemptMarker", "owner-attempt-consumed");
            SandboxExecutionRequirement requirement = new SandboxExecutionRequirement(
                    ProcessRequirement.of(Set.of("/usr/bin/timeout"), "/usr/bin/timeout",
                            List.of("30", "/usr/bin/sleep", "30"), Duration.ofMillis(250)),
                    FilesystemPolicy.exact(Set.of(input), workspace,
                            workspace.resolve(".sandbox-tmp"), workspace.resolve(".sandbox-output"), workspace),
                    NetworkPolicy.none(), EnvironmentPolicy.exact(Map.of()), SecretExposure.none(),
                    PrivilegePolicy.unprivileged(), ResourceEnforcementLimits.captureOnly(1024),
                    DeviceExposurePolicy.none());
            BubblewrapSandboxProcessLauncher launcher = new BubblewrapSandboxProcessLauncher(
                    Path.of("/usr/bin/bwrap"), capabilities);
            launchAttempted = true;
            SandboxExecutionResult result = launcher.launchResolved(requirement, SandboxCancellation.never());
            returnedNano = System.nanoTime();
            boolean rootAlive = recorder.rootIsAliveObserved();
            SandboxCleanupObservation cleanup = result.observation().cleanup();
            boolean failurePresent = result.failure().isPresent();
            boolean failureIsTimeout = result.failure().map(f -> f.code() == SandboxFailureCode.PROCESS_TIMEOUT)
                    .orElse(false);
            originalPass = failurePresent && failureIsTimeout && cleanup.completed()
                    && cleanup.failure().isEmpty() && cleanup.survivors().isEmpty() && !rootAlive;
            original = object("returnedNano", returnedNano,
                    "primaryFailureRecorded", recorder.primaryRecorded(), "primaryFailure", recorder.primaryFailure(),
                    "failure", TimeoutDiagnosticRecorder.failure(result.failure().orElse(null)),
                    "cleanup", TimeoutDiagnosticRecorder.cleanup(cleanup),
                    "exitCode", result.exitCode().isPresent() ? result.exitCode().getAsInt() : null,
                    "stdout", capture(result.stdout()), "stderr", capture(result.stderr()),
                    "observation", object("processId", result.observation().handle().processId(),
                            "workingDirectory", result.observation().workingDirectory().toString(),
                            "elapsedNanos", result.observation().elapsed().toNanos(),
                            "handle", result.observation().handle().toString()),
                    "originalPredicates", object("failurePresent", failurePresent,
                            "failureCodeEqualsPROCESS_TIMEOUT", failureIsTimeout,
                            "cleanupCompleted", cleanup.completed(), "cleanupFailureEmpty", cleanup.failure().isEmpty(),
                            "cleanupSurvivorsEmpty", cleanup.survivors().isEmpty(),
                            "rootIsAliveObserved", rootAlive, "rootNotAlive", !rootAlive,
                            "rootPredicateEvaluation", "retained actual root ProcessHandle.isAlive; no numeric PID relookup",
                            "combinedPass", originalPass));
            TimeoutDiagnosticRecorder.mark("main.returned_original_result", "originalResult", original);
            recorder.snapshotAll("follow_up.immediately_after_return");
            writeJson(directory.resolve("result.json"), envelope(original, null, originalPass, true, recorder.status()));
            recorder.flushTimeline(directory);
            originalFlushed = true;
            // Measured from actual return; disk flush time is visible and may exceed 200 ms.
            long remaining = returnedNano + TimeUnit.MILLISECONDS.toNanos(200) - System.nanoTime();
            if (remaining > 0) TimeUnit.NANOSECONDS.sleep(remaining);
            TimeoutDiagnosticRecorder.mark("follow_up.delay", "sinceReturnNanos", System.nanoTime() - returnedNano);
            recorder.snapshotAll("follow_up.about_200ms_after_return");
        } catch (Exception failure) {
            diagnosticFailure = TimeoutDiagnosticRecorder.exception(failure);
            if (failure instanceof InterruptedException) Thread.currentThread().interrupt();
            if (recorder != null) recorder.diagnosticError("main", failure);
        } finally {
            if (recorder != null) {
                // Best effort durable preservation is attempted before ANY separate teardown,
                // including the exceptional path. Failure to persist never suppresses teardown.
                if (!originalFlushed) {
                    try {
                        writeJson(directory.resolve("result.json"), envelope(original, diagnosticFailure,
                                originalPass, launchAttempted, recorder.status()));
                        recorder.flushTimeline(directory);
                        originalFlushed = true;
                    } catch (Exception failure) {
                        recorder.diagnosticError("pre_teardown_flush", failure);
                        diagnosticFailure = TimeoutDiagnosticRecorder.exception(failure);
                    }
                }
                try {
                    teardown = recorder.teardown();
                    teardown.put("originalArtifactsFlushedBeforeTeardown", originalFlushed);
                } catch (Exception failure) {
                    recorder.diagnosticError("teardown", failure);
                    teardown = object("status", "diagnostic_error", "error", TimeoutDiagnosticRecorder.exception(failure),
                            "unresolvedRisk", true, "originalArtifactsFlushedBeforeTeardown", originalFlushed);
                    diagnosticFailure = TimeoutDiagnosticRecorder.exception(failure);
                }
                try {
                    recorder.close();
                } catch (Exception failure) {
                    recorder.diagnosticError("recorder_close", failure);
                    diagnosticFailure = TimeoutDiagnosticRecorder.exception(failure);
                }
            }
            try {
                if (recorder != null && recorder.failed() && diagnosticFailure == null) {
                    diagnosticFailure = object("type", "recorder_failure", "message", "See recorder-status.json");
                }
                writeJson(directory.resolve("teardown.json"), teardown);
                writeJson(directory.resolve("result.json"), envelope(original, diagnosticFailure,
                        originalPass, launchAttempted, recorder == null ? null : recorder.status()));
                if (recorder != null) {
                    recorder.flushTimeline(directory);
                    writeJson(directory.resolve("recorder-status.json"), recorder.status());
                } else {
                    writeJson(directory.resolve("recorder-status.json"), object("diagnosticFailed", true,
                            "error", diagnosticFailure));
                }
            } catch (Exception failure) {
                diagnosticFailure = TimeoutDiagnosticRecorder.exception(failure);
                System.err.println(DiagnosticJson.encode(object("status", "diagnostic_error",
                        "during", "final_flush", "error", diagnosticFailure)));
                // An unwritable evidence directory cannot be made reliable by further writes.
            }
        }
        return diagnosticFailure != null || recorder == null || recorder.failed() ? 2 : originalPass ? 0 : 1;
    }

    private static Map<String, Object> capture(BoundedCapture capture) {
        return object("utf8", capture.utf8(), "bytesBase64",
                java.util.Base64.getEncoder().encodeToString(capture.bytes()),
                "byteCount", capture.bytes().length, "truncated", capture.truncated());
    }

    private static Map<String, Object> envelope(Map<String, Object> original, Object diagnosticFailure,
                                               boolean pass, boolean launchAttempted, Object status) {
        if (diagnosticFailure == null && status instanceof Map<?, ?> fields
                && Boolean.TRUE.equals(fields.get("diagnosticFailed"))) {
            diagnosticFailure = object("type", "recorder_failure", "message", "See recorderStatus");
        }
        return object("status", diagnosticFailure != null ? "diagnostic_error"
                        : original == null ? "diagnostic_incomplete" : "original_result_recorded",
                "launchAttempted", launchAttempted, "originalResult", original,
                "originalAssertionsPass", pass, "diagnosticFailure", diagnosticFailure,
                "recorderStatus", status,
                "capabilityEvidenceKind", "diagnostic_declaration_not_freshly_probed");
    }
}
