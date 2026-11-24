/*
Colorectal cancer core indicators (衛生福利部國民健康署「115 年癌症診療核心測量指標」大腸癌 3 項).

Normative expression of mappings/crc-core-indicator-criteria.csv. Every define
below carries the criterion_id from that file; reference/crc_indicators.py is
the independent Python reference implementation of the same table, and the two
are checked against the same synthetic cases (tests/fixtures/synthetic-cases.json).

UNIT OF MEASUREMENT: the indicators count registry cases, i.e. primary tumours,
not patients. The population basis is Condition: every population define returns
the list of primary-tumour Conditions of the patient that belong to it. A
patient with synchronous colon and rectal primaries contributes two tumours,
each evaluated on its own registry fields.

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
valueset "Malignant Polyp High Risk Feature": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-malignant-polyp-high-risk-feature'
valueset "Curative Resection": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-curative-resection'

parameter "Measurement Period" Interval<DateTime>

context Patient

// ==========================================================================
// references and registry value access
// ==========================================================================

// True when a (relative or absolute) reference points at the given resource.
define function "Points To"(Ref FHIR.Reference, ResourceType String, ResourceId String):
  Ref.reference.value = ResourceType + '/' + ResourceId
    or EndsWith(Ref.reference.value, '/' + ResourceType + '/' + ResourceId)

define "TCR Field System":
  'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/CodeSystem/crc-tcr-field'

define "Registry Items":
  [Observation] Item
    where Item.status in { 'final', 'amended', 'corrected' }
      and exists (Item.code.coding C where C.system.value = "TCR Field System")

// IP-UNIT: a primary tumour is a Condition that registry fields are abstracted for.
define "Primary Tumours":
  [Condition] Tumour
    where exists ("Registry Items" Item
      where exists (Item.focus F where "Points To"(F, 'Condition', Tumour.id)))

define function "Field Versions"(Tumour Condition, Field String):
  "Registry Items" Item
    where exists (Item.code.coding C where C.code.value = Field)
      and exists (Item.focus F where "Points To"(F, 'Condition', Tumour.id))
    // id must be the string value: sorting the FHIR.id element itself compares
    // objects, which the JavaScript engine orders arbitrarily.
    return Tuple { issued: Item.issued.value, id: Item.id.value, raw: (Item.value as FHIR.string).value }

// IP-CURRENT: the current value of one registry field of one tumour: latest issued wins;
// equal issued times fall back to the Observation id so the choice is stable.
define function "Registry Value"(Tumour Condition, Field String):
  Last(
    (("Field Versions"(Tumour, Field)) Candidate
      where Candidate.issued = Max(("Field Versions"(Tumour, Field)) Other return Other.issued)
    ) Latest
      sort by id
  ).raw

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

// ICD-O-3 topography is compared without the dot, so C18.7 and C187 match.
define function "Normalized Site"(Raw String):
  if Raw is null then null
  else Upper(ReplaceMatches(Raw, '\\.', ''))

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
define function "Histology"(Tumour Condition): "Registry Value"(Tumour, '2.8')
define function "Behavior"(Tumour Condition): "Registry Value"(Tumour, '2.9')
define function "Microscopic Confirmation Date"(Tumour Condition): "Registry Date"("Registry Value"(Tumour, '2.12'))
define function "Regional Nodes Examined"(Tumour Condition): "Registry Integer"("Registry Value"(Tumour, '2.14'))
define function "Clinical Stage Group"(Tumour Condition): "Registry Value"(Tumour, '3.7')
define function "Pathological Stage Group"(Tumour Condition): "Registry Value"(Tumour, '3.13')
define function "First Course Start Date"(Tumour Condition): "Registry Date"("Registry Value"(Tumour, '4.1'))
define function "Primary Site Surgery"(Tumour Condition): "Registry Integer"("Registry Value"(Tumour, '4.1.4'))

// ==========================================================================
// shared initial population
// ==========================================================================

define "Measurement Dates":
  Interval[date from start of "Measurement Period", date from end of "Measurement Period"]

// IP-CROSS
define function "Cross Hospital Treatment"(Tumour Condition):
  Coalesce("Class Of Case"(Tumour) = '2', false)
    and Coalesce("Diagnosis Status"(Tumour) = '2', false)
    and Coalesce("Treatment Status"(Tumour) = '3', false)

// IP-DXDATE, IP-CLASS, IP-CROSS
define function "Is Eligible Case"(Tumour Condition):
  "Date Of Initial Diagnosis"(Tumour) is not null
    and "Date Of Initial Diagnosis"(Tumour) on or after @2024-01-01
    and "Date Of Initial Diagnosis"(Tumour) in "Measurement Dates"
    and Coalesce("Class Of Case"(Tumour) in { '1', '2' }, false)
    and not "Cross Hospital Treatment"(Tumour)

define "Initial Population":
  "Primary Tumours" Tumour where "Is Eligible Case"(Tumour)

// ==========================================================================
// crc-qi-01  惡性息肉 12 週內治癒性切除（醫院自行申報）
// ==========================================================================

// D1-POLYP: the tumour itself is coded as a confirmed malignant polyp (T1).
define function "Is Malignant Polyp"(Tumour Condition):
  Tumour.code in "Malignant Polyp"
    and exists (Tumour.verificationStatus.coding V
      where V.system.value = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'
        and V.code.value = 'confirmed')

// D1-FEATURE: only features recorded for this tumour count.
define function "Has High Risk Feature"(Tumour Condition):
  exists ([Observation: "Malignant Polyp High Risk Feature"] Feature
    where Feature.status in { 'final', 'amended', 'corrected' }
      and exists (Feature.focus F where "Points To"(F, 'Condition', Tumour.id))
      and Coalesce((Feature.value as FHIR.boolean).value, false))

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

define "Denominator 1":
  "Initial Population" Tumour
    where "Is Malignant Polyp"(Tumour)
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
  Coalesce("Primary Site"(Tumour) in { 'C180', 'C182', 'C183', 'C184', 'C185', 'C186', 'C187', 'C188', 'C189' }, false)

// D2-SURG, X2-POLYP
define function "Has Resection Surgery 30 To 90"(Tumour Condition):
  Coalesce("Primary Site Surgery"(Tumour) in Interval[30, 90], false)

// D2-PSTAGE
define function "Is Pathological Stage I To III"(Tumour Condition):
  Coalesce("Stage Leading Digit"("Pathological Stage Group"(Tumour)) in { '1', '2', '3' }, false)

define "Denominator 2":
  "Initial Population" Tumour
    where "Is Colon Excluding Appendix"(Tumour)
      and "Has Resection Surgery 30 To 90"(Tumour)
      and "Is Pathological Stage I To III"(Tumour)

// X2-HIST: GIST, NETs and high grade dysplasia are outside the colon scope.
define "Denominator 2 Exclusion":
  "Denominator 2" Tumour
    where Coalesce("Histology"(Tumour) in { '8935', '8936', '8153', '8240', '8241', '8242', '8246', '8249' }, false)
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
  Coalesce("Primary Site"(Tumour) in { 'C199', 'C209' }, false)

// D3-CSTAGE
define function "Is Clinical Stage II To III"(Tumour Condition):
  Coalesce("Stage Leading Digit"("Clinical Stage Group"(Tumour)) in { '2', '3' }, false)

// D3-CLASS: class 1 only, narrower than the shared class 1/2 population.
define "Denominator 3":
  "Initial Population" Tumour
    where "Is Rectosigmoid Or Rectum"(Tumour)
      and Coalesce("Class Of Case"(Tumour) = '1', false)
      and "Is Clinical Stage II To III"(Tumour)

// N3-42D: no lower bound is stated in the official text, so none is applied.
define function "Days From Confirmation To First Course"(Tumour Condition):
  days between "Microscopic Confirmation Date"(Tumour) and "First Course Start Date"(Tumour)

define "Numerator 3":
  "Denominator 3" Tumour
    where Coalesce("Days From Confirmation To First Course"(Tumour) <= 42, false)
