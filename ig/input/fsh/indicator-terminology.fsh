// 大腸癌指標 1（惡性息肉）屬「醫院自行申報」，癌登資料庫無法提供條件 A／C，
// 因此需要臨床來源事實。
//
// 交換用代碼：條件 B、C、D 以 LOINC 問題加答案表達（答案取自 LOINC 答案清單或
// SNOMED CT，見下方各題的答案 ValueSet）。惡性息肉、條件 A 與治癒性切除尚無經審查的
// 國際代碼，交換仍用本 CodeSystem 的本地代碼；在逐碼查證 SNOMED CT／LOINC 對應並經
// 臨床審查前作為穩定的交換鍵，不宣稱等同任何國際標準代碼。
// 條件 B–D 的本地代碼只是指標條件的定義概念，供 ConceptMap 記錄候選對應，不用於交換。

CodeSystem: CRCIndicatorConceptCodeSystem
Id: crc-indicator-concept
Title: "大腸癌核心指標臨床概念（本地暫用）"
Description: "大腸癌指標 1 需要、但癌登長表沒有對應欄位的臨床事實。惡性息肉（malignant-polyp-t1）、條件 A 與治癒性切除的代碼用於交換；條件 B–D 的代碼只是定義概念，交換時改用 LOINC 問題加答案（CRCPathologyHighRiskFeature）。本地暫用代碼，待臨床與術語審查後對應至國際標準代碼。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* ^caseSensitive = true
* ^content = #complete
* #malignant-polyp-t1 "Malignant polyp（含 T1 腺癌之息肉）"
    "切除之息肉中出現 T1 腺癌。Tis 不屬之（指標 1 備註）。"
* #criterion-a-polyp-incompletely-excised "A. 大腸鏡檢報告指出息肉未完全被切除"
* #criterion-b-margin-positive "B. 手術切除外緣之癌細胞呈陽性"
    "指標條件的定義概念。交換時以 LOINC 85290-5 加答案 LA27251-0 表達（CRCPathologyHighRiskFeature）。"
* #criterion-c-lymphovascular-invasion "C. 癌細胞已侵犯淋巴或靜脈組織"
    "指標條件的定義概念。交換時以 LOINC 59544-7 加答案 LA13328-2 表達。"
* #criterion-d-grade3-poorly-differentiated "D. 病理顯示為第 3 級或屬分化不全之癌細胞"
    "指標條件的定義概念。交換時以 LOINC 33732-9 加 SNOMED CT 1155704001（G3）表達。"
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
Title: "病理報告類型"
Description: "指標 1 計時起點之病理報告的報告類型（LOINC）。「惡性息肉」是報告的發現，不是報告類型，由 CRCMalignantPolypCondition.evidence 連結。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* http://loinc.org#11529-5 "Surgical pathology study"

ValueSet: CRCPathologyHighRiskFeatureVS
Id: crc-pathology-high-risk-feature
Title: "惡性息肉病理高風險條件 B–D 的觀察問題（LOINC）"
Description: "病理報告中用來判定條件 B、C、D 的 LOINC 觀察碼：B 切緣（85290-5）、C 淋巴血管侵犯（59544-7）、D 組織學分級（33732-9）。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* http://loinc.org#85290-5 "Surgical margin tumor involvement [Presence] in Colorectal cancer specimen by Light microscopy"
* http://loinc.org#59544-7 "Lymph-vascular invasion Cancer specimen"
* http://loinc.org#33732-9 "Histology grade [Identifier] in Cancer specimen"

// 條件 B、C、D 各自的答案清單。CRCPathologyHighRiskFeature 以 invariant
// crc-hrf-b/c/d-answer 把每個 LOINC 問題綁到自己的答案清單，且該清單的 coding 恰一個：
// 避免把某一題的答案（例如切緣的 LA27251-0）填到另一題（59544-7）仍能通過驗證，
// 也擋下同一清單內互相矛盾的答案。
ValueSet: CRCSurgicalMarginAnswerVS
Id: crc-surgical-margin-answer
Title: "條件 B 的答案：切緣癌細胞（LOINC LL4381-1）"
Description: "LOINC 85290-5 的官方答案清單 LL4381-1（CAP_surgical margins）。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* http://loinc.org#LA27250-2 "Surgical margin not involved by tumor"
* http://loinc.org#LA27251-0 "Surgical margin involved by tumor"
* http://loinc.org#LA27144-7 "Cannot be assessed"

ValueSet: CRCLymphovascularInvasionAnswerVS
Id: crc-lymphovascular-invasion-answer
Title: "條件 C 的答案：淋巴血管侵犯（LOINC LL906-9）"
Description: "LOINC 59544-7 的官方答案清單 LL906-9（NAACCR_1182）。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* http://loinc.org#LA13327-4 "Lymph-vascular Invasion Not Present (absent)/Not Identified"
* http://loinc.org#LA13328-2 "Lymph-vascular Invasion Present/Identified"
* http://loinc.org#LA4720-4 "Not applicable"
* http://loinc.org#LA13420-7 "Unknown/Indeterminate"

ValueSet: CRCHistologicGradeAnswerVS
Id: crc-histologic-grade-answer
Title: "條件 D 的答案：組織學分級（SNOMED CT）"
Description: "LOINC 33732-9 沒有 LOINC 答案清單，以 SNOMED CT 組織學分級 G1–G4 表達。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* http://snomed.info/sct#1155701009 "G1: Well differentiated"
* http://snomed.info/sct#1155703007 "G2: Moderately differentiated"
* http://snomed.info/sct#1155704001 "G3: Poorly differentiated"
* http://snomed.info/sct#1155702002 "G4: Undifferentiated"

ValueSet: CRCPathologyHighRiskAnswerVS
Id: crc-pathology-high-risk-answer
Title: "惡性息肉病理高風險條件 B–D 的答案"
Description: "條件 B、C、D 三份答案清單的聯集，供 CRCPathologyHighRiskFeature.valueCodeableConcept 的 required 綁定使用。哪一題可用哪一份清單，由 Profile 的 invariant crc-hrf-b-answer、crc-hrf-c-answer、crc-hrf-d-answer 規定：每題恰一個 coding 取自自己的清單，其他 coding 視為 translation。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* include codes from valueset CRCSurgicalMarginAnswerVS
* include codes from valueset CRCLymphovascularInvasionAnswerVS
* include codes from valueset CRCHistologicGradeAnswerVS

ValueSet: CRCMarginInvolvedVS
Id: crc-criterion-b-met
Title: "條件 B 成立：切緣有癌細胞"
Description: "85290-5 的答案中表示條件 B 成立者。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* http://loinc.org#LA27251-0 "Surgical margin involved by tumor"

ValueSet: CRCLymphovascularInvasionPresentVS
Id: crc-criterion-c-met
Title: "條件 C 成立：有淋巴血管侵犯"
Description: "59544-7 的答案中表示條件 C 成立者。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* http://loinc.org#LA13328-2 "Lymph-vascular Invasion Present/Identified"

ValueSet: CRCGrade3VS
Id: crc-criterion-d-met
Title: "條件 D 成立：第 3 級（分化不全）"
Description: "33732-9 的答案中表示條件 D 成立者。第 3 級即分化不全（G3）；G4（未分化）是否也算，原文未提，列為待確認（見術語對應與審核）。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* http://snomed.info/sct#1155704001 "G3: Poorly differentiated"

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
Description: "記載條件 A–D 的 Observation 代碼：條件 A 的本地代碼，加上條件 B–D 的 LOINC 觀察問題。條件是否成立由各自的答案決定。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* CRCIndicatorConceptCodeSystem#criterion-a-polyp-incompletely-excised
* http://loinc.org#85290-5 "Surgical margin tumor involvement [Presence] in Colorectal cancer specimen by Light microscopy"
* http://loinc.org#59544-7 "Lymph-vascular invasion Cancer specimen"
* http://loinc.org#33732-9 "Histology grade [Identifier] in Cancer specimen"

ValueSet: CRCCurativeResectionVS
Id: crc-curative-resection
Title: "治癒性切除"
Description: "指標 1 分子之治癒性切除。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* CRCIndicatorConceptCodeSystem#curative-resection
