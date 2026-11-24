/*
Colorectal cancer core indicators (衛生福利部國民健康署「115 年癌症診療核心測量指標」大腸癌 3 項).

Normative expression of mappings/crc-core-indicator-criteria.csv. Every define
below carries the criterion_id from that file; reference/crc_indicators.py is
the independent Python reference implementation of the same table, and the two
are checked against the same synthetic cases (tests/fixtures/synthetic-cases.json).

UNIT OF MEASUREMENT: the official numerators and denominators are "人數"
(number of persons). After 註1 de-duplication a person keeps one registry case
per hospital and 癌別, so within one hospital counting the kept cases equals
counting persons. The population basis is Condition (the kept primary tumour)
so that every registry field is attributed to the right case: a field of one
tumour can never be read for another.

ASSUMPTIONS. One FHIR Patient per person (de-duplication runs inside Patient
context and cannot merge two Patient resources of one person). References are
resolved: "Condition/id", absolute URLs ending in it, optionally with
"/_history/n"; urn:uuid references must be resolved before evaluation.

RAW VALUES. Every registry value is trimmed of leading and trailing ASCII
spaces and tabs; nothing else is removed, so an internal blank makes a value
malformed. Digits are ASCII only. reference/ applies the same rule.

Registry long-form fields are CRCTCRDataItemObservation resources whose focus
references the tumour. When one field of one tumour has several current values
(e.g. a final and a later amended abstract), the value with the latest issued
time is used, so the result never depends on retrieval order.

Indicators 2 and 3 are written directly on the registry fields named in the
official text (valueString keeps the raw value). Indicator 1 is "醫院自行申報":
criteria A and C are not in the registry, so it also reads clinical facts, and
every fact must be linked to the same tumour: features by Observation.focus,
the pathology report by Condition.evidence.detail, the resection by
Procedure.reasonReference.
*/

library ColorectalCancerCoreIndicators version '0.1.0-preview.1'

using FHIR version '4.0.1'

include hl7.fhir.uv.cql.FHIRHelpers version '4.0.1' called FHIRHelpers

valueset "Malignant Polyp": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-malignant-polyp'
valueset "Malignant Polyp Pathology Report": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-malignant-polyp-pathology-report'
valueset "Colon Excluding Appendix": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-colon-excluding-appendix'
valueset "Rectosigmoid Or Rectum": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-rectosigmoid-rectum'
valueset "Colorectal Category": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-colorectal-category'
valueset "Colonoscopy High Risk Feature": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-colonoscopy-high-risk-feature'
valueset "Criterion B Met": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-criterion-b-met'
valueset "Criterion C Met": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-criterion-c-met'
valueset "Criterion D Met": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-criterion-d-met'
valueset "Curative Resection": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-curative-resection'

codesystem "LOINC": 'http://loinc.org'

code "Margin Involvement": '85290-5' from "LOINC" display 'Surgical margin tumor involvement [Presence] in Colorectal cancer specimen by Light microscopy'
code "Lymphovascular Invasion": '59544-7' from "LOINC" display 'Lymph-vascular invasion Cancer specimen'
code "Histologic Grade": '33732-9' from "LOINC" display 'Histology grade [Identifier] in Cancer specimen'

parameter "Measurement Period" Interval<DateTime>

// Raw 5.4 生存狀態 values that mean "dead". The long-form code table was not
// available from any source this IG could verify, so the caller supplies it
// (see the case assembly page). The default only covers a boolean rendering.
parameter "Vital Status Dead Codes" List<String> default { 'true' }

// 第五點: tumour ids the hospital excludes from one indicator because the
// numerator and denominator data are both outside, or the numerator data is
// outside and could not be obtained. Supplied per indicator by the hospital.
// No default on purpose: cql-execution 3.3.2 fails type-checking a supplied
// List<String> when the declaration has an empty-list default. A missing list
// is handled by "Is Outside Excluded" (not Coalesce, which cql-execution
// flattens into list elements when its operands are lists).
parameter "Outside Data Excluded QI01" List<String>
parameter "Outside Data Excluded QI02" List<String>
parameter "Outside Data Excluded QI03" List<String>

context Patient

// ==========================================================================
// references and registry value access
// ==========================================================================

// True when a relative or absolute reference, with or without a version
// suffix (/_history/n), points at the given resource.
define function "Points To"(Ref FHIR.Reference, ResourceType String, ResourceId String):
  "Unversioned"(Ref.reference.value) = ResourceType + '/' + ResourceId
    or EndsWith("Unversioned"(Ref.reference.value), '/' + ResourceType + '/' + ResourceId)

define function "Unversioned"(Reference String):
  ReplaceMatches(Reference, '/_history/[^/]*$', '')

// Leading and trailing ASCII spaces/tabs removed. A value made only of
// whitespace (Java Character.isWhitespace set, e.g. CR, LF, U+3000; not the
// no-break spaces) is no value: HAPI drops such values when parsing, so the
// rule must be the same on every engine. Explicit class, not \s, because
// \s differs between the JavaScript and Java regex engines.
define function "Trimmed"(Raw String):
  if Raw is null then null
  else if Matches(Raw, '[ \\t\\n\\r\\u000B\\f\\u001C-\\u001F\\u1680\\u2000-\\u2006\\u2008-\\u200A\\u2028\\u2029\\u205F\\u3000]*') then null
  else ReplaceMatches(ReplaceMatches(Raw, '^[ \\t]+', ''), '[ \\t]+$', '')

define "TCR Field System":
  'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/CodeSystem/crc-tcr-field'

// A registry item belongs to exactly one tumour (profile: focus 1..1); items
// with several focus targets are ignored rather than attributed to all.
define "Registry Items":
  [Observation] Item
    where Item.status in { 'final', 'amended', 'corrected' }
      and exists (Item.code.coding C where C.system.value = "TCR Field System")
      and Count(Item.focus) = 1

// IP-UNIT: a primary tumour is a Condition that registry fields are abstracted for.
// Conditions recorded in error or refuted are never cases.
define "Primary Tumours":
  [Condition] Tumour
    where not exists (Tumour.verificationStatus.coding V
        where V.system.value = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'
          and V.code.value in { 'entered-in-error', 'refuted' })
      and exists ("Registry Items" Item
        where exists (Item.focus F where "Points To"(F, 'Condition', Tumour.id)))

define function "Field Versions"(Tumour Condition, Field String):
  "Registry Items" Item
    where exists (Item.code.coding C where C.system.value = "TCR Field System" and C.code.value = Field)
      and exists (Item.focus F where "Points To"(F, 'Condition', Tumour.id))
    // id must be the string value: sorting the FHIR.id element itself compares
    // objects, which the JavaScript engine orders arbitrarily.
    return Tuple { issued: Item.issued.value, id: Item.id.value, raw: (Item.value as FHIR.string).value }

// IP-CURRENT: the current value of one registry field of one tumour: latest issued wins;
// equal issued times fall back to the Observation id so the choice is stable.
// A version without issued (the profile requires it) ranks below every dated
// version, so it is used only when no version is dated.
define function "Registry Value"(Tumour Condition, Field String):
  "Trimmed"(Last(
    (("Field Versions"(Tumour, Field)) Candidate
      where (Candidate.issued is null and not exists (("Field Versions"(Tumour, Field)) Dated where Dated.issued is not null))
        or Candidate.issued = Max(("Field Versions"(Tumour, Field)) Other return Other.issued)
    ) Latest
      sort by id
  ).raw)

// Registry dates are YYYYMMDD. 00000000 (none) and 99999999 (unknown), and any
// value with an unknown month or day, are not a calendar date and yield null.
// A well-formed but nonexistent day (20250231) is rejected explicitly: the
// JavaScript engine does not refuse Date(2025, 2, 31) and would count it.
define function "Registry Date"(Raw String):
  if Raw is null then null
  else if not Matches(Raw, '[0-9]{4}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])') then null
  else "Checked Date"(
    ToInteger(Substring(Raw, 0, 4)),
    ToInteger(Substring(Raw, 4, 2)),
    ToInteger(Substring(Raw, 6, 2))
  )

define function "Checked Date"(Y Integer, M Integer, D Integer):
  if D > "Days In Month"(Y, M) then null
  else Date(Y, M, D)

define function "Days In Month"(CalendarYear Integer, CalendarMonth Integer):
  case
    when CalendarMonth in { 4, 6, 9, 11 } then 30
    when CalendarMonth = 2 then
      if (CalendarYear mod 4 = 0 and CalendarYear mod 100 != 0) or CalendarYear mod 400 = 0 then 29 else 28
    else 31
  end

define function "Registry Integer"(Raw String):
  if Raw is null then null
  else if Matches(Raw, '[0-9]+') then ToInteger(Raw)
  else null

// ICD-O-3 topography with or without the dot (C18.7, C187, c187); anything
// else is malformed and yields null.
define function "Normalized Site"(Raw String):
  if Raw is null then null
  else if not Matches(Upper(Raw), 'C[0-9]{2}\\.?[0-9]') then null
  else ReplaceMatches(Upper(Raw), '\\.', '')

// Stage groups are coded with an Arabic leading digit (1A, 2B, 3C, 4).
// 0/0A (in situ), 888 and 999 do not start with 1-3.
define function "Stage Leading Digit"(Raw String):
  if Raw is null or Length(Raw) = 0 then null
  else Substring(Raw, 0, 1)

define function "Class Of Case"(Tumour Condition): "Registry Value"(Tumour, '2.3')
define function "Diagnosis Status"(Tumour Condition): "Registry Value"(Tumour, '2.3.1')
define function "Treatment Status"(Tumour Condition): "Registry Value"(Tumour, '2.3.2')
define function "Date Of Initial Diagnosis"(Tumour Condition): "Registry Date"("Registry Value"(Tumour, '2.5'))
define function "Primary Site"(Tumour Condition): "Normalized Site"("Registry Value"(Tumour, '2.6'))

// The registry writes topography without the dot (C187); the site ValueSets
// use ICD-O-3 notation (C18.7). Malformed values yield null, never a code.
define function "Primary Site Code"(Tumour Condition):
  if not Coalesce(Matches("Primary Site"(Tumour), 'C[0-9]{3}'), false) then null
  else Code {
    system: 'http://terminology.hl7.org/CodeSystem/icd-o-3',
    code: Substring("Primary Site"(Tumour), 0, 3) + '.' + Substring("Primary Site"(Tumour), 3, 1)
  }
define function "Histology"(Tumour Condition): "Registry Value"(Tumour, '2.8')
define function "Behavior"(Tumour Condition): "Registry Value"(Tumour, '2.9')
define function "Microscopic Confirmation Date"(Tumour Condition): "Registry Date"("Registry Value"(Tumour, '2.12'))
define function "Regional Nodes Examined"(Tumour Condition): "Registry Integer"("Registry Value"(Tumour, '2.14'))
define function "Clinical Stage Group"(Tumour Condition): "Registry Value"(Tumour, '3.7')
define function "Pathological Stage Group"(Tumour Condition): "Registry Value"(Tumour, '3.13')
define function "First Course Start Date"(Tumour Condition): "Registry Date"("Registry Value"(Tumour, '4.1'))
define function "Primary Site Surgery"(Tumour Condition): "Registry Integer"("Registry Value"(Tumour, '4.1.4'))
define function "Reporting Hospital"(Tumour Condition): "Registry Value"(Tumour, '1.1')
define function "Last Contact Or Death Date"(Tumour Condition): "Registry Date"("Registry Value"(Tumour, '5.3'))
define function "Vital Status"(Tumour Condition): "Registry Value"(Tumour, '5.4')

// ==========================================================================
// shared initial population
// ==========================================================================

define "Measurement Dates":
  Interval[date from start of "Measurement Period", date from end of "Measurement Period"]

// --------------------------------------------------------------------------
// Case assembly (收錄資料說明). Steps and decisions follow the case assembly
// page and reference/cohort.py step for step:
//   1 癌別 scope, 2 valid 2.5, 3 new diagnosis since 2024 and in the period,
//   4 complete duplicate key, 5 註1 de-duplication, then on the kept record only
//   6 class 1/2, 7 註3 cross-hospital, 8 第二點 died before treatment.
// Step 9 (第五點 outside-hospital data) depends on what the hospital could
// obtain, which no registry field records. The hospital supplies, per
// indicator, the tumours it excludes under that rule (parameters "Outside
// Data Excluded QI01/02/03"); they are removed from that indicator's
// denominator. Nothing is guessed here.
// --------------------------------------------------------------------------

// IP-SCOPE: 癌別「大腸癌」 = C18 except C18.1 (appendix), C19.9, C20.9.
define function "Is Colorectal Category"(Tumour Condition):
  Coalesce("Primary Site Code"(Tumour) in "Colorectal Category", false)

define "Patient Has National Id":
  exists (Patient.identifier I
    where I.system.value = 'http://www.moi.gov.tw' and "Trimmed"(I.value.value) is not null)

define function "Normalized Key"(Raw String):
  if "Trimmed"(Raw) is null then null
  else Upper("Trimmed"(Raw))

// Steps 1-4. IP-SCOPE, IP-DXDATE.
define "Assembly Candidates":
  "Primary Tumours" Tumour
    where "Is Colorectal Category"(Tumour)
      and "Date Of Initial Diagnosis"(Tumour) is not null
      and "Date Of Initial Diagnosis"(Tumour) on or after @2024-01-01
      and "Date Of Initial Diagnosis"(Tumour) in "Measurement Dates"
      and "Patient Has National Id"
      and "Normalized Key"("Reporting Hospital"(Tumour)) is not null

// 註1 same-day tie-break: more severe stage group, pathological (3.13) first,
// clinical (3.7) when 3.13 is not rankable; unrankable ranks lowest.
define "Stage Severity Order":
  { '0', '0A', '0IS',
    '1', '1A', '1A1', '1A2', '1A3', '1B', '1B1', '1B2', '1C', '1E', '1S',
    '2', '2A', '2A1', '2A2', '2B', '2BU', '2C', '2E',
    '3', '3A', '3A1', '3A2', '3B', '3C', '3C1', '3C2', '3D',
    '4', '4A', '4A1', '4A2', '4B', '4C' }

define function "Stage Rank"(Raw String):
  if Raw is null then -1
  else IndexOf("Stage Severity Order", Upper(Raw))

define function "Severity"(Tumour Condition):
  if "Stage Rank"("Pathological Stage Group"(Tumour)) >= 0 then "Stage Rank"("Pathological Stage Group"(Tumour))
  else "Stage Rank"("Clinical Stage Group"(Tumour))

// True when Other wins the 註1 comparison against Tumour: earlier diagnosis,
// or same day and more severe, or same day, same severity, smaller id.
define function "Beats"(Other Condition, Tumour Condition):
  "Date Of Initial Diagnosis"(Other) < "Date Of Initial Diagnosis"(Tumour)
    or ("Date Of Initial Diagnosis"(Other) = "Date Of Initial Diagnosis"(Tumour)
      and ("Severity"(Other) > "Severity"(Tumour)
        or ("Severity"(Other) = "Severity"(Tumour) and Other.id.value < Tumour.id.value)))

// IP-DUP, step 5: same patient (national id), same hospital (1.1), same 癌別.
// Every candidate here is colorectal, so the group is patient + hospital.
define function "Is Duplicate"(Tumour Condition):
  exists ("Assembly Candidates" Other
    where Other.id.value != Tumour.id.value
      and "Normalized Key"("Reporting Hospital"(Other)) = "Normalized Key"("Reporting Hospital"(Tumour))
      and "Beats"(Other, Tumour))

define "Representative Cases":
  "Assembly Candidates" Tumour where not "Is Duplicate"(Tumour)

// IP-CROSS, step 7.
define function "Cross Hospital Treatment"(Tumour Condition):
  Coalesce("Class Of Case"(Tumour) = '2', false)
    and Coalesce("Diagnosis Status"(Tumour) = '2', false)
    and Coalesce("Treatment Status"(Tumour) = '3', false)

// Case-insensitive on both sides.
define function "Is Dead"(Tumour Condition):
  "Vital Status"(Tumour) is not null
    and Lower("Vital Status"(Tumour)) in ("Vital Status Dead Codes" DeadCode return Lower(DeadCode))

// IP-DEATH, step 8: (a) 2.3.2 = 0; (b) dead, 4.1 = 00000000 and 2.3.2 != 4;
// (c) dead and 5.3 before 4.1. Death on the day treatment starts is treated.
define function "Died Before Treatment"(Tumour Condition):
  Coalesce("Treatment Status"(Tumour) = '0', false)
    or ("Is Dead"(Tumour)
      and ((Coalesce("Registry Value"(Tumour, '4.1') = '00000000', false)
            and not Coalesce("Treatment Status"(Tumour) = '4', false))
        or Coalesce("Last Contact Or Death Date"(Tumour) < "First Course Start Date"(Tumour), false)))

// IP-CLASS (step 6), IP-CROSS (step 7), IP-DEATH (step 8) on the kept record only.
define "Initial Population":
  "Representative Cases" Tumour
    where Coalesce("Class Of Case"(Tumour) in { '1', '2' }, false)
      and not "Cross Hospital Treatment"(Tumour)
      and not "Died Before Treatment"(Tumour)

// ==========================================================================
// crc-qi-01  惡性息肉 12 週內治癒性切除（醫院自行申報）
// ==========================================================================

// D1-POLYP: the tumour itself is coded as a confirmed malignant polyp (T1).
define function "Is Malignant Polyp"(Tumour Condition):
  Tumour.code in "Malignant Polyp"
    and exists (Tumour.verificationStatus.coding V
      where V.system.value = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'
        and V.code.value = 'confirmed')

define function "Is Current Finding Of"(Finding Observation, Tumour Condition):
  Finding.status in { 'final', 'amended', 'corrected' }
    and exists (Finding.focus F where "Points To"(F, 'Condition', Tumour.id))

// D1-FEATURE: only findings recorded for this tumour count. A: local code with
// valueBoolean (colonoscopy report). B, C, D: LOINC question + coded answer
// (pathology report); the criterion is met when the answer is in its "Met" set.
define function "Has High Risk Feature"(Tumour Condition):
  exists ([Observation: "Colonoscopy High Risk Feature"] A
    where "Is Current Finding Of"(A, Tumour) and Coalesce((A.value as FHIR.boolean).value, false))
  or exists ([Observation: "Margin Involvement"] B
    where "Is Current Finding Of"(B, Tumour) and (B.value as FHIR.CodeableConcept) in "Criterion B Met")
  or exists ([Observation: "Lymphovascular Invasion"] C
    where "Is Current Finding Of"(C, Tumour) and (C.value as FHIR.CodeableConcept) in "Criterion C Met")
  or exists ([Observation: "Histologic Grade"] D
    where "Is Current Finding Of"(D, Tumour) and (D.value as FHIR.CodeableConcept) in "Criterion D Met")

// D1-REPORT: the pathology report the tumour's diagnosis rests on
// (Condition.evidence.detail); the earliest such final report starts the clock.
define function "Pathology Report Date"(Tumour Condition):
  Min(
    [DiagnosticReport: "Malignant Polyp Pathology Report"] Report
      where Report.status in { 'final', 'amended', 'corrected' }
        and Report.issued is not null
        and exists (Tumour.evidence E
          where exists (E.detail D where "Points To"(D, 'DiagnosticReport', Report.id)))
      return date from Report.issued.value
  )

// IP-OUTSIDE: 第五點, hospital-supplied per indicator.
define function "Is Outside Excluded"(Tumour Condition, Excluded List<String>):
  if Excluded is null then false
  else Tumour.id.value in Excluded

define "Denominator 1":
  "Initial Population" Tumour
    where not "Is Outside Excluded"(Tumour, "Outside Data Excluded QI01")
      and "Is Malignant Polyp"(Tumour)
      and "Has High Risk Feature"(Tumour)
      and "Pathology Report Date"(Tumour) is not null

define function "Procedure Start Date"(Performed Choice<FHIR.dateTime, FHIR.Period, FHIR.string, FHIR.Age, FHIR.Range>):
  case
    when Performed is FHIR.dateTime then date from FHIRHelpers.ToDateTime(Performed as FHIR.dateTime)
    when Performed is FHIR.Period then date from start of FHIRHelpers.ToInterval(Performed as FHIR.Period)
    else null
  end

// N1-RESECT: a completed curative resection of this tumour within 12 weeks
// (84 days) of its pathology report.
define function "Resected Within 12 Weeks"(Tumour Condition):
  exists ([Procedure: "Curative Resection"] Resection
    let ResectionDate: "Procedure Start Date"(Resection.performed),
        ReportDate: "Pathology Report Date"(Tumour)
    where Resection.status = 'completed'
      and exists (Resection.reasonReference R where "Points To"(R, 'Condition', Tumour.id))
      and ResectionDate is not null
      and ResectionDate in Interval[ReportDate, ReportDate + 84 days])

define "Numerator 1":
  "Denominator 1" Tumour where "Resected Within 12 Weeks"(Tumour)

// ==========================================================================
// crc-qi-02  第 I–III 期結腸癌手術病人淋巴結檢查 ≥12 顆
// ==========================================================================

// D2-SITE (附件1：排除 Appendix C18.1)
define function "Is Colon Excluding Appendix"(Tumour Condition):
  Coalesce("Primary Site Code"(Tumour) in "Colon Excluding Appendix", false)

// D2-SURG, X2-POLYP
define function "Has Resection Surgery 30 To 90"(Tumour Condition):
  Coalesce("Primary Site Surgery"(Tumour) in Interval[30, 90], false)

// D2-PSTAGE
define function "Is Pathological Stage I To III"(Tumour Condition):
  Coalesce("Stage Leading Digit"("Pathological Stage Group"(Tumour)) in { '1', '2', '3' }, false)

define "Denominator 2":
  "Initial Population" Tumour
    where not "Is Outside Excluded"(Tumour, "Outside Data Excluded QI02")
      and "Is Colon Excluding Appendix"(Tumour)
      and "Has Resection Surgery 30 To 90"(Tumour)
      and "Is Pathological Stage I To III"(Tumour)

// X2-HIST: GIST, NETs and high grade dysplasia are outside the colon scope.
// Registry 2.8 holds the 4-digit histology without behavior, which is not a
// complete ICD-O-3 code, so this list stays a named expression rather than a
// ValueSet; tests/test_specification.py keeps it equal to the reference.
define "Special Histology":
  { '8935', '8936', '8153', '8240', '8241', '8242', '8246', '8249' }

define "Denominator 2 Exclusion":
  "Denominator 2" Tumour
    where Coalesce("Histology"(Tumour) in "Special Histology", false)
      or Coalesce("Behavior"(Tumour) = '2', false)

// N2-LN12
define "Numerator 2":
  "Denominator 2" Tumour
    where Coalesce("Regional Nodes Examined"(Tumour) in Interval[12, 90], false)

// ==========================================================================
// crc-qi-03  第 II、III 期直腸癌 6 週內開始治療
// ==========================================================================

// D3-SITE
define function "Is Rectosigmoid Or Rectum"(Tumour Condition):
  Coalesce("Primary Site Code"(Tumour) in "Rectosigmoid Or Rectum", false)

// D3-CSTAGE
define function "Is Clinical Stage II To III"(Tumour Condition):
  Coalesce("Stage Leading Digit"("Clinical Stage Group"(Tumour)) in { '2', '3' }, false)

// D3-CLASS: class 1 only, narrower than the shared class 1/2 population.
define "Denominator 3":
  "Initial Population" Tumour
    where not "Is Outside Excluded"(Tumour, "Outside Data Excluded QI03")
      and "Is Rectosigmoid Or Rectum"(Tumour)
      and Coalesce("Class Of Case"(Tumour) = '1', false)
      and "Is Clinical Stage II To III"(Tumour)

// N3-42D: no lower bound is stated in the official text, so none is applied.
define function "Days From Confirmation To First Course"(Tumour Condition):
  days between "Microscopic Confirmation Date"(Tumour) and "First Course Start Date"(Tumour)

define "Numerator 3":
  "Denominator 3" Tumour
    where Coalesce("Days From Confirmation To First Course"(Tumour) <= 42, false)
