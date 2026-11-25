// Independent cross-check of the colorectal core-indicator CQL on the HL7/CQF
// Java reference stack (info.cqframework cql-to-elm + engine + engine-fhir).
//
// It translates the CQL source in-process, executes it against the same
// synthetic cases the JavaScript runner uses, and compares every asserted
// define. Every expression referenced by a generated Measure is also executed
// for every case so runtime errors on any branch surface.
//
// usage: java -cp <classpath>:<classes> CqlJavaRunner \
//          <cql-dir> <fhirhelpers-cql> <cases.json> <value-sets.json> <fsh-generated-resources-dir> [results.json]
//
// The optional results.json receives every evaluated value ({case: {define: value}},
// resources rendered as "Type/id") so it can be diffed against another engine.
//
// Java 17 compatible on purpose (CI uses temurin 17).

import ca.uhn.fhir.context.FhirContext;
import ca.uhn.fhir.parser.IParser;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.InputStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import org.apache.commons.lang3.tuple.Pair;
import org.cqframework.cql.cql2elm.CqlCompilerException;
import org.cqframework.cql.cql2elm.CqlCompilerOptions;
import org.cqframework.cql.cql2elm.LibraryBuilder;
import org.cqframework.cql.cql2elm.LibraryManager;
import org.cqframework.cql.cql2elm.LibrarySourceProvider;
import org.cqframework.cql.cql2elm.ModelManager;
import org.cqframework.cql.cql2elm.model.CompiledLibrary;
import org.hl7.cql.model.NamespaceInfo;
import org.hl7.elm.r1.ExpressionDef;
import org.hl7.elm.r1.FunctionDef;
import org.hl7.elm.r1.VersionedIdentifier;
import org.hl7.fhir.instance.model.api.IBaseReference;
import org.hl7.fhir.instance.model.api.IBaseResource;
import org.hl7.fhir.instance.model.api.IPrimitiveType;
import org.hl7.fhir.r4.model.Bundle;
import org.hl7.fhir.r4.model.CodeableConcept;
import org.hl7.fhir.r4.model.Coding;
import org.hl7.fhir.r4.model.Resource;
import org.opencds.cqf.cql.engine.data.CompositeDataProvider;
import org.opencds.cqf.cql.engine.data.DataProvider;
import org.opencds.cqf.cql.engine.execution.CqlEngine;
import org.opencds.cqf.cql.engine.execution.Environment;
import org.opencds.cqf.cql.engine.execution.EvaluationResult;
import org.opencds.cqf.cql.engine.fhir.model.R4FhirModelResolver;
import org.opencds.cqf.cql.engine.model.CachingModelResolverDecorator;
import org.opencds.cqf.cql.engine.model.ModelResolver;
import org.opencds.cqf.cql.engine.retrieve.TerminologyAwareRetrieveProvider;
import org.opencds.cqf.cql.engine.runtime.Code;
import org.opencds.cqf.cql.engine.runtime.DateTime;
import org.opencds.cqf.cql.engine.runtime.Interval;
import org.opencds.cqf.cql.engine.terminology.CodeSystemInfo;
import org.opencds.cqf.cql.engine.terminology.TerminologyProvider;
import org.opencds.cqf.cql.engine.terminology.ValueSetInfo;

public class CqlJavaRunner {
    static final String FHIR_MODEL_URI = "http://hl7.org/fhir";
    static final Pattern LIBRARY_HEADER =
            Pattern.compile("^\\s*library\\s+([A-Za-z0-9_.\"]+)\\s+version\\s+'([^']+)'", Pattern.MULTILINE);
    static final ObjectMapper JSON = new ObjectMapper();

    public static void main(String[] args) throws Exception {
        if (args.length != 5 && args.length != 6) {
            System.err.println("usage: CqlJavaRunner <cql-dir> <fhirhelpers-cql> <cases.json> <value-sets.json> <resources-dir> [results.json]");
            System.exit(2);
        }
        long started = System.nanoTime();
        Path cqlDir = Path.of(args[0]);
        Path helpersCql = Path.of(args[1]);
        JsonNode cases = JSON.readTree(new File(args[2]));
        JsonNode valueSets = JSON.readTree(new File(args[3]));
        Path resourcesDir = Path.of(args[4]);

        // ---- library sources: every .cql in the IG plus FHIRHelpers 4.0.1 ----
        Map<String, String> sources = new HashMap<>(); // "name|version" -> CQL text
        VersionedIdentifier mainId = null;
        List<Path> cqlFiles = new ArrayList<>();
        try (var stream = Files.list(cqlDir)) {
            stream.filter(p -> p.toString().endsWith(".cql")).sorted().forEach(cqlFiles::add);
        }
        for (Path p : cqlFiles) {
            VersionedIdentifier id = register(sources, Files.readString(p));
            if (mainId == null || p.getFileName().toString().equals("ColorectalCancerCoreIndicators.cql")) {
                mainId = id;
            }
        }
        if (mainId == null) throw new IllegalStateException("no .cql files in " + cqlDir);
        register(sources, Files.readString(helpersCql));

        ModelManager modelManager = new ModelManager();
        CqlCompilerOptions options = CqlCompilerOptions.defaultOptions()
                .withSignatureLevel(LibraryBuilder.SignatureLevel.Overloads);
        LibraryManager libraryManager = new LibraryManager(modelManager, options);
        // `include hl7.fhir.uv.cql.FHIRHelpers` resolves through this namespace.
        libraryManager.getNamespaceManager().addNamespace(new NamespaceInfo("hl7.fhir.uv.cql", "http://hl7.org/fhir/uv/cql"));
        libraryManager.getLibrarySourceLoader().registerProvider(new LibrarySourceProvider() {
            @Override
            public InputStream getLibrarySource(VersionedIdentifier id) {
                String text = sources.get(id.getId() + "|" + id.getVersion());
                if (text == null && id.getVersion() == null) {
                    text = sources.entrySet().stream()
                            .filter(e -> e.getKey().startsWith(id.getId() + "|"))
                            .map(Map.Entry::getValue).findFirst().orElse(null);
                }
                return text == null ? null : new ByteArrayInputStream(text.getBytes(StandardCharsets.UTF_8));
            }
        });

        // ---- translate ----
        List<CqlCompilerException> errors = new ArrayList<>();
        CompiledLibrary compiled = libraryManager.resolveLibrary(mainId, errors);
        List<CqlCompilerException> fatal = errors.stream()
                .filter(e -> e.getSeverity() == CqlCompilerException.ErrorSeverity.Error)
                .collect(Collectors.toList());
        for (CqlCompilerException e : errors) {
            var loc = e.getLocator();
            System.err.printf("%s: %s%s%n", e.getSeverity(), e.getMessage(),
                    loc == null ? "" : " [" + loc.getLibrary().getId() + " " + loc.getStartLine() + ":" + loc.getStartChar() + "]");
        }
        if (!fatal.isEmpty()) {
            System.err.println("CQL translation failed (" + fatal.size() + " errors)");
            System.exit(1);
        }
        Set<String> defines = new TreeSet<>();
        for (ExpressionDef def : compiled.getLibrary().getStatements().getDef()) {
            if (!(def instanceof FunctionDef)) defines.add(def.getName());
        }

        // ---- Measure population expressions ----
        Set<String> measureExpressions = new LinkedHashSet<>();
        List<String> failures = new ArrayList<>();
        File[] measureFiles = resourcesDir.toFile().listFiles((d, n) -> n.startsWith("Measure-") && n.endsWith(".json"));
        if (measureFiles == null || measureFiles.length == 0) {
            System.err.println("no Measure resources found in " + resourcesDir + " (run SUSHI first)");
            System.exit(1);
        }
        java.util.Arrays.sort(measureFiles);
        for (File f : measureFiles) {
            JsonNode measure = JSON.readTree(f);
            List<JsonNode> criteria = new ArrayList<>();
            for (JsonNode group : measure.path("group")) group.path("population").forEach(criteria::add);
            measure.path("supplementalData").forEach(criteria::add);
            {
                for (JsonNode population : criteria) {
                    String expression = population.path("criteria").path("expression").asText(null);
                    if (expression == null) continue;
                    if (!defines.contains(expression)) {
                        failures.add(measure.path("id").asText() + ": unknown define " + json(expression));
                    }
                    measureExpressions.add(expression);
                }
            }
        }

        // ---- engine wiring shared across cases ----
        ModelResolver modelResolver = new CachingModelResolverDecorator(new R4FhirModelResolver());
        TerminologyProvider terminology = new FixtureTerminologyProvider(valueSets);
        IParser parser = FhirContext.forR4Cached().newJsonParser();
        Map<String, Object> parameters = new HashMap<>();
        parameters.put("Measurement Period", new Interval(
                new DateTime(OffsetDateTime.of(2025, 1, 1, 0, 0, 0, 0, ZoneOffset.ofHours(8))), true,
                new DateTime(OffsetDateTime.of(2025, 12, 31, 23, 59, 59, 999_000_000, ZoneOffset.ofHours(8))), true));

        Set<String> covered = new TreeSet<>();
        Map<String, Map<String, Object>> allResults = new LinkedHashMap<>();
        int comparisons = 0;
        int evaluations = 0;
        for (JsonNode testCase : cases) {
            String caseId = testCase.path("id").asText();
            JsonNode expected = testCase.path("expected");
            if (!expected.isObject() || expected.size() == 0) {
                failures.add(caseId + ": no assertions");
                continue;
            }
            Bundle bundle = parser.parseResource(Bundle.class, testCase.path("bundle").toString());
            List<Resource> resources = new ArrayList<>();
            for (Bundle.BundleEntryComponent entry : bundle.getEntry()) {
                if (entry.hasResource()) resources.add(entry.getResource());
            }
            List<Resource> patients = resources.stream()
                    .filter(r -> r.fhirType().equals("Patient")).collect(Collectors.toList());
            if (patients.size() != 1) {
                failures.add(caseId + ": expected exactly one Patient, found " + patients.size());
                continue;
            }
            String patientId = patients.get(0).getIdElement().getIdPart();
            // A case may carry its own Measurement Period (dates, +08:00).
            Map<String, Object> caseParameters = new HashMap<>(parameters);
            JsonNode period = testCase.path("measurementPeriod");
            if (!period.isMissingNode() && !(period.isArray() && period.size() == 2)) {
                failures.add(caseId + ": measurementPeriod must be [start, end]");
                continue;
            }
            if (period.isArray()) {
                java.time.LocalDate start = java.time.LocalDate.parse(period.get(0).asText());
                java.time.LocalDate end = java.time.LocalDate.parse(period.get(1).asText());
                caseParameters.put("Measurement Period", new Interval(
                        new DateTime(start.atStartOfDay().atOffset(ZoneOffset.ofHours(8))), true,
                        new DateTime(end.atTime(23, 59, 59, 999_000_000).atOffset(ZoneOffset.ofHours(8))), true));
            }

            BundleRetrieveProvider retrieve = new BundleRetrieveProvider(resources, modelResolver);
            retrieve.setTerminologyProvider(terminology);
            Map<String, DataProvider> dataProviders = new HashMap<>();
            dataProviders.put(FHIR_MODEL_URI, new CompositeDataProvider(modelResolver, retrieve));
            Environment environment = new Environment(libraryManager, dataProviders, terminology);
            CqlEngine engine = new CqlEngine(environment, EnumSet.of(CqlEngine.Options.EnableExpressionCaching));

            Set<String> expressions = new LinkedHashSet<>(measureExpressions);
            expected.fieldNames().forEachRemaining(expressions::add);
            for (String expression : expressions) {
                if (!defines.contains(expression)) {
                    failures.add(caseId + ": " + json(expression) + " is not a define in " + mainId.getId());
                    continue;
                }
                Object value;
                try {
                    EvaluationResult result = engine.evaluate(mainId, Set.of(expression),
                            Pair.<String, Object>of("Patient", patientId), caseParameters, null);
                    evaluations++;
                    if (result.forExpression(expression) == null) {
                        failures.add(caseId + ": no result for " + json(expression));
                        continue;
                    }
                    value = result.forExpression(expression).value();
                    allResults.computeIfAbsent(caseId, k -> new LinkedHashMap<>())
                            .put(expression, JSON.readTree(render(value)));
                } catch (Exception e) {
                    failures.add(caseId + ": " + json(expression) + " raised " + rootMessage(e));
                    continue;
                }
                if (expected.has(expression)) {
                    comparisons++;
                    JsonNode want = expected.get(expression);
                    if (matches(want, value)) {
                        covered.add(expression);
                    } else {
                        failures.add(caseId + ": " + json(expression) + " expected " + want + " got " + render(value));
                    }
                }
            }
        }

        if (args.length == 6) JSON.writerWithDefaultPrettyPrinter().writeValue(new File(args[5]), allResults);
        double seconds = (System.nanoTime() - started) / 1e9;
        if (!failures.isEmpty()) {
            System.err.println(String.join("\n", failures));
            System.err.printf("Java CQL engine: %d failure(s) across %d case(s), %d comparison(s), %.1fs%n",
                    failures.size(), cases.size(), comparisons, seconds);
            System.exit(1);
        }
        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("engine", "info.cqframework:engine-fhir:" + packageVersion(CqlEngine.class));
        summary.put("cases", cases.size());
        summary.put("comparisons", comparisons);
        summary.put("evaluations", evaluations);
        summary.put("measureExpressions", measureExpressions);
        summary.put("assertedExpressions", covered);
        summary.put("seconds", Math.round(seconds * 10) / 10.0);
        System.out.println(JSON.writeValueAsString(summary));
    }

    static VersionedIdentifier register(Map<String, String> sources, String text) {
        Matcher m = LIBRARY_HEADER.matcher(stripComments(text));
        if (!m.find()) throw new IllegalArgumentException("CQL without a versioned library header");
        String qualified = m.group(1).replace("\"", "");
        String name = qualified.contains(".") ? qualified.substring(qualified.lastIndexOf('.') + 1) : qualified;
        sources.put(name + "|" + m.group(2), text);
        return new VersionedIdentifier().withId(name).withVersion(m.group(2));
    }

    static String stripComments(String text) {
        return text.replaceAll("(?s)/\\*.*?\\*/", "").replaceAll("(?m)//.*$", "");
    }

    static String packageVersion(Class<?> c) {
        String v = c.getPackage().getImplementationVersion();
        if (v != null) return v;
        String location = c.getProtectionDomain().getCodeSource().getLocation().getPath();
        Matcher m = Pattern.compile("engine-([0-9][^/]*)\\.jar$").matcher(location);
        return m.find() ? m.group(1) : "unknown";
    }

    static String rootMessage(Throwable e) {
        StringBuilder sb = new StringBuilder(e.getClass().getSimpleName() + ": " + e.getMessage());
        Throwable cause = e.getCause();
        while (cause != null && cause != e) {
            sb.append(" <- ").append(cause.getClass().getSimpleName()).append(": ").append(cause.getMessage());
            e = cause;
            cause = cause.getCause();
        }
        return sb.toString();
    }

    static String json(String s) {
        try {
            return JSON.writeValueAsString(s);
        } catch (Exception e) {
            return s;
        }
    }

    // ---- comparison ----

    /** Expected values are JSON: null, boolean, number, string, or an array (order-insensitive). */
    static boolean matches(JsonNode want, Object got) {
        if (want == null || want.isNull()) return got == null;
        if (got == null) return false;
        if (want.isBoolean()) return got instanceof Boolean && (Boolean) got == want.booleanValue();
        if (want.isIntegralNumber()) {
            return (got instanceof Integer || got instanceof Long) && ((Number) got).longValue() == want.longValue();
        }
        if (want.isNumber()) return got instanceof BigDecimal && ((BigDecimal) got).compareTo(want.decimalValue()) == 0;
        if (want.isTextual()) {
            String s = want.textValue();
            if (got instanceof IBaseResource) {
                IBaseResource r = (IBaseResource) got;
                String idPart = r.getIdElement().getIdPart();
                return s.equals(idPart) || s.equals(r.fhirType() + "/" + idPart);
            }
            return got instanceof String && got.equals(s);
        }
        if (want.isArray()) {
            if (!(got instanceof Iterable)) return false;
            List<Object> remaining = new ArrayList<>();
            ((Iterable<?>) got).forEach(remaining::add);
            if (remaining.size() != want.size()) return false;
            for (JsonNode w : want) {
                Iterator<Object> it = remaining.iterator();
                boolean found = false;
                while (it.hasNext()) {
                    if (matches(w, it.next())) {
                        it.remove();
                        found = true;
                        break;
                    }
                }
                if (!found) return false;
            }
            return true;
        }
        return false;
    }

    static String render(Object v) {
        if (v == null) return "null";
        if (v instanceof Boolean || v instanceof Number) return v.toString();
        if (v instanceof String) return json((String) v);
        if (v instanceof IBaseResource) {
            IBaseResource r = (IBaseResource) v;
            return json(r.fhirType() + "/" + r.getIdElement().getIdPart());
        }
        if (v instanceof Iterable) {
            List<String> parts = new ArrayList<>();
            ((Iterable<?>) v).forEach(x -> parts.add(render(x)));
            return "[" + String.join(",", parts) + "]";
        }
        return json(v.getClass().getSimpleName() + ":" + v);
    }

    // ---- terminology from tests/fixtures/cql/value-sets.json ----

    /** Same shape cql-execution's CodeService takes: {url: {version: [{system, code}]}}. */
    static class FixtureTerminologyProvider implements TerminologyProvider {
        final Map<String, Map<String, List<Code>>> valueSets = new HashMap<>();

        FixtureTerminologyProvider(JsonNode node) {
            node.fields().forEachRemaining(vs -> {
                Map<String, List<Code>> versions = new LinkedHashMap<>();
                vs.getValue().fields().forEachRemaining(ver -> {
                    List<Code> codes = new ArrayList<>();
                    for (JsonNode c : ver.getValue()) {
                        codes.add(new Code().withSystem(c.path("system").asText())
                                .withCode(c.path("code").asText())
                                .withVersion(c.hasNonNull("version") ? c.get("version").asText() : null));
                    }
                    versions.put(ver.getKey(), codes);
                });
                valueSets.put(vs.getKey(), versions);
            });
        }

        List<Code> codes(ValueSetInfo info) {
            Map<String, List<Code>> versions = valueSets.get(info.getId());
            if (versions == null) throw new IllegalArgumentException("unknown value set " + info.getId());
            if (info.getVersion() != null) {
                List<Code> codes = versions.get(info.getVersion());
                if (codes == null) throw new IllegalArgumentException("unknown value set version " + info.getId() + "|" + info.getVersion());
                return codes;
            }
            return versions.values().iterator().next();
        }

        @Override
        public boolean in(Code code, ValueSetInfo info) {
            for (Code c : codes(info)) {
                if (c.getCode().equals(code.getCode()) && c.getSystem().equals(code.getSystem())) return true;
            }
            return false;
        }

        @Override
        public Iterable<Code> expand(ValueSetInfo info) {
            return codes(info);
        }

        @Override
        public Code lookup(Code code, CodeSystemInfo codeSystem) {
            throw new UnsupportedOperationException("code lookup is not supported by the fixture terminology");
        }
    }

    // ---- data: the case Bundle, filtered by type, patient and code ----

    static class BundleRetrieveProvider extends TerminologyAwareRetrieveProvider {
        final List<Resource> resources;
        final ModelResolver modelResolver;

        BundleRetrieveProvider(List<Resource> resources, ModelResolver modelResolver) {
            this.resources = resources;
            this.modelResolver = modelResolver;
        }

        @Override
        public Iterable<Object> retrieve(String context, String contextPath, Object contextValue, String dataType,
                String templateId, String codePath, Iterable<Code> codes, String valueSet, String datePath,
                String dateLowPath, String dateHighPath, Interval dateRange) {
            if (datePath != null || dateLowPath != null || dateHighPath != null || dateRange != null) {
                throw new UnsupportedOperationException("date-filtered retrieve is not supported by this runner");
            }
            List<Object> out = new ArrayList<>();
            for (Resource r : resources) {
                if (!r.fhirType().equals(dataType)) continue;
                if (contextPath != null && contextValue != null
                        && !contextValue.toString().equals(referencedId(modelResolver.resolvePath(r, contextPath)))) {
                    continue;
                }
                if (codePath != null && (codes != null || valueSet != null)) {
                    List<Code> resourceCodes = codesOf(modelResolver.resolvePath(r, codePath));
                    if (!codeMatches(resourceCodes, codes, valueSet)) continue;
                }
                out.add(r);
            }
            return out;
        }

        boolean codeMatches(List<Code> resourceCodes, Iterable<Code> codes, String valueSet) {
            for (Code rc : resourceCodes) {
                if (codes != null) {
                    for (Code c : codes) {
                        if (rc.getCode() != null && rc.getCode().equals(c.getCode())
                                && rc.getSystem() != null && rc.getSystem().equals(c.getSystem())) {
                            return true;
                        }
                    }
                }
                if (valueSet != null && terminologyProvider.in(rc, new ValueSetInfo().withId(valueSet))) return true;
            }
            return false;
        }

        static String referencedId(Object value) {
            if (value == null) return null;
            if (value instanceof Iterable) {
                for (Object v : (Iterable<?>) value) {
                    String id = referencedId(v);
                    if (id != null) return id;
                }
                return null;
            }
            String raw;
            if (value instanceof IBaseReference) {
                raw = ((IBaseReference) value).getReferenceElement().getIdPart();
            } else if (value instanceof IPrimitiveType) {
                raw = ((IPrimitiveType<?>) value).getValueAsString();
            } else {
                raw = value.toString();
            }
            if (raw == null) return null;
            int history = raw.indexOf("/_history/");
            if (history >= 0) raw = raw.substring(0, history);
            return raw.contains("/") ? raw.substring(raw.lastIndexOf('/') + 1) : raw;
        }

        static List<Code> codesOf(Object value) {
            List<Code> out = new ArrayList<>();
            if (value == null) return out;
            if (value instanceof Iterable) {
                for (Object v : (Iterable<?>) value) out.addAll(codesOf(v));
            } else if (value instanceof CodeableConcept) {
                for (Coding c : ((CodeableConcept) value).getCoding()) out.add(toCode(c));
            } else if (value instanceof Coding) {
                out.add(toCode((Coding) value));
            } else if (value instanceof IPrimitiveType) {
                out.add(new Code().withCode(((IPrimitiveType<?>) value).getValueAsString()));
            } else if (value instanceof Code) {
                out.add((Code) value);
            }
            return out;
        }

        static Code toCode(Coding c) {
            return new Code().withSystem(c.getSystem()).withCode(c.getCode()).withVersion(c.getVersion());
        }
    }
}
