package com.example.platform.sandbox;

import static com.example.platform.sandbox.DiagnosticJson.object;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.AccessDeniedException;
import java.nio.file.Files;
import java.nio.file.NoSuchFileException;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/** Isolated experiment instrumentation. No collector, discovery loop, or alternate Process. */
final class TimeoutDiagnosticRecorder implements AutoCloseable {
    private static final int MAX_EVENTS = 8192;
    private static final int MAX_EVENT_CHARACTERS = 262144;
    private static final int MAX_BUFFER_CHARACTERS = 8 * 1024 * 1024;
    private static final int MAX_IDENTITIES = 256;
    private static final int PROC_BYTES = 16384;
    private static volatile TimeoutDiagnosticRecorder active;
    private final List<String> events = new ArrayList<>();
    private int bufferCharacters;
    private int eventsFlushed;
    private final Map<Long, Identity> identities = new LinkedHashMap<>();
    private final ArrayBlockingQueue<Map<String, Object>> journalQueue =
            new ArrayBlockingQueue<>(MAX_IDENTITIES);
    private final AtomicLong errors = new AtomicLong();
    private final AtomicLong droppedEvents = new AtomicLong();
    private final AtomicLong droppedIdentities = new AtomicLong();
    private final AtomicLong procErrors = new AtomicLong();
    private final AtomicLong procTruncations = new AtomicLong();
    private final AtomicLong captureReadErrors = new AtomicLong();
    private final AtomicLong captureCloseErrors = new AtomicLong();
    private final AtomicLong captureTruncations = new AtomicLong();
    private final AtomicLong captureDroppedBytes = new AtomicLong();
    private final AtomicLong journalWritten = new AtomicLong();
    private final FileChannel journal;
    private final Thread journalThread;
    private volatile boolean journalClosing;
    private Process root;
    private SandboxFailure primaryFailure;
    private boolean primaryRecorded;

    TimeoutDiagnosticRecorder(Path directory) throws IOException {
        journal = FileChannel.open(directory.resolve("registered-identities.jsonl"),
                StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
        journalThread = Thread.ofPlatform().daemon(true).name("diagnostic-identity-journal")
                .start(this::writeJournal);
    }

    void activate() {
        if (active != null) throw new IllegalStateException("recorder already active");
        active = this;
    }

    static long begin(String phase, Object... fields) {
        long now = System.nanoTime();
        record(phase + ".begin", now, now, fields);
        return now;
    }

    static void end(String phase, long start, Object... fields) {
        record(phase + ".end", start, System.nanoTime(), fields);
    }

    static void mark(String phase, Object... fields) {
        long now = System.nanoTime();
        record(phase, now, now, fields);
    }

    private static void record(String phase, long start, long end, Object... fields) {
        TimeoutDiagnosticRecorder recorder = active;
        if (recorder == null) return;
        try {
            recorder.add(object("phase", phase, "startNano", start, "endNano", end,
                    "data", object(fields)));
        } catch (RuntimeException failure) {
            recorder.errors.incrementAndGet();
        }
    }

    private synchronized void add(Map<String, Object> event) {
        String encoded = DiagnosticJson.encode(event);
        if (events.size() == MAX_EVENTS || encoded.length() > MAX_EVENT_CHARACTERS
                || bufferCharacters + encoded.length() > MAX_BUFFER_CHARACTERS) {
            droppedEvents.incrementAndGet();
        } else {
            events.add(encoded);
            bufferCharacters += encoded.length();
        }
    }

    static void rootStarted(Process process) {
        TimeoutDiagnosticRecorder recorder = active;
        if (recorder == null) return;
        recorder.root = process; // Preserve the actual Process even if registration fails.
        long start = begin("root.started", "pid", process.pid());
        recorder.register(process.toHandle(), "root");
        end("root.started", start, "pid", process.pid());
    }

    static void descendants(List<ProcessHandle> handles) {
        TimeoutDiagnosticRecorder recorder = active;
        if (recorder == null) return;
        for (ProcessHandle handle : handles) recorder.register(handle, "root.descendants");
    }

    private void register(ProcessHandle handle, String source) {
        if (identities.containsKey(handle.pid())) return;
        if (identities.size() >= MAX_IDENTITIES) {
            droppedIdentities.incrementAndGet();
            return;
        }
        Identity identity = new Identity(handle, source);
        identities.put(handle.pid(), identity);
        Map<String, Object> initial = sample(identity, true);
        Map<String, Object> registration = object("pid", handle.pid(), "source", source,
                "startInstant", identity.start == null ? null : identity.start.toString(),
                "startTicks", identity.ticks, "registrationNano", identity.registeredNano,
                "initialObservation", initial);
        mark("identity.registered", "identity", registration);
        // Only bounded queue insertion on the cleanup thread. The dedicated journal writer
        // persists registrations without bulk synchronous cleanup output.
        if (!journalQueue.offer(registration)) errors.incrementAndGet();
    }

    static void snapshot(String phase) {
        TimeoutDiagnosticRecorder recorder = active;
        if (recorder != null) recorder.snapshotAll(phase);
    }

    List<Map<String, Object>> snapshotAll(String phase) {
        long start = begin(phase);
        List<Map<String, Object>> samples = new ArrayList<>();
        for (Identity identity : identities.values()) samples.add(sample(identity, false));
        end(phase, start, "observations", samples,
                "interpretation", "isAlive is an observation, not proof of running or own reaping");
        return samples;
    }

    private static void snapshotTarget(long pid, String phase) {
        TimeoutDiagnosticRecorder recorder = active;
        if (recorder == null) return;
        Identity identity = recorder.identities.get(pid);
        if (identity != null) {
            long start = begin(phase, "pid", pid);
            end(phase, start, "observation", recorder.sample(identity, false));
        }
    }

    private Map<String, Object> sample(Identity identity, boolean registration) {
        long start = System.nanoTime();
        Map<String, Object> result = object("pid", identity.handle.pid(), "startNano", start,
                "registeredStartInstant", identity.start == null ? null : identity.start.toString(),
                "registeredStartTicks", identity.ticks);
        try {
            result.put("isAliveObserved", identity.handle.isAlive());
            if (identity.retired != null) {
                result.put("outcome", "not_resampled");
                result.put("reason", identity.retired);
                return result;
            }
            Instant before = identity.handle.info().startInstant().orElse(null);
            if (registration) identity.start = before;
            if (before == null || (!registration && identity.ticks == null)) {
                identity.retired = "unknown_start_identity";
                result.put("outcome", "unknown");
                return result;
            }
            if (!before.equals(identity.start)) {
                identity.retired = "identity_mismatch";
                result.put("outcome", "identity_mismatch");
                return result;
            }
            // No PID lookup, no parent read. Only the retained actual handle's stat/status.
            Path proc = Path.of("/proc", Long.toString(identity.handle.pid()));
            Stat stat = readStat(proc.resolve("stat"));
            Instant afterStat = identity.handle.info().startInstant().orElse(null);
            if (!before.equals(afterStat) || (!registration && !stat.ticks.equals(identity.ticks))) {
                identity.retired = "identity_mismatch";
                result.put("outcome", "identity_mismatch");
                return result; // Do not retain raw evidence from a different identity.
            }
            if (registration) identity.ticks = stat.ticks;
            String status = readBounded(proc.resolve("status"));
            String subset = status.lines().filter(line -> line.startsWith("State:")
                    || line.startsWith("Pid:") || line.startsWith("PPid:")
                    || line.startsWith("Uid:") || line.startsWith("NSpid:"))
                    .collect(java.util.stream.Collectors.joining("\n"));
            Stat confirm = readStat(proc.resolve("stat"));
            Instant after = identity.handle.info().startInstant().orElse(null);
            if (!stat.ticks.equals(confirm.ticks) || !before.equals(after)) {
                identity.retired = "identity_mismatch";
                result.put("outcome", "identity_mismatch");
                return result;
            }
            result.putAll(object("outcome", "matching_identity", "state", stat.state,
                    "ppid", stat.ppid, "startTicks", stat.ticks,
                    "startInstant", before.toString(), "rawStat", stat.raw,
                    "rawStatusSubset", subset, "rawConfirmStat", confirm.raw));
        } catch (NoSuchFileException missing) {
            identity.retired = "missing_proc_entry";
            result.put("outcome", "missing_proc_entry");
        } catch (AccessDeniedException | SecurityException denied) {
            procErrors.incrementAndGet();
            result.putAll(object("outcome", "permission_denied", "error", exception(denied)));
        } catch (IllegalArgumentException invalid) {
            procErrors.incrementAndGet();
            result.putAll(object("outcome", "parse_error", "error", exception(invalid)));
        } catch (IOException | RuntimeException failure) {
            procErrors.incrementAndGet();
            result.putAll(object("outcome", "unknown", "error", exception(failure)));
        } finally {
            result.put("endNano", System.nanoTime());
        }
        return result;
    }

    private String readBounded(Path path) throws IOException {
        try (var input = Files.newInputStream(path)) {
            byte[] bytes = input.readNBytes(PROC_BYTES + 1);
            if (bytes.length > PROC_BYTES) {
                procTruncations.incrementAndGet();
                throw new IOException("proc evidence exceeds byte bound");
            }
            return new String(bytes, StandardCharsets.UTF_8);
        }
    }

    private Stat readStat(Path path) throws IOException {
        String raw = readBounded(path);
        int close = raw.lastIndexOf(')');
        if (close < 0) throw new IllegalArgumentException("stat missing final command delimiter");
        String[] fields = raw.substring(close + 1).trim().split("\\s+");
        if (fields.length < 20 || fields[0].length() != 1) {
            throw new IllegalArgumentException("stat missing state/ppid/starttime fields");
        }
        return new Stat(raw, fields[0], Long.parseLong(fields[1]), Long.parseLong(fields[19]));
    }

    private record Stat(String raw, String state, long ppid, Long ticks) {}

    private static final class Identity {
        final ProcessHandle handle;
        final String source;
        final long registeredNano = System.nanoTime();
        Instant start;
        Long ticks;
        String retired;
        Identity(ProcessHandle handle, String source) { this.handle = handle; this.source = source; }
    }

    static void destroy(Process process) {
        long start = beforeSignal(process.pid(), "Process.destroy", "original_cleanup");
        try {
            process.destroy();
            afterSignal(process.pid(), "Process.destroy", start, "void", null);
        } catch (RuntimeException failure) {
            afterSignal(process.pid(), "Process.destroy", start, null, failure);
            throw failure;
        }
    }

    static Process destroyForcibly(Process process) {
        long start = beforeSignal(process.pid(), "Process.destroyForcibly", "original_cleanup");
        try {
            Process returned = process.destroyForcibly();
            afterSignal(process.pid(), "Process.destroyForcibly", start,
                    object("type", "Process", "sameInstance", returned == process), null);
            return returned;
        } catch (RuntimeException failure) {
            afterSignal(process.pid(), "Process.destroyForcibly", start, null, failure);
            throw failure;
        }
    }

    static boolean destroy(ProcessHandle handle) { return signal(handle, false, "original_cleanup"); }
    static boolean destroyForcibly(ProcessHandle handle) { return signal(handle, true, "original_cleanup"); }

    private static boolean signal(ProcessHandle handle, boolean force, String context) {
        String method = force ? "ProcessHandle.destroyForcibly" : "ProcessHandle.destroy";
        long start = beforeSignal(handle.pid(), method, context);
        try {
            boolean returned = force ? handle.destroyForcibly() : handle.destroy();
            afterSignal(handle.pid(), method, start, returned, null);
            return returned;
        } catch (RuntimeException failure) {
            afterSignal(handle.pid(), method, start, null, failure);
            throw failure;
        }
    }

    private static long beforeSignal(long pid, String method, String context) {
        if (context.equals("original_cleanup")) snapshotTarget(pid, context + ".signal.before_state");
        return begin("signal", "pid", pid, "method", method, "context", context);
    }

    private static void afterSignal(long pid, String method, long start, Object returned,
                                    RuntimeException failure) {
        end("signal", start, "pid", pid, "method", method, "returned", returned,
                "exception", exception(failure));
        snapshotTarget(pid, "signal.after_state");
    }

    static void captureError(String stream, String operation, IOException failure) {
        TimeoutDiagnosticRecorder recorder = active;
        if (recorder == null) return;
        if (operation.equals("read_or_implicit_close")) recorder.captureReadErrors.incrementAndGet();
        else recorder.captureCloseErrors.incrementAndGet();
        mark("capture.error", "stream", stream, "operation", operation, "error", exception(failure));
    }

    static void captureTruncated(long bytes) {
        TimeoutDiagnosticRecorder recorder = active;
        if (recorder == null) return;
        recorder.captureTruncations.incrementAndGet();
        recorder.captureDroppedBytes.addAndGet(bytes);
    }

    static ReaderCloseMarker readerCloseMarker(String stream) { return new ReaderCloseMarker(stream); }

    static final class ReaderCloseMarker implements AutoCloseable {
        private final String stream;
        private long start;
        ReaderCloseMarker(String stream) { this.stream = stream; }
        @Override public void close() { start = begin("capture.implicit_close", "stream", stream); }
        void finished() { end("capture.implicit_close", start, "stream", stream); }
    }

    static void primary(SandboxFailure failure) {
        TimeoutDiagnosticRecorder recorder = active;
        if (recorder == null) return;
        recorder.primaryFailure = failure;
        recorder.primaryRecorded = true;
        mark("primary_failure.before_return", "primaryFailure", failure(failure));
    }

    static void primaryBeforeCleanup(SandboxFailure failure) {
        TimeoutDiagnosticRecorder recorder = active;
        if (recorder == null) return;
        recorder.primaryFailure = failure;
        mark("primary_failure.before_cleanup", "primaryFailure", failure(failure));
    }

    Object primaryFailure() { return failure(primaryFailure); }
    boolean primaryRecorded() { return primaryRecorded; }

    static Object failure(SandboxFailure failure) {
        return failure == null ? null : object("code", failure.code().name(),
                "message", failure.message(), "missingCapabilities",
                failure.missingCapabilities().stream().map(Enum::name).sorted().toList());
    }

    static Object exception(Throwable failure) {
        if (failure == null) return null;
        String message = failure.getMessage();
        if (message != null && message.length() > 2048) message = message.substring(0, 2048);
        return object("type", failure.getClass().getName(), "message", message);
    }

    static Map<String, Object> cleanup(SandboxCleanupObservation c) {
        return object("completed", c.completed(), "namedContainerRemoved", c.namedContainerRemoved(),
                "engineClientReaped", c.engineClientReaped(),
                "workloadProcessesContained", c.workloadProcessesContained(),
                "captureStreamsClosed", c.captureStreamsClosed(), "descendantsObserved", c.descendantsObserved(),
                "survivors", c.survivors(), "detachedEngineHelpers", c.detachedEngineHelpers(),
                "engineClientProcessId", c.engineClientProcessId().isPresent()
                        ? c.engineClientProcessId().getAsLong() : null,
                "containerName", c.containerName(), "containerStatus", c.containerStatus(),
                "failure", failure(c.failure().orElse(null)), "failureMessage", c.failureMessage(),
                "diagnostic", c.diagnostic());
    }

    boolean rootIsAliveObserved() {
        // Retain identity instead of looking up a possibly reused historical numeric PID.
        return root != null && root.toHandle().isAlive();
    }

    Map<String, Object> teardown() {
        long start = begin("separate_teardown", "budgetMillis", 2000);
        long deadline = start + TimeUnit.SECONDS.toNanos(2);
        List<Map<String, Object>> actions = new ArrayList<>();
        for (Identity identity : identities.values()) {
            if (System.nanoTime() >= deadline) {
                actions.add(object("pid", identity.handle.pid(), "startInstant",
                        identity.start == null ? null : identity.start.toString(), "startTicks", identity.ticks,
                        "action", "none", "outcome", "budget_exhausted"));
                continue;
            }
            Map<String, Object> observed = sample(identity, false);
            String outcome = (String) observed.get("outcome");
            String action = "none";
            Object returned = null;
            Object error = null;
            if ("matching_identity".equals(outcome)) {
                if ("Z".equals(observed.get("state"))) outcome = "zombie_requires_external_parent_reaping";
                else if (Boolean.TRUE.equals(observed.get("isAliveObserved"))
                        && System.nanoTime() < deadline) {
                    action = "ProcessHandle.destroyForcibly";
                    try {
                        returned = signal(identity.handle, true, "separate_teardown");
                        outcome = "signal_returned_not_proof_of_exit";
                    } catch (RuntimeException failure) {
                        error = exception(failure);
                        outcome = "signal_exception";
                        errors.incrementAndGet();
                    }
                } else outcome = Boolean.TRUE.equals(observed.get("isAliveObserved"))
                        ? "budget_exhausted" : "not_alive_observed";
            }
            actions.add(object("pid", identity.handle.pid(), "startInstant",
                    identity.start == null ? null : identity.start.toString(), "startTicks", identity.ticks,
                    "before", observed, "action", action, "returned", returned,
                    "exception", error, "outcome", outcome));
        }
        Map<String, Object> rootWait = object("action", "none");
        long remaining = deadline - System.nanoTime();
        if (root != null && remaining > 0) {
            long waitStart = begin("separate_teardown.root_waitFor", "budgetNanos", remaining);
            try {
                boolean returned = root.waitFor(Math.max(0, deadline - System.nanoTime()), TimeUnit.NANOSECONDS);
                rootWait = object("action", "own_Process.waitFor", "returned", returned,
                        "meaning", "own root only; no descendant reaping claim");
            } catch (InterruptedException interrupted) {
                Thread.currentThread().interrupt();
                rootWait = object("action", "own_Process.waitFor", "exception", exception(interrupted));
                errors.incrementAndGet();
            } finally {
                end("separate_teardown.root_waitFor", waitStart, "outcome", rootWait);
            }
        }
        List<Map<String, Object>> later = new ArrayList<>();
        for (Identity identity : identities.values()) {
            later.add(System.nanoTime() < deadline ? sample(identity, false)
                    : object("pid", identity.handle.pid(), "outcome", "budget_exhausted"));
        }
        boolean unresolved = droppedIdentities.get() != 0 || later.stream().anyMatch(s -> {
            if ("missing_proc_entry".equals(s.get("outcome"))) return false;
            if ("not_resampled".equals(s.get("outcome"))
                    && "missing_proc_entry".equals(s.get("reason"))) return false;
            return !"matching_identity".equals(s.get("outcome"))
                    || !Boolean.FALSE.equals(s.get("isAliveObserved")) || "Z".equals(s.get("state"));
        });
        Map<String, Object> result = object("actions", actions, "rootWait", rootWait,
                "finalSnapshots", later, "unresolvedRisk", unresolved,
                "limitations", "No discovery beyond original handles; disappearance does not prove own reaping. "
                        + "Zombie descendants require external parent reaping. Procfs and signal operations "
                        + "have no hard syscall deadline; budget limits initiation and root wait.");
        end("separate_teardown", start, "result", result);
        return result;
    }

    Map<String, Object> status() {
        return object("eventLimit", MAX_EVENTS, "eventsRetained", eventCount(),
                "eventCharacterLimit", MAX_EVENT_CHARACTERS,
                "bufferCharacterLimit", MAX_BUFFER_CHARACTERS, "bufferCharacters", bufferCharacters,
                "eventsDropped", droppedEvents.get(), "identityLimit", MAX_IDENTITIES,
                "identitiesRegistered", identities.size(), "identitiesDropped", droppedIdentities.get(),
                "instrumentationErrors", errors.get(), "procErrors", procErrors.get(),
                "procTruncations", procTruncations.get(), "captureReadOrImplicitCloseErrors", captureReadErrors.get(),
                "captureExplicitCloseErrors", captureCloseErrors.get(),
                "captureTruncationEvents", captureTruncations.get(), "captureDroppedBytes", captureDroppedBytes.get(),
                "identitiesJournaled", journalWritten.get(), "journalQueuePending", journalQueue.size(),
                "journalThreadAlive", journalThread.isAlive(), "diagnosticFailed", failed());
    }

    private synchronized int eventCount() { return events.size(); }

    boolean failed() {
        return errors.get() != 0 || droppedEvents.get() != 0 || droppedIdentities.get() != 0
                || procErrors.get() != 0 || procTruncations.get() != 0;
    }

    void diagnosticError(String phase, Throwable failure) {
        errors.incrementAndGet();
        mark("diagnostic.error", "during", phase, "error", exception(failure));
    }

    void flushTimeline(Path directory) throws IOException {
        List<String> copy;
        synchronized (this) { copy = List.copyOf(events.subList(eventsFlushed, events.size())); }
        StringBuilder text = new StringBuilder();
        for (String event : copy) text.append(event).append('\n');
        // The status record is out-of-band and survives a full event buffer.
        text.append(DiagnosticJson.encode(object("phase", "recorder.status", "data", status()))).append('\n');
        try (FileChannel channel = FileChannel.open(directory.resolve("timeline.jsonl"),
                StandardOpenOption.WRITE, StandardOpenOption.APPEND)) {
            ByteBuffer bytes = StandardCharsets.UTF_8.encode(text.toString());
            while (bytes.hasRemaining()) channel.write(bytes);
            channel.force(true);
        }
        eventsFlushed += copy.size();
    }

    static void writeJson(Path path, Object value) throws IOException {
        Path temporary = Files.createTempFile(path.getParent(), "." + path.getFileName() + "-", ".tmp");
        try {
            writeDurable(temporary, DiagnosticJson.encode(value) + "\n");
            Files.move(temporary, path, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } finally {
            Files.deleteIfExists(temporary);
        }
    }

    private static void writeDurable(Path path, String value) throws IOException {
        try (FileChannel channel = FileChannel.open(path, StandardOpenOption.CREATE,
                StandardOpenOption.TRUNCATE_EXISTING, StandardOpenOption.WRITE)) {
            ByteBuffer bytes = StandardCharsets.UTF_8.encode(value);
            while (bytes.hasRemaining()) channel.write(bytes);
            channel.force(true);
        }
    }

    private void writeJournal() {
        try {
            while (!journalClosing || !journalQueue.isEmpty()) {
                Map<String, Object> registration = journalQueue.poll(50, TimeUnit.MILLISECONDS);
                if (registration == null) continue;
                ByteBuffer bytes = StandardCharsets.UTF_8.encode(DiagnosticJson.encode(registration) + "\n");
                while (bytes.hasRemaining()) journal.write(bytes);
                journal.force(true);
                journalWritten.incrementAndGet();
            }
        } catch (IOException | RuntimeException failure) {
            diagnosticError("identity_journal", failure);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            diagnosticError("identity_journal", interrupted);
        }
    }

    @Override public void close() throws IOException {
        journalClosing = true;
        try {
            journalThread.join(500);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            diagnosticError("journal_join", interrupted);
        }
        if (journalThread.isAlive() || journalWritten.get() != identities.size()) {
            diagnosticError("journal_incomplete", new IOException("identity journal did not finish"));
        }
        journal.close();
        active = null;
    }
}
