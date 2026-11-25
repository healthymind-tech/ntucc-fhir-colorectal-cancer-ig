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
  // 第五點 exclusions and the 5.4 code table are no longer parameters: the
  // former is data (CRCOutsideDataExclusion), the latter fixed by the manual.
};

// Population expressions return lists of FHIR resources (population basis =
// Condition). Compare them as sorted lists of resource ids.
function normalize(value) {
  if (Array.isArray(value)) {
    return value.map(item => {
      const id = item?.id?.value ?? item?.id ?? item?._json?.id;
      return typeof id === 'string' ? id : item;
    }).sort();
  }
  return value;
}

function patientId(testCase) {
  const patients = testCase.bundle.entry.map(e => e.resource).filter(r => r.resourceType === 'Patient');
  assert.equal(patients.length, 1, `${testCase.id}: expected exactly one Patient`);
  return patients[0].id;
}

const MEASURE_POPULATIONS = {
  'crc-qi-01': { 'initial-population': 'Initial Population', denominator: 'Denominator 1', numerator: 'Numerator 1' },
  'crc-qi-02': { 'initial-population': 'Initial Population', denominator: 'Denominator 2',
    'denominator-exclusion': 'Denominator 2 Exclusion', numerator: 'Numerator 2' },
  'crc-qi-03': { 'initial-population': 'Initial Population', denominator: 'Denominator 3', numerator: 'Numerator 3' }
};

async function main() {
  const covered = new Set();
  const failures = [];
  const members = {}; // define -> Set of "case/tumour" ids, aggregated over all cases
  for (const testCase of testCases) {
    assert.ok(testCase.expected && Object.keys(testCase.expected).length, `${testCase.id}: no assertions`);
    const executor = new cql.Executor(library, codeService, { ...parameters, ...(testCase.parameters || {}) });
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
      const value = normalize(result[expression]);
      if (Array.isArray(value)) {
        members[expression] = members[expression] || new Set();
        value.forEach(id => members[expression].add(`${testCase.id}/${id}`));
      }
      if (Object.prototype.hasOwnProperty.call(testCase.expected, expression)) {
        try {
          assert.deepEqual(normalize(result[expression]), testCase.expected[expression]);
          covered.add(expression);
        } catch (error) {
          failures.push(`${testCase.id}: ${expression} expected ${JSON.stringify(testCase.expected[expression])} got ${JSON.stringify(normalize(result[expression]))}`);
        }
      }
    }
  }
  // The generated summary MeasureReports must be reproduced by the CQL: one
  // summary report per Measure, with matching counts and measureScore.
  const reported = new Set();
  for (const file of fs.readdirSync(resourcesDir).filter(name => name.startsWith('MeasureReport-'))) {
    const report = readJson(path.join(resourcesDir, file));
    const measureId = report.measure.split('/').pop().split('|')[0];
    const mapping = MEASURE_POPULATIONS[measureId];
    if (!mapping) {
      failures.push(`${report.id}: unknown measure ${report.measure}`);
      continue;
    }
    if (report.type === 'summary') reported.add(measureId);
    const cqlMembers = code => {
      const ids = new Set(members[mapping[code]] || []);
      // Proportion scoring: members of the denominator exclusion are removed
      // from the numerator, as a measure engine does.
      if (code === 'numerator' && mapping['denominator-exclusion']) {
        for (const id of members[mapping['denominator-exclusion']] || []) ids.delete(id);
      }
      return ids;
    };
    for (const population of report.group[0].population) {
      const code = population.code.coding[0].code;
      const got = cqlMembers(code).size;
      if (got !== population.count) {
        failures.push(`${report.id}: ${code} count ${population.count} but CQL gives ${got}`);
      }
    }
    // measureScore = numerator / (denominator - denominator exclusion).
    const denominator = cqlMembers('denominator');
    const excluded = [...cqlMembers('denominator-exclusion')].filter(id => denominator.has(id)).length;
    const effectiveDenominator = denominator.size - (mapping['denominator-exclusion'] ? excluded : 0);
    const score = report.group[0].measureScore?.value;
    if (effectiveDenominator === 0) {
      if (score !== undefined) failures.push(`${report.id}: measureScore ${score} but the denominator is empty`);
    } else {
      const expectedScore = cqlMembers('numerator').size / effectiveDenominator;
      if (typeof score !== 'number' || Math.abs(score - expectedScore) > 1e-4) {
        failures.push(`${report.id}: measureScore ${score} but CQL gives ${expectedScore.toFixed(4)}`);
      }
    }
  }
  for (const measureId of Object.keys(MEASURE_POPULATIONS)) {
    if (!reported.has(measureId)) failures.push(`${measureId}: no summary MeasureReport in ${resourcesDir}`);
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
