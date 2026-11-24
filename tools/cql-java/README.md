# Java reference-engine cross-check

`scripts/run_cql_java.sh` runs the synthetic CQL cases on the HL7/CQF Java
reference stack. The main runner, `scripts/run_cql.sh`, uses the JavaScript
engine (`cql-execution` + `cql-exec-fhir`). The two engines do not always
behave the same: for example, the JavaScript engine accepts `Date(2025, 2, 31)`,
while the Java engine raises `Invalid date 'FEBRUARY 31'`. Running the same
cases on both engines catches that kind of difference.

## Usage

```sh
(cd ig && sushi .)                 # the Measures in ig/fsh-generated are required
scripts/run_cql_java.sh            # JAVA=/path/to/java to pick a JDK (17+)
CQL_JAVA_RESULTS=out.json scripts/run_cql_java.sh   # also dump every evaluated value
```

The script works without a Maven or Gradle install. It:

1. downloads `coursier.jar` (checksum verified) and resolves the pinned
   classpath into `.cql-work/java/classpath-*.txt`.
2. extracts the FHIRHelpers 4.0.1 CQL source from the `hl7.fhir.uv.cql#2.0.0`
   package (checksum verified).
3. compiles `src/CqlJavaRunner.java` with `javac --release 17`.
4. runs it on `ig/input/cql`, `tests/fixtures/cql/cases.json`,
   `tests/fixtures/cql/value-sets.json` and `ig/fsh-generated/resources`.

Everything is cached under `.cql-work/java/` (gitignored). Set
`CQL_JAVA_WORK_DIR` to cache it somewhere else.

## What the runner does

- **Translation.** It translates the CQL source in-process with `cql-to-elm`,
  using signature level Overloads. It does not reuse the ELM that the JS path
  produces, so translation is cross-checked as well. Translation errors stop
  the run. `include hl7.fhir.uv.cql.FHIRHelpers` resolves through the
  `hl7.fhir.uv.cql` namespace.
- **Terminology.** It reads `value-sets.json` (the `{url: {version: [{system, code}]}}`
  shape that the JS `CodeService` uses). `expand` and `in` are supported.
  `lookup` is not.
- **Data.**
  - Each case Bundle is the data source. The Patient context is the Bundle's
    single Patient.
  - Retrieves filter by resource type, by the patient context path, and by
    code or value set.
  - A date-filtered retrieve throws, so it never passes silently.
- **Parameters.** "Measurement Period" =
  `Interval[2025-01-01T00:00:00.000+08:00, 2025-12-31T23:59:59.999+08:00]`.
- **What is evaluated.** For each case, the runner evaluates every define named
  in `expected`, plus every population expression of every
  `Measure-*.json`. Each define is evaluated on its own, so a runtime error is
  reported against the define that raised it.
- **Comparison.** Expected values can be:
  - `null`, a boolean, an integer or a decimal.
  - a string. A resource result matches when the string equals its id or
    `Type/id`.
  - an array, compared to a list result without regard to order. For example,
    `["case-1-tumour"]` matches a `List<Condition>` that holds that one resource.
- **Exit status.** A mismatch, runtime error, unknown define or untranslatable
  CQL prints one line per problem, in the form
  `<case>: "<define>" expected <x> got <y>`, and exits with 1. A successful run
  prints a JSON summary.

## Pinned versions

| Component | Version |
|---|---|
| `info.cqframework:engine-fhir`, `engine`, `cql-to-elm`, `quick`, `model-jackson` | 3.26.0 (same translator version as `scripts/run_cql.sh`) |
| `ca.uhn.hapi.fhir:hapi-fhir-*` (forced) | 8.2.0 (engine-fhir's own BOM) |
| `org.slf4j:slf4j-simple` | 2.0.16 |
| coursier | 2.1.25-M26, sha256 `97647d03…93eb5e` |
| FHIRHelpers | 4.0.1 from `https://hl7.org/fhir/uv/cql/STU2/package.tgz`, sha256 `a7c20146…3c35a` |

The 3.26.0 jars target Java 17 (class file version 61), so the runner works on
JDK 17 and 21. To upgrade, bump `CQF_VERSION` and `HAPI_VERSION` together in
`scripts/run_cql_java.sh`. The classpath cache file name includes both versions,
so the classpath is resolved again.
