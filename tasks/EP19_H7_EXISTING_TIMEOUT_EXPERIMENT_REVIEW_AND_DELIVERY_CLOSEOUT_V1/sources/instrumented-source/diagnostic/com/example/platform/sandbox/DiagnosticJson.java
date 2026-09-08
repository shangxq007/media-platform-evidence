package com.example.platform.sandbox;

import java.util.LinkedHashMap;
import java.util.Map;

/** Small, strict stdlib encoder for diagnostic values only. */
final class DiagnosticJson {
    private DiagnosticJson() {}

    static Map<String, Object> object(Object... pairs) {
        if (pairs.length % 2 != 0) throw new IllegalArgumentException("unpaired JSON field");
        Map<String, Object> result = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) result.put((String) pairs[i], pairs[i + 1]);
        return result;
    }

    static String encode(Object value) {
        StringBuilder out = new StringBuilder();
        append(out, value);
        return out.toString();
    }

    private static void append(StringBuilder out, Object value) {
        if (value == null) out.append("null");
        else if (value instanceof Boolean || value instanceof Integer || value instanceof Long) {
            out.append(value);
        } else if (value instanceof String text) {
            out.append('"');
            for (int i = 0; i < text.length(); i++) {
                char c = text.charAt(i);
                switch (c) {
                    case '"' -> out.append("\\\"");
                    case '\\' -> out.append("\\\\");
                    case '\n' -> out.append("\\n");
                    case '\r' -> out.append("\\r");
                    case '\t' -> out.append("\\t");
                    default -> {
                        // Escape surrogate code units too: no lossy UTF-8 replacement.
                        if (c < 0x20 || Character.isSurrogate(c)) {
                            out.append("\\u");
                            for (int shift = 12; shift >= 0; shift -= 4) {
                                out.append("0123456789abcdef".charAt((c >> shift) & 15));
                            }
                        } else out.append(c);
                    }
                }
            }
            out.append('"');
        } else if (value instanceof Map<?, ?> map) {
            out.append('{');
            boolean first = true;
            for (var entry : map.entrySet()) {
                if (!first) out.append(',');
                first = false;
                append(out, (String) entry.getKey());
                out.append(':');
                append(out, entry.getValue());
            }
            out.append('}');
        } else if (value instanceof Iterable<?> values) {
            out.append('[');
            boolean first = true;
            for (Object item : values) {
                if (!first) out.append(',');
                first = false;
                append(out, item);
            }
            out.append(']');
        } else throw new IllegalArgumentException("unsupported JSON type: " + value.getClass());
    }
}
