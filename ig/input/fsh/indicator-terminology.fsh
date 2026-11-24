// 大腸癌指標 1（惡性息肉）屬「醫院自行申報」，癌登資料庫無法提供條件 A／C，
// 因此需要臨床來源事實。以下為本 IG 的本地概念代碼：在逐碼查證 SNOMED CT／LOINC
// 對應並經臨床審查前，作為穩定的交換鍵使用，不宣稱等同任何國際標準代碼。

CodeSystem: CRCIndicatorConceptCodeSystem
Id: crc-indicator-concept
Title: "大腸癌核心指標臨床概念（本地暫用）"
Description: "大腸癌指標 1 需要、但癌登長表沒有對應欄位的臨床事實。本地暫用代碼，待臨床與術語審查後對應至國際標準代碼。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* ^caseSensitive = true
* ^content = #complete
* #malignant-polyp-t1 "Malignant polyp（含 T1 腺癌之息肉）"
    "切除之息肉中出現 T1 腺癌。Tis 不屬之（指標 1 備註）。"
* #malignant-polyp-pathology-report "惡性息肉病理報告"
    "指標 1 計時起點：病理報告日期。"
* #criterion-a-polyp-incompletely-excised "A. 大腸鏡檢報告指出息肉未完全被切除"
* #criterion-b-margin-positive "B. 手術切除外緣之癌細胞呈陽性"
* #criterion-c-lymphovascular-invasion "C. 癌細胞已侵犯淋巴或靜脈組織"
* #criterion-d-grade3-poorly-differentiated "D. 病理顯示為第 3 級或屬分化不全之癌細胞"
* #curative-resection "治癒性切除（curative resection）"
    "惡性息肉後續之治癒性外科切除。何種術式屬治癒性切除由申報醫院依臨床判定，本 IG 不列舉術式。"

ValueSet: CRCMalignantPolypVS
Id: crc-malignant-polyp
Title: "Malignant polyp (T1)"
Description: "指標 1 分母之惡性息肉診斷。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* CRCIndicatorConceptCodeSystem#malignant-polyp-t1

ValueSet: CRCMalignantPolypPathologyReportVS
Id: crc-malignant-polyp-pathology-report
Title: "惡性息肉病理報告"
Description: "指標 1 計時起點之病理報告。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* CRCIndicatorConceptCodeSystem#malignant-polyp-pathology-report

ValueSet: CRCPathologyHighRiskFeatureVS
Id: crc-pathology-high-risk-feature
Title: "惡性息肉病理高風險條件 B–D"
Description: "記載於病理報告的條件 B、C、D。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* CRCIndicatorConceptCodeSystem#criterion-b-margin-positive
* CRCIndicatorConceptCodeSystem#criterion-c-lymphovascular-invasion
* CRCIndicatorConceptCodeSystem#criterion-d-grade3-poorly-differentiated

ValueSet: CRCColonoscopyHighRiskFeatureVS
Id: crc-colonoscopy-high-risk-feature
Title: "惡性息肉大腸鏡高風險條件 A"
Description: "記載於大腸鏡檢報告的條件 A。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* CRCIndicatorConceptCodeSystem#criterion-a-polyp-incompletely-excised

ValueSet: CRCMalignantPolypHighRiskFeatureVS
Id: crc-malignant-polyp-high-risk-feature
Title: "惡性息肉高風險條件 A–D"
Description: "指標 1 分母條件 A、B、C、D（大腸鏡與病理兩個來源的聯集）。任一記錄為存在即符合分母；CQL 讀取本值集。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* CRCIndicatorConceptCodeSystem#criterion-a-polyp-incompletely-excised
* CRCIndicatorConceptCodeSystem#criterion-b-margin-positive
* CRCIndicatorConceptCodeSystem#criterion-c-lymphovascular-invasion
* CRCIndicatorConceptCodeSystem#criterion-d-grade3-poorly-differentiated

ValueSet: CRCCurativeResectionVS
Id: crc-curative-resection
Title: "治癒性切除"
Description: "指標 1 分子之治癒性切除。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* CRCIndicatorConceptCodeSystem#curative-resection
