// 說明檔第五點「外院資料」：醫院對某顆腫瘤、某項指標宣告排除時，以一筆
// CRCOutsideDataExclusion 記錄。以資料（而非 CQL 參數）表達，可被驗證、稽核，
// 也不依賴 R4 $evaluate-measure 沒有的參數輸入。

CodeSystem: CRCOutsideDataCodeSystem
Id: crc-outside-data
Title: "大腸癌核心指標第五點外院資料代碼"
Description: "第五點外院資料排除：排除哪一項指標（Observation.code）與排除理由（Observation.valueCodeableConcept）。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* ^caseSensitive = true
* ^content = #complete
* #excluded-qi01 "第五點：自指標 1 排除" "此腫瘤依第五點自指標 1（malignant polyp 治癒性切除）排除。"
* #excluded-qi02 "第五點：自指標 2 排除" "此腫瘤依第五點自指標 2（結腸癌淋巴結檢查）排除。"
* #excluded-qi03 "第五點：自指標 3 排除" "此腫瘤依第五點自指標 3（直腸癌首次療程等待）排除。"
* #both-outside "分子與分母資料皆在外院" "第五點 1：分子分母資料均在外院。"
* #numerator-outside-not-obtained "分子資料在外院且無法取得" "第五點 2：分子資料在外院且無法取得。"

ValueSet: CRCOutsideDataStatusVS
Id: crc-outside-data-status
Title: "第五點宣告的狀態"
Description: "final、amended、corrected 為有效宣告；entered-in-error 用於撤回誤植的宣告（CQL 不採用）。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* http://hl7.org/fhir/observation-status#final
* http://hl7.org/fhir/observation-status#amended
* http://hl7.org/fhir/observation-status#corrected
* http://hl7.org/fhir/observation-status#entered-in-error

ValueSet: CRCOutsideDataIndicatorVS
Id: crc-outside-data-indicator
Title: "第五點排除的指標"
Description: "CRCOutsideDataExclusion.code：排除的指標。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* CRCOutsideDataCodeSystem#excluded-qi01
* CRCOutsideDataCodeSystem#excluded-qi02
* CRCOutsideDataCodeSystem#excluded-qi03

ValueSet: CRCOutsideDataReasonVS
Id: crc-outside-data-reason
Title: "第五點排除理由"
Description: "CRCOutsideDataExclusion.valueCodeableConcept：第五點 1 或 2。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* CRCOutsideDataCodeSystem#both-outside
* CRCOutsideDataCodeSystem#numerator-outside-not-obtained

Profile: CRCOutsideDataExclusion
Parent: Observation
Id: crc-outside-data-exclusion
Title: "大腸癌第五點外院資料排除"
Description: "醫院依說明檔第五點，宣告某顆原發腫瘤自某一項指標排除（分子分母資料皆在外院，或分子資料在外院且無法取得）。每顆腫瘤、每項指標一筆。CQL 只採用 status 為 final、amended、corrected，subject 為該病人，focus 恰為一顆腫瘤，且 value 為第五點 1 或 2 者；以 entered-in-error 撤回。與 CRCTCRDataItemObservation 相同，繼承 FHIR R4 Observation 而非 TW Core：這是醫院的管理性宣告，不是臨床結果。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* status MS
* status from CRCOutsideDataStatusVS (required)
* code 1..1 MS
* code from CRCOutsideDataIndicatorVS (required)
* obeys crc-ode-one-indicator and crc-ode-one-reason
* code ^short = "排除的指標"
* subject 1..1 MS
* subject only Reference(ColorectalCancerPatient)
* focus 1..1 MS
* focus only Reference(ColorectalCancerPrimaryCondition)
* focus ^short = "被排除的原發腫瘤"
* value[x] 1..1 MS
* value[x] only CodeableConcept
* valueCodeableConcept from CRCOutsideDataReasonVS (required)
* valueCodeableConcept ^short = "第五點 1 或 2"
* issued 1..1 MS
* issued ^short = "醫院作出此宣告的時間"
* note MS
* note ^short = "外院名稱、無法取得的原因等稽核說明"

Invariant: crc-ode-one-indicator
Description: "一筆宣告只針對一項指標：code 恰有一個 coding 屬於 crc-outside-data-indicator。"
Severity: #error
Expression: "code.coding.where(memberOf('https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-outside-data-indicator')).count() = 1"

Invariant: crc-ode-one-reason
Description: "理由只能有一個：value 恰有一個 coding 屬於 crc-outside-data-reason。"
Severity: #error
Expression: "value.ofType(CodeableConcept).coding.where(memberOf('https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/ValueSet/crc-outside-data-reason')).count() = 1"

Instance: CRCOutsideDataExclusionExample
InstanceOf: CRCOutsideDataExclusion
Usage: #example
Title: "合成第五點外院資料排除"
Description: "完全合成範例：結腸癌個案的淋巴結檢查在外院完成且報告無法取得，自指標 2 排除。"
* id = "crc-outside-data-colon-qi02"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCOutsideDataCodeSystem#excluded-qi02 "第五點：自指標 2 排除"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueCodeableConcept = CRCOutsideDataCodeSystem#numerator-outside-not-obtained "分子資料在外院且無法取得"
* issued = "2026-01-15T10:00:00+08:00"
* note.text = "合成範例：手術於外院施行，病理報告無法取得。"
