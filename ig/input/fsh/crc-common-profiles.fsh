// 大腸癌共同層：沿用範例乳癌 IG 的分層方式。
// 共同層只放跨 Task 可重用的最小限制；指標專屬的規則放在 Measure／CQL。

Profile: ColorectalCancerPatient
Parent: $TWCorePatient
Id: colorectal-cancer-patient
Title: "Colorectal Cancer Patient - Draft"
Description: "大腸癌各 Task 共用之病人 Profile，結構以 TW Core Patient 為基礎。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* identifier MS
* gender MS
* birthDate MS
* deceased[x] MS

Profile: ColorectalCancerPrimaryCondition
Parent: Condition
Id: colorectal-cancer-primary-condition
Title: "Colorectal Cancer Primary Condition - Draft"
Description: "一顆原發大腸直腸癌。癌登摘錄（TCR Data Item Observation）以 focus 指向本 Condition，讓同一病人多原發時仍能分辨每筆欄位屬於哪一顆腫瘤。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* clinicalStatus MS
* verificationStatus MS
* code 1..1 MS
* subject 1..1 MS
* subject only Reference(ColorectalCancerPatient)
* bodySite MS
* recordedDate MS

Profile: CRCTCRDataItemObservation
Parent: Observation
Id: crc-tcr-data-item-observation
Title: "大腸癌癌登長表欄位 Observation"
Description: "一個癌登長表欄位的申報值。值以 valueString 保存原始字串（例如日期 20250312、手術方式 30、期別 3B、未知 99999999），轉換可逆，不推論臨床語意。核心指標的 CQL 直接讀取本 Profile。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* status MS
* status from CRCTCRObservationStatusVS (required)
* code 1..1 MS
* code from CRCTCRFieldValueSet (required)
* subject 1..1 MS
* subject only Reference(ColorectalCancerPatient)
* focus 1..1 MS
* focus only Reference(ColorectalCancerPrimaryCondition)
* focus ^short = "此欄位所屬的原發腫瘤"
* value[x] 1..1 MS
* value[x] only string
* derivedFrom MS
* derivedFrom ^short = "摘錄來源文件（病理報告、手術紀錄等）"

ValueSet: CRCTCRObservationStatusVS
Id: crc-tcr-observation-status
Title: "癌登欄位 Observation 可用狀態"
Description: "已定稿的申報值才可被指標計算讀取。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* http://hl7.org/fhir/observation-status#final
* http://hl7.org/fhir/observation-status#amended
* http://hl7.org/fhir/observation-status#corrected

// ---------------------------------------------------------------------------
// 指標 1（惡性息肉，醫院自行申報）所需之臨床來源事實
// ---------------------------------------------------------------------------

Profile: CRCMalignantPolypCondition
Parent: Condition
Id: crc-malignant-polyp-condition
Title: "Malignant Polyp (T1) Condition"
Description: "切除之息肉中出現 T1 腺癌（Tis 不屬之）。指標 1 分母的對象。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* verificationStatus 1..1 MS
* code 1..1 MS
* code from CRCMalignantPolypVS (required)
* subject 1..1 MS
* subject only Reference(ColorectalCancerPatient)

Profile: CRCMalignantPolypPathologyReport
Parent: DiagnosticReport
Id: crc-malignant-polyp-pathology-report
Title: "惡性息肉病理報告"
Description: "指標 1 的計時起點。issued 為病理報告日期；12 週以此日起算。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* status MS
* code 1..1 MS
* code from CRCMalignantPolypPathologyReportVS (required)
* category 1..* MS
* category ^slicing.discriminator.type = #pattern
* category ^slicing.discriminator.path = "$this"
* category ^slicing.rules = #open
* category contains pathology 1..1 MS
* category[pathology] = http://terminology.hl7.org/CodeSystem/v2-0074#SP
* subject 1..1 MS
* subject only Reference(ColorectalCancerPatient)
* issued 1..1 MS
* result MS
* result only Reference(CRCMalignantPolypHighRiskFeature)

Profile: CRCMalignantPolypHighRiskFeature
Parent: Observation
Id: crc-malignant-polyp-high-risk-feature
Title: "惡性息肉高風險條件（A–D）"
Description: "條件 A 來自大腸鏡檢報告；B、C、D 來自病理報告。valueBoolean = true 表示報告記載該條件成立；false 表示報告明確記載不成立。未記載者不建立本 Observation。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* status MS
* code 1..1 MS
* code from CRCMalignantPolypHighRiskFeatureVS (required)
* subject 1..1 MS
* subject only Reference(ColorectalCancerPatient)
* value[x] 1..1 MS
* value[x] only boolean
* derivedFrom MS

Profile: CRCCurativeResectionProcedure
Parent: Procedure
Id: crc-curative-resection-procedure
Title: "惡性息肉後續治癒性切除"
Description: "指標 1 分子之治癒性切除。performed[x] 為手術日期。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* status MS
* code 1..1 MS
* code from CRCCurativeResectionVS (required)
* subject 1..1 MS
* subject only Reference(ColorectalCancerPatient)
* performed[x] 1..1 MS
* performed[x] only dateTime or Period
