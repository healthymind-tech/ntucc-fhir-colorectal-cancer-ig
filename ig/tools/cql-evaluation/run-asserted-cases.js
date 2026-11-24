// Execute the colorectal core indicator ELM against synthetic Bundles and
// assert every expected define value. Also checks that every population
// expression referenced by a generated Measure exists in the library.
//
// usage: node run-asserted-cases.js <main-elm> <fhirhelpers-elm> <cases> <value-sets> <fsh-generated-resources-dir>
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const cql = require('cql-execution');
const cqlfhir = require('cql-exec-fhir');

const [mainPath, helpersPath, casesPath, valueSetsPath, resourcesDir] = process.argv.slice(2);
if (!resourcesDir) {
  throw new Error('usage: node run-asserted-cases.js <main-elm> <fhirhelpers-elm> <cases> <value-sets> <resources-dir>');
}

const readJson = filePath => JSON.parse(fs.readFileSync(filePath, 'utf8'));
const mainElm = readJson(mainPath);
const helpersElm = readJson(helpersPath);
const testCases = readJson(casesPath);
const valueSets = readJson(valueSetsPath);

const helpersInclude = mainElm.library.includes?.def?.find(include => include.localIdentifier === 'FHIRHelpers');
const helpersIdentifier = helpersElm.library?.identifier;
assert.ok(helpersInclude?.path, 'main ELM has no FHIRHelpers include path');
assert.equal(helpersIdentifier?.id, 'FHIRHelpers');
assert.equal(helpersIdentifier?.version, helpersInclude.version);
const helperSuffix = `/${helpersIdentifier.id}`;
if (helpersInclude.path.endsWith(helperSuffix)) {
  helpersIdentifier.system = helpersInclude.path.slice(0, -helperSuffix.length);
}

const repository = new cql.Repository({ main: mainElm, FHIRHelpers: helpersElm });
const library = new cql.Library(mainElm, repository);
const codeService = new cql.CodeService(valueSets);
const defines = new Set(mainElm.library.statements.def.map(def => def.name));

// Every Measure population must point at a define that exists.
const measureExpressions = [];
for (const file of fs.readdirSync(resourcesDir).filter(name => name.startsWith('Measure-'))) {
  const measure = readJson(path.join(resourcesDir, file));
  for (const group of measure.group || []) {
    for (const population of group.population || []) {
      const expression = population.criteria.expression;
      assert.ok(defines.has(expression), `${measure.id}: unknown define ${expression}`);
      measureExpressions.push(expression);
    }
  }
}
assert.ok(measureExpressions.length > 0, 'no Measure resources found');

const parameters = {
  'Measurement Period': new cql.Interval(
    new cql.DateTime(2025, 1, 1, 0, 0, 0, 0, 8),
    new cql.DateTime(2025, 12, 31, 23, 59, 59, 999, 8),
    true,
    true
  )
};

function patientId(testCase) {
  const patients = testCase.bundle.entry.map(e => e.resource).filter(r => r.resourceType === 'Patient');
  assert.equal(patients.length, 1, `${testCase.id}: expected exactly one Patient`);
  return patients[0].id;
}

async function main() {
  const covered = new Set();
  const failures = [];
  for (const testCase of testCases) {
    assert.ok(testCase.expected && Object.keys(testCase.expected).length, `${testCase.id}: no assertions`);
    const executor = new cql.Executor(library, codeService, parameters);
    const id = patientId(testCase);
    // Execute every Measure expression for every case so runtime errors on any
    // branch surface, then compare the asserted ones.
    const expressions = new Set([...measureExpressions, ...Object.keys(testCase.expected)]);
    for (const expression of expressions) {
      const source = cqlfhir.PatientSource.FHIRv401();
      source.loadBundles([testCase.bundle]);
      const execution = await executor.exec_expression(expression, source);
      const result = execution.patientResults[id];
      assert.ok(result && Object.prototype.hasOwnProperty.call(result, expression), `${testCase.id}: no result for ${expression}`);
      if (Object.prototype.hasOwnProperty.call(testCase.expected, expression)) {
        try {
          assert.deepEqual(result[expression], testCase.expected[expression]);
          covered.add(expression);
        } catch (error) {
          failures.push(`${testCase.id}: ${expression} expected ${JSON.stringify(testCase.expected[expression])} got ${JSON.stringify(result[expression])}`);
        }
      }
    }
  }
  if (failures.length) {
    console.error(failures.join('\n'));
    process.exitCode = 1;
    return;
  }
  process.stdout.write(`${JSON.stringify({ cases: testCases.length, assertedExpressions: [...covered].sort() })}\n`);
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
