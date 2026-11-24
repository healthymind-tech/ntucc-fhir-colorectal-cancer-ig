// 大腸癌共同層：沿用範例乳癌 IG 的分層方式。
// 共同層只放跨 Task 可重用的最小限制；指標專屬的規則放在 Measure／CQL。
//
// 臨床資源一律繼承 TW Core 1.0.0 對應的 Profile：符合本 IG Profile 的實例，同時
// 也符合 TW Core。反方向不成立——本 IG 另要求本地代碼與病理 category，一般的
// TW Core 資料須補上這些內容才符合本 IG。唯一例外是 CRCTCRDataItemObservation。

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
Parent: $TWCoreCondition
Id: colorectal-cancer-primary-condition
Title: "Colorectal Cancer Primary Condition - Draft"
Description: "一顆原發大腸直腸癌，繼承 TW Core Condition。癌登摘錄（TCR Data Item Observation）以 focus 指向本 Condition，讓同一病人多原發時仍能分辨每筆欄位屬於哪一顆腫瘤。診斷碼使用國際 ICD-10-CM（http://hl7.org/fhir/sid/icd-10-cm）：TW Core 1.0.0 的 ICD-10-CM 台灣版 CodeSystem 在套件中僅收 11 個代碼，無法驗證大腸癌代碼；TW Core 的 code.coding slicing 為 open，國際 ICD-10-CM 為允許的寫法。接收端應同時接受國際 ICD-10-CM 與 TW Core 的 icd-10-cm-*-tw 代碼系統。癌登的 ICD-O-3 部位與組織型態另見 CRCTCRDataItemObservation。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* clinicalStatus MS
* verificationStatus MS
* code 1..1 MS
* subject 1..1 MS
* subject only Reference(ColorectalCancerPatient)
* bodySite MS
* bodySite.coding ^slicing.discriminator.type = #value
* bodySite.coding ^slicing.discriminator.path = "system"
* bodySite.coding ^slicing.rules = #open
* bodySite.coding contains icdo3Topography 0..1 MS
* bodySite.coding[icdo3Topography] ^short = "ICD-O-3 topography（例如 C18.7），由癌登 2.6 原發部位轉換"
* bodySite.coding[icdo3Topography].system = "http://terminology.hl7.org/CodeSystem/icd-o-3" (exactly)
* bodySite.coding[icdo3Topography].code 1..1
* bodySite.coding[icdo3Topography].code obeys crc-icdo3-topography-format
* extension contains CRCHistologyMorphologyBehavior named histologyMorphologyBehavior 0..1 MS
* recordedDate MS

// 刻意不繼承 TW Core。結構上可行：TW Core Observation Clinical Result 的
// effective[x] 是 0..1，category 的 binding 只是 preferred，加上本地類別代碼就能
// 通過驗證。但它的語意是「臨床檢驗檢查結果」，而「癌登長表某欄位的申報值」不是
// 臨床結果；標成 Clinical Result 會讓接收端誤判資料性質，也帶不來實際的 TW Core
// 互通效益（沒有 TW Core 系統會依「臨床結果」去解讀癌登欄位）。其他 TW Core
// Observation Profile 不是固定特定代碼（如職業、性傾向），就是要求 effective 1..1
// 與臨床類別（如 Simple Observation），都不適用。
Profile: CRCTCRDataItemObservation
Parent: Observation
Id: crc-tcr-data-item-observation
Title: "大腸癌癌登長表欄位 Observation"
Description: "一個癌登長表欄位的申報值。值以 valueString 保存原始字串（例如日期 20250312、手術方式 30、期別 3B、未知 99999999），轉換可逆，不推論臨床語意。核心指標的 CQL 直接讀取本 Profile。本 Profile 刻意繼承 FHIR R4 Observation 而非 TW Core：TW Core Observation Clinical Result 在結構上可以容納，但其語意為臨床檢驗檢查結果，癌登欄位值不是臨床結果，套用會誤導接收端，也沒有實際互通效益。"
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
* issued 1..1 MS
* issued ^short = "此申報值確定的時間"
* issued ^definition = "同一顆腫瘤的同一欄位有多筆申報值（例如 final 之後又有 amended）時，以 issued 最晚者為現行值；issued 相同時以 Observation.id 排序取最後一筆，並應視為資料品質問題。"
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
Parent: ColorectalCancerPrimaryCondition
Id: crc-malignant-polyp-condition
Title: "Malignant Polyp (T1) Condition"
Description: "切除之息肉中出現 T1 腺癌（Tis 不屬之）的原發腫瘤，是指標 1 的計算單位。它本身就是一顆已登記的原發大腸直腸癌（繼承 ColorectalCancerPrimaryCondition），癌登欄位以 focus 指向它；另以 code 的 malignantPolyp coding 標示為惡性息肉，並以 evidence 連到確立診斷的病理報告。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* verificationStatus 1..1 MS
* code.coding contains malignantPolyp 1..1 MS
* code.coding[malignantPolyp] = CRCIndicatorConceptCodeSystem#malignant-polyp-t1
* evidence 1..* MS
* evidence.detail 1..* MS
* evidence.detail only Reference(CRCMalignantPolypPathologyReport)
* evidence.detail ^short = "確立惡性息肉診斷的病理報告；指標 1 的 12 週由此報告起算"

Profile: CRCMalignantPolypPathologyReport
Parent: $TWCoreDiagnosticReport
Id: crc-malignant-polyp-pathology-report
Title: "惡性息肉病理報告"
Description: "指標 1 的計時起點，繼承 TW Core DiagnosticReport。issued 為病理報告日期；12 週以此日起算。result 指向病理報告記載的條件 B、C、D。"
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
* result only Reference(CRCPathologyHighRiskFeature)

// 條件 B、C、D 記載於病理報告。TW Core DiagnosticReport.result 只能指向 TW Core
// 檢驗結果 Observation，因此本 Profile 繼承 Observation-laboratoryResult-twcore
// （category = laboratory；病理判讀在 FHIR 中屬檢驗結果）。
Profile: CRCPathologyHighRiskFeature
Parent: $TWCoreLabResult
Id: crc-pathology-high-risk-feature
Title: "惡性息肉病理高風險條件（B、C、D）"
Description: "病理報告記載的惡性息肉高風險條件：B 切緣陽性、C 淋巴或靜脈侵犯、D 第 3 級或分化不全。valueBoolean = true 表示報告記載條件成立；false 表示報告明確記載不成立；未記載者不建立本 Observation。effective[x] 為檢體採檢或病理判讀日期。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* status MS
* code 1..1 MS
* code from CRCPathologyHighRiskFeatureVS (required)
* subject 1..1 MS
* subject only Reference(ColorectalCancerPatient)
* focus 1..1 MS
* focus only Reference(CRCMalignantPolypCondition)
* focus ^short = "此條件所屬的惡性息肉（原發腫瘤）"
* value[x] 1..1 MS
* value[x] only boolean

// 條件 A 記載於大腸鏡檢報告，屬於處置結果（category = procedure），不是檢驗結果。
Profile: CRCColonoscopyHighRiskFeature
Parent: $TWCoreClinicalResult
Id: crc-colonoscopy-high-risk-feature
Title: "惡性息肉大腸鏡高風險條件（A）"
Description: "大腸鏡檢報告記載的條件 A：息肉未完全被切除。valueBoolean 語意同 CRCPathologyHighRiskFeature。effective[x] 為大腸鏡檢日期。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* status MS
* category[twcore] 1..1
* category[twcore] = $ObservationCategory#procedure
* code 1..1 MS
* code from CRCColonoscopyHighRiskFeatureVS (required)
* subject 1..1 MS
* subject only Reference(ColorectalCancerPatient)
* focus 1..1 MS
* focus only Reference(CRCMalignantPolypCondition)
* focus ^short = "此條件所屬的惡性息肉（原發腫瘤）"
* effective[x] 1..1 MS
* value[x] 1..1 MS
* value[x] only boolean

Profile: CRCCurativeResectionProcedure
Parent: $TWCoreProcedure
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
* reasonReference 1..* MS
* reasonReference only Reference(CRCMalignantPolypCondition)
* reasonReference ^short = "此切除所治療的惡性息肉（原發腫瘤）"
* performed[x] 1..1 MS
* performed[x] only dateTime or Period
