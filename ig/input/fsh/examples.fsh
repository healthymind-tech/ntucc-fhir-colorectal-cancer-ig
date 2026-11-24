// 完全合成範例：不代表任何真實病人，不可用於臨床或申報。

RuleSet: SyntheticTag
* meta.tag = https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/CodeSystem/fixture-tag#synthetic

Instance: CRCPatientRectumExample
InstanceOf: ColorectalCancerPatient
Usage: #example
Title: "合成病人－直腸癌"
Description: "完全合成範例。"
* id = "crc-patient-rectum"
* language = #zh-TW
* identifier[idCardNumber].type.coding.system = "http://terminology.hl7.org/CodeSystem/v2-0203"
* identifier[idCardNumber].type.coding.code = #NNxxx
* identifier[idCardNumber].system = "http://www.moi.gov.tw"
* identifier[idCardNumber].value = "Z000000001"
* gender = #male
* birthDate = "1962-05-01"

Instance: CRCConditionRectumExample
InstanceOf: ColorectalCancerPrimaryCondition
Usage: #example
Title: "合成原發直腸癌"
Description: "完全合成範例。"
* id = "crc-condition-rectum"
* language = #zh-TW
* clinicalStatus = http://terminology.hl7.org/CodeSystem/condition-clinical#active
* verificationStatus = http://terminology.hl7.org/CodeSystem/condition-ver-status#confirmed
* code = http://hl7.org/fhir/sid/icd-10-cm#C20 "Malignant neoplasm of rectum"
* subject = Reference(CRCPatientRectumExample)
* recordedDate = "2025-01-10"

Instance: CRCPatientColonExample
InstanceOf: ColorectalCancerPatient
Usage: #example
Title: "合成病人－結腸癌"
Description: "完全合成範例。"
* id = "crc-patient-colon"
* language = #zh-TW
* identifier[idCardNumber].type.coding.system = "http://terminology.hl7.org/CodeSystem/v2-0203"
* identifier[idCardNumber].type.coding.code = #NNxxx
* identifier[idCardNumber].system = "http://www.moi.gov.tw"
* identifier[idCardNumber].value = "Z000000002"
* gender = #female
* birthDate = "1958-09-15"

Instance: CRCConditionColonExample
InstanceOf: ColorectalCancerPrimaryCondition
Usage: #example
Title: "合成原發乙狀結腸癌"
Description: "完全合成範例。"
* id = "crc-condition-colon"
* language = #zh-TW
* clinicalStatus = http://terminology.hl7.org/CodeSystem/condition-clinical#active
* verificationStatus = http://terminology.hl7.org/CodeSystem/condition-ver-status#confirmed
* code = http://hl7.org/fhir/sid/icd-10-cm#C18.7 "Malignant neoplasm of sigmoid colon"
* subject = Reference(CRCPatientColonExample)
* recordedDate = "2025-03-05"

Instance: CRCTCRRectumField2_3
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成直腸癌癌登欄位 2.3 個案分類"
Description: "完全合成範例。"
* id = "crc-tcr-rectum-2-3"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.3 "個案分類"
* subject = Reference(CRCPatientRectumExample)
* focus = Reference(CRCConditionRectumExample)
* valueString = "1"

Instance: CRCTCRRectumField2_5
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成直腸癌癌登欄位 2.5 最初診斷日期"
Description: "完全合成範例。"
* id = "crc-tcr-rectum-2-5"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.5 "最初診斷日期"
* subject = Reference(CRCPatientRectumExample)
* focus = Reference(CRCConditionRectumExample)
* valueString = "20250110"

Instance: CRCTCRRectumField2_6
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成直腸癌癌登欄位 2.6 原發部位"
Description: "完全合成範例。"
* id = "crc-tcr-rectum-2-6"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.6 "原發部位"
* subject = Reference(CRCPatientRectumExample)
* focus = Reference(CRCConditionRectumExample)
* valueString = "C209"

Instance: CRCTCRRectumField2_8
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成直腸癌癌登欄位 2.8 組織型態"
Description: "完全合成範例。"
* id = "crc-tcr-rectum-2-8"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.8 "組織型態"
* subject = Reference(CRCPatientRectumExample)
* focus = Reference(CRCConditionRectumExample)
* valueString = "8140"

Instance: CRCTCRRectumField2_9
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成直腸癌癌登欄位 2.9 性態碼"
Description: "完全合成範例。"
* id = "crc-tcr-rectum-2-9"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.9 "性態碼"
* subject = Reference(CRCPatientRectumExample)
* focus = Reference(CRCConditionRectumExample)
* valueString = "3"

Instance: CRCTCRRectumField2_12
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成直腸癌癌登欄位 2.12 首次顯微鏡檢證實日期"
Description: "完全合成範例。"
* id = "crc-tcr-rectum-2-12"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.12 "首次顯微鏡檢證實日期"
* subject = Reference(CRCPatientRectumExample)
* focus = Reference(CRCConditionRectumExample)
* valueString = "20250110"

Instance: CRCTCRRectumField3_7
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成直腸癌癌登欄位 3.7 臨床期別組合"
Description: "完全合成範例。"
* id = "crc-tcr-rectum-3-7"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#3.7 "臨床期別組合"
* subject = Reference(CRCPatientRectumExample)
* focus = Reference(CRCConditionRectumExample)
* valueString = "2A"

Instance: CRCTCRRectumField4_1
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成直腸癌癌登欄位 4.1 首次療程開始日期"
Description: "完全合成範例。"
* id = "crc-tcr-rectum-4-1"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#4.1 "首次療程開始日期"
* subject = Reference(CRCPatientRectumExample)
* focus = Reference(CRCConditionRectumExample)
* valueString = "20250221"

Instance: CRCTCRRectumField4_1_4
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成直腸癌癌登欄位 4.1.4 申報醫院原發部位手術方式"
Description: "完全合成範例。"
* id = "crc-tcr-rectum-4-1-4"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#4.1.4 "申報醫院原發部位手術方式"
* subject = Reference(CRCPatientRectumExample)
* focus = Reference(CRCConditionRectumExample)
* valueString = "40"

Instance: CRCTCRColonField2_3
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成結腸癌癌登欄位 2.3 個案分類"
Description: "完全合成範例。"
* id = "crc-tcr-colon-2-3"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.3 "個案分類"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueString = "1"

Instance: CRCTCRColonField2_5
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成結腸癌癌登欄位 2.5 最初診斷日期"
Description: "完全合成範例。"
* id = "crc-tcr-colon-2-5"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.5 "最初診斷日期"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueString = "20250305"

Instance: CRCTCRColonField2_6
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成結腸癌癌登欄位 2.6 原發部位"
Description: "完全合成範例。"
* id = "crc-tcr-colon-2-6"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.6 "原發部位"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueString = "C187"

Instance: CRCTCRColonField2_8
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成結腸癌癌登欄位 2.8 組織型態"
Description: "完全合成範例。"
* id = "crc-tcr-colon-2-8"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.8 "組織型態"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueString = "8140"

Instance: CRCTCRColonField2_9
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成結腸癌癌登欄位 2.9 性態碼"
Description: "完全合成範例。"
* id = "crc-tcr-colon-2-9"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.9 "性態碼"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueString = "3"

Instance: CRCTCRColonField2_12
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成結腸癌癌登欄位 2.12 首次顯微鏡檢證實日期"
Description: "完全合成範例。"
* id = "crc-tcr-colon-2-12"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.12 "首次顯微鏡檢證實日期"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueString = "20250305"

Instance: CRCTCRColonField2_14
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成結腸癌癌登欄位 2.14 區域淋巴結檢查數目"
Description: "完全合成範例。"
* id = "crc-tcr-colon-2-14"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#2.14 "區域淋巴結檢查數目"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueString = "15"

Instance: CRCTCRColonField3_13
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成結腸癌癌登欄位 3.13 病理期別組合"
Description: "完全合成範例。"
* id = "crc-tcr-colon-3-13"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#3.13 "病理期別組合"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueString = "3B"

Instance: CRCTCRColonField4_1
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成結腸癌癌登欄位 4.1 首次療程開始日期"
Description: "完全合成範例。"
* id = "crc-tcr-colon-4-1"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#4.1 "首次療程開始日期"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueString = "20250320"

Instance: CRCTCRColonField4_1_4
InstanceOf: CRCTCRDataItemObservation
Usage: #example
Title: "合成結腸癌癌登欄位 4.1.4 申報醫院原發部位手術方式"
Description: "完全合成範例。"
* id = "crc-tcr-colon-4-1-4"
* language = #zh-TW
* insert SyntheticTag
* status = #final
* code = CRCTCRFieldCodeSystem#4.1.4 "申報醫院原發部位手術方式"
* subject = Reference(CRCPatientColonExample)
* focus = Reference(CRCConditionColonExample)
* valueString = "30"

Instance: CRCPatientPolypExample
InstanceOf: ColorectalCancerPatient
Usage: #example
Title: "合成病人－惡性息肉"
Description: "完全合成範例。"
* id = "crc-patient-polyp"
* language = #zh-TW
* identifier[idCardNumber].type.coding.system = "http://terminology.hl7.org/CodeSystem/v2-0203"
* identifier[idCardNumber].type.coding.code = #NNxxx
* identifier[idCardNumber].system = "http://www.moi.gov.tw"
* identifier[idCardNumber].value = "Z000000003"
* gender = #male
* birthDate = "1970-02-20"

Instance: CRCMalignantPolypExample
InstanceOf: CRCMalignantPolypCondition
Usage: #example
Title: "合成惡性息肉（T1）"
Description: "完全合成範例。"
* id = "crc-malignant-polyp"
* language = #zh-TW
* verificationStatus = http://terminology.hl7.org/CodeSystem/condition-ver-status#confirmed
* code = CRCIndicatorConceptCodeSystem#malignant-polyp-t1
* subject = Reference(CRCPatientPolypExample)

Instance: CRCPolypFeatureMarginExample
InstanceOf: CRCMalignantPolypHighRiskFeature
Usage: #example
Title: "合成條件 B：切緣陽性"
Description: "完全合成範例。"
* id = "crc-polyp-feature-b"
* language = #zh-TW
* status = #final
* code = CRCIndicatorConceptCodeSystem#criterion-b-margin-positive
* subject = Reference(CRCPatientPolypExample)
* valueBoolean = true

Instance: CRCPolypPathologyReportExample
InstanceOf: CRCMalignantPolypPathologyReport
Usage: #example
Title: "合成惡性息肉病理報告"
Description: "完全合成範例；issued 為指標 1 計時起點。"
* id = "crc-polyp-pathology-report"
* language = #zh-TW
* status = #final
* category[pathology] = http://terminology.hl7.org/CodeSystem/v2-0074#SP "Surgical Pathology"
* code = CRCIndicatorConceptCodeSystem#malignant-polyp-pathology-report
* subject = Reference(CRCPatientPolypExample)
* issued = "2025-03-01T10:00:00+08:00"
* result = Reference(CRCPolypFeatureMarginExample)

Instance: CRCCurativeResectionExample
InstanceOf: CRCCurativeResectionProcedure
Usage: #example
Title: "合成治癒性切除（病理報告後第 84 天）"
Description: "完全合成範例；落在 12 週內，計入指標 1 分子。"
* id = "crc-curative-resection"
* language = #zh-TW
* status = #completed
* code = CRCIndicatorConceptCodeSystem#curative-resection
* subject = Reference(CRCPatientPolypExample)
* performedDateTime = "2025-05-24T09:00:00+08:00"

CodeSystem: CRCFixtureTagCodeSystem
Id: fixture-tag
Title: "合成資料標記"
Description: "標記完全合成、不得用於臨床或申報的範例與測試資料。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* ^caseSensitive = true
* #synthetic "完全合成資料"
