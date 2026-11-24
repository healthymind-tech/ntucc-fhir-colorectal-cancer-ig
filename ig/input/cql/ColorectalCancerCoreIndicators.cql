/*
Colorectal cancer core indicators (衛生福利部國民健康署「115 年癌症診療核心測量指標」大腸癌 3 項).

Normative expression of mappings/crc-core-indicator-criteria.csv. Every define
below carries the criterion_id from that file; reference/crc_indicators.py is
the independent Python reference implementation of the same table, and the two
are checked against the same synthetic cases (tests/fixtures/synthetic-cases.json).

Indicators 2 and 3 are written directly on the cancer registry (TCR) long-form
fields named in the official text, read from CRCTCRDataItemObservation
(valueString keeps the raw registry value). Indicator 1 is "醫院自行申報":
criteria A and C are not in the registry, so it reads clinical source facts.

Cohort assembly is outside this library, by design (criteria IP-DUP, IP-DEATH):
the task layer removes in-hospital duplicate cases and patients who died before
treatment before the evaluation Group is built. The library assumes one primary
colorectal tumour per evaluated patient context.
*/

library ColorectalCancerCoreIndicators version '1.0.0'

using FHIR version '4.0.1'

include hl7.fhir.uv.cql.FHIRHelpers version '4.0.1' called FHIRHelpers

codesystem "CRC TCR Field": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/CodeSystem/crc-tcr-field'

code "Class Of Case Field": '2.3' from "CRC TCR Field" display '個案分類'
code "Diagnosis Status Field": 'CLASS-DX-STATUS' from "CRC TCR Field" display '診斷狀態分類'
code "Treatment Status Field": 'CLASS-TX-STATUS' from "CRC TCR Field" display '治療狀態分類'
code "Date Of Initial Diagnosis Field": '2.5' from "CRC TCR Field" display '最初診斷日期'
code "Primary Site Field": '2.6' from "CRC TCR Field" display '原發部位'
code "Histology Field": '2.8' from "CRC TCR Field" display '組織型態'
code "Behavior Field": '2.9' from "CRC TCR Field" display '性態碼'
code "Microscopic Confirmation Date Field": '2.12' from "CRC TCR Field" display '首次顯微鏡檢證實日期'
code "Regional Nodes Examined Field": '2.14' from "CRC TCR Field" display '區域淋巴結檢查數目'
code "Clinical Stage Group Field": '3.7' from "CRC TCR Field" display '臨床期別組合'
code "Pathological Stage Group Field": '3.13' from "CRC TCR Field" display '病理期別組合'
code "First Course Start Date Field": '4.1' from "CRC TCR Field" display '首次療程開始日期'
code "Primary Site Surgery Field": '4.1.4' from "CRC TCR Field" display '申報醫院原發部位手術方式'

valueset "Malignant Polyp": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-malignant-polyp'
valueset "Malignant Polyp Pathology Report": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-malignant-polyp-pathology-report'
valueset "Malignant Polyp High Risk Feature": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-malignant-polyp-high-risk-feature'
valueset "Curative Resection": 'https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-curative-resection'

parameter "Measurement Period" Interval<DateTime>

context Patient

// ==========================================================================
// registry value access
// ==========================================================================

define function "Registry Value"(Items List<Observation>):
  First(
    Items Item
      where Item.status in { 'final', 'amended', 'corrected' }
      return (Item.value as FHIR.string).value
  )

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

define "Class Of Case":
  "Registry Value"([Observation: "Class Of Case Field"])

define "Diagnosis Status":
  "Registry Value"([Observation: "Diagnosis Status Field"])

define "Treatment Status":
  "Registry Value"([Observation: "Treatment Status Field"])

define "Date Of Initial Diagnosis":
  "Registry Date"("Registry Value"([Observation: "Date Of Initial Diagnosis Field"]))

define "Primary Site":
  "Normalized Site"("Registry Value"([Observation: "Primary Site Field"]))

define "Histology":
  "Registry Value"([Observation: "Histology Field"])

define "Behavior":
  "Registry Value"([Observation: "Behavior Field"])

define "Microscopic Confirmation Date":
  "Registry Date"("Registry Value"([Observation: "Microscopic Confirmation Date Field"]))

define "Regional Nodes Examined":
  "Registry Integer"("Registry Value"([Observation: "Regional Nodes Examined Field"]))

define "Clinical Stage Group":
  "Registry Value"([Observation: "Clinical Stage Group Field"])

define "Pathological Stage Group":
  "Registry Value"([Observation: "Pathological Stage Group Field"])

define "First Course Start Date":
  "Registry Date"("Registry Value"([Observation: "First Course Start Date Field"]))

define "Primary Site Surgery":
  "Registry Integer"("Registry Value"([Observation: "Primary Site Surgery Field"]))

// ==========================================================================
// shared initial population
// ==========================================================================

define "Measurement Dates":
  Interval[date from start of "Measurement Period", date from end of "Measurement Period"]

// IP-CROSS
define "Cross Hospital Treatment":
  Coalesce("Class Of Case" = '2', false)
    and Coalesce("Diagnosis Status" = '2', false)
    and Coalesce("Treatment Status" = '3', false)

// IP-DXDATE, IP-CLASS, IP-CROSS
define "Initial Population":
  "Date Of Initial Diagnosis" is not null
    and "Date Of Initial Diagnosis" on or after @2024-01-01
    and "Date Of Initial Diagnosis" in "Measurement Dates"
    and Coalesce("Class Of Case" in { '1', '2' }, false)
    and not "Cross Hospital Treatment"

// ==========================================================================
// crc-qi-01  惡性息肉 12 週內治癒性切除（醫院自行申報）
// ==========================================================================

// D1-POLYP
define "Has Malignant Polyp":
  exists ([Condition: "Malignant Polyp"] Polyp
    where exists (Polyp.verificationStatus.coding Coding
      where Coding.system.value = 'http://terminology.hl7.org/CodeSystem/condition-ver-status'
        and Coding.code.value = 'confirmed'))

// D1-FEATURE
define "Has High Risk Feature":
  exists ([Observation: "Malignant Polyp High Risk Feature"] Feature
    where Feature.status in { 'final', 'amended', 'corrected' }
      and Coalesce((Feature.value as FHIR.boolean).value, false))

// D1-REPORT
define "Malignant Polyp Pathology Report Date":
  Min(
    [DiagnosticReport: "Malignant Polyp Pathology Report"] Report
      where Report.status in { 'final', 'amended', 'corrected' }
        and Report.issued is not null
      return date from Report.issued.value
  )

define "Denominator 1":
  "Initial Population"
    and "Has Malignant Polyp"
    and "Has High Risk Feature"
    and "Malignant Polyp Pathology Report Date" is not null

define function "Procedure Start Date"(Performed Choice<FHIR.dateTime, FHIR.Period, FHIR.string, FHIR.Age, FHIR.Range>):
  case
    when Performed is FHIR.dateTime then date from FHIRHelpers.ToDateTime(Performed as FHIR.dateTime)
    when Performed is FHIR.Period then date from start of FHIRHelpers.ToInterval(Performed as FHIR.Period)
    else null
  end

// N1-RESECT: 12 weeks = 84 days, counted from the pathology report date.
define "Numerator 1":
  exists ([Procedure: "Curative Resection"] Resection
    let ResectionDate: "Procedure Start Date"(Resection.performed)
    where Resection.status = 'completed'
      and ResectionDate is not null
      and ResectionDate in Interval["Malignant Polyp Pathology Report Date", "Malignant Polyp Pathology Report Date" + 84 days])

// ==========================================================================
// crc-qi-02  第 I–III 期結腸癌手術病人淋巴結檢查 ≥12 顆
// ==========================================================================

// D2-SITE (附件1：排除 Appendix C18.1)
define "Is Colon Excluding Appendix":
  Coalesce("Primary Site" in { 'C180', 'C182', 'C183', 'C184', 'C185', 'C186', 'C187', 'C188', 'C189' }, false)

// D2-SURG, X2-POLYP
define "Has Resection Surgery 30 To 90":
  Coalesce("Primary Site Surgery" in Interval[30, 90], false)

// D2-PSTAGE
define "Is Pathological Stage I To III":
  Coalesce("Stage Leading Digit"("Pathological Stage Group") in { '1', '2', '3' }, false)

define "Denominator 2":
  "Initial Population"
    and "Is Colon Excluding Appendix"
    and "Has Resection Surgery 30 To 90"
    and "Is Pathological Stage I To III"

// X2-HIST: GIST, NETs and high grade dysplasia are outside the colon scope.
define "Denominator 2 Exclusion":
  Coalesce("Histology" in { '8935', '8936', '8153', '8240', '8241', '8242', '8246', '8249' }, false)
    or Coalesce("Behavior" = '2', false)

// N2-LN12
define "Numerator 2":
  Coalesce("Regional Nodes Examined" in Interval[12, 90], false)

// ==========================================================================
// crc-qi-03  第 II、III 期直腸癌 6 週內開始治療
// ==========================================================================

// D3-SITE
define "Is Rectosigmoid Or Rectum":
  Coalesce("Primary Site" in { 'C199', 'C209' }, false)

// D3-CSTAGE
define "Is Clinical Stage II To III":
  Coalesce("Stage Leading Digit"("Clinical Stage Group") in { '2', '3' }, false)

// D3-CLASS: class 1 only, narrower than the shared class 1/2 population.
define "Denominator 3":
  "Initial Population"
    and "Is Rectosigmoid Or Rectum"
    and Coalesce("Class Of Case" = '1', false)
    and "Is Clinical Stage II To III"

// N3-42D: no lower bound is stated in the official text, so none is applied.
define "Days From Confirmation To First Course":
  days between "Microscopic Confirmation Date" and "First Course Start Date"

define "Numerator 3":
  Coalesce("Days From Confirmation To First Course" <= 42, false)
