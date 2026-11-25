{% include disclaimer.md %}

原文沒有寫明之處，本 IG 不自行補規則，只採用下表「目前做法」中最貼近原文字面的解讀，並保留可追溯性。正式使用前，建議向國家衛生研究院「癌症診療核心指標」研究團隊確認（聯絡方式見國健署公告）。

| # | 範圍 | 問題 | 目前做法 | 需要誰確認 |
|---|---|---|---|---|
| A-01 | 共通 IP-CROSS | ~~註3 的「診斷狀態」與「治療狀態分類」沒有寫長表欄位序號~~ **已解決** | 依台灣癌症登記長表實作指引（TWCR_LF）邏輯模型，分別為 2.3.1、2.3.2 | — |
| A-02 | 共通 IP-DEATH | 「治療前已死亡」沒有指定判定欄位 | 已於 CQL 實作（2.3.2、4.1、5.3、5.4）；5.4 依長表摘錄手冊 0＝死亡、1＝存活。各項決定與待確認問題見「[個案組裝](case-assembly.html)」C-01～C-14 | 國衛院研究團隊 |
| A-03 | 共通 IP-DXDATE | 指標年度以哪個日期歸屬（最初診斷日期 2.5 或其他） | 用 2.5，期間由呼叫端以 Measurement Period 指定 | 國衛院研究團隊 |
| A-04 | 指標 1 | 原文為 12 週，參考文獻 RAND 為 6 週 | 依指標名稱，採 12 週（84 天） | — |
| A-05 | 指標 1 | 「病理報告後」的起算日（簽發日、報告日或切片日） | DiagnosticReport.issued | 醫院自訂作業規範 |
| A-06 | 指標 1 | 哪些術式屬「治癒性切除」 | 由醫院判定後以 CRCCurativeResectionProcedure 記錄；IG 不列舉術式 | 臨床團隊 |
| A-07 | 指標 1 | 本地概念代碼與 SNOMED CT／LOINC 的對應尚未審核 | 條件 B–D 已改用 LOINC 問題加答案交換（見 A-21）。惡性息肉（`malignant-polyp-t1`）、條件 A（`criterion-a-polyp-incompletely-excised`）與治癒性切除（`curative-resection`）仍用 crc-indicator-concept 本地代碼交換；條件 B–D 的本地代碼只保留為定義概念。候選對應見「[術語對應與審核](terminology-review.html)」，全部待審核 | 術語與臨床專家 |
| A-08 | 指標 2、3 | 期別組合代碼格式（阿拉伯數字開頭）需依長表手冊核對 | 以第一碼判斷 I–III 期 | 依長表摘錄手冊核對 |
| A-09 | 指標 2 | 2.14 的特殊值（例如 95–99）留在分母、不計入分子，是否符合原意 | 依原文「=12~90」 | 國衛院研究團隊 |
| A-10 | 指標 2 | 原文同時列出 4.1.4＝30~90 與排除 4.1.4<30，兩者互斥 | X2-POLYP 由 D2-SURG 實現，不重複設 define | — |
| A-11 | 指標 2 | 特殊組織型態（GIST、NETs）以 2.8 判斷；high grade dysplasia 以 2.9＝2 判斷 | 列為 Denominator Exclusion | 國衛院研究團隊 |
| A-12 | 指標 3 | 適用範圍說明的特殊組織型態排除只寫在結腸癌，直腸癌是否也適用 | 不套用於指標 3 | 國衛院研究團隊 |
| A-13 | 指標 3 | 天數差沒有下限；首次療程早於顯微鏡檢證實日期時，天數為負數 | 依原文，只檢查 ≦ 42 天 | 國衛院研究團隊 |
| A-14 | 指標 3 | 指標名稱寫「手術或放療或 CCRT」，但選用欄位用首次療程開始日期（4.1，涵蓋所有療法） | 依選用欄位，用 4.1 | 國衛院研究團隊 |
| A-15 | 全部 | 同一病人多原發大腸癌 | **第一優先確認。** 以保留的原發腫瘤為 population basis；同院同癌別依註1只留一筆（同步結腸＋直腸癌亦然），不同醫院各自計算。本項對結果影響最大：同步結腸＋直腸癌只保留一筆，另一顆腫瘤永遠不會進入它自己部位專屬的指標（例如保留直腸癌時，結腸癌不進指標 2） | 國衛院研究團隊（癌別定義，見個案組裝 C-01，第一優先） |
| A-16 | 全部 | 115 年指標沒有寫明適用期間的結束日 | Measure.effectivePeriod 只設起日 2026-04-20，由下一年度修訂取代 | 國衛院研究團隊 |
| A-17 | 共同層 | TW Core 1.0.0 台灣版 ICD-10-CM CodeSystem 在套件中僅 11 個代碼 | 診斷碼使用國際 ICD-10-CM；接收端應接受兩種代碼系統 | TW Core 維護者 |
| A-18 | 指標 1 條件 D | 「第 3 級或屬分化不全」是否包含 G4（未分化） | 只計 G3（SNOMED CT 1155704001）；G4 不計 | 國衛院研究團隊 |
| A-19 | 全部 | 同一人有多個 FHIR Patient 資源時無法在 Patient context 內去重 | 要求評估前完成病人身分整合（一人一個 Patient） | 導入醫院 |
| A-20 | 全部 | `urn:uuid:` 參照需要 Bundle fullUrl，CQL 資料模型取不到 | 不支援；評估前須解析為 `Condition/id` | 導入醫院 |
| A-21 | 指標 1 條件 B–D | 病理發現的答案與問題如何配對；同一筆發現帶互相矛盾的答案（例如同時「有」與「無」淋巴血管侵犯）如何計算 | 每一題的答案取自自己的答案清單（B：LL4381-1；C：LL906-9；D：SNOMED CT G1–G4），且該清單的 coding **恰一個**，由 `CRCPathologyHighRiskFeature` 的 invariant `crc-hrf-b-answer`／`crc-hrf-c-answer`／`crc-hrf-d-answer` 檢查。同一清單內兩個 coding（例如 LA13328-2 加 LA13327-4）是矛盾的錯誤資料，驗證即失敗；完全沒有該題清單的 coding（例如 59544-7 只答切緣的 LA27251-0）也失敗。其他代碼系統或清單的 coding 視為 translation，依一般 CodeableConcept 用法允許，例如 LOINC 答案加上同義的 SNOMED CT coding，或 D 的 SNOMED CT G3 加上 LOINC LA15450-2。translation 是否與答案一致不由 Profile 檢查；CQL 另行把關：發現只要帶有任何不屬於「成立」值集的答案清單 coding（成立與不成立混雜），就不算成立。評估前資料仍應先通過 Profile 驗證 | 導入醫院 |
| A-22 | 全部 | `code`、`status` 等 FHIR code 型別值前後帶空白（不合法的 FHIR） | 不處理：HAPI（Java 引擎）解析時會去除 code 的前後空白，cql-execution 不會，兩個引擎結果可能不同；`status` 帶空白時 HAPI 會拒絕整個 Bundle。評估前資料應先通過 FHIR 驗證 | 導入醫院 |
| A-23 | 全部 IP-DUP | 註1 的「身分證號」在 Patient context 中無法比對 | 以 Patient 資源代表同一人；1.4 缺漏或 `9999999999` 不排除個案。同一人分散在多個 Patient 資源時須先整合（MPI），否則可能重複計算；每個 Bundle 只能有一個 Patient（兩個引擎遇到多個 Patient 都會失敗） | 導入醫院 |
| A-24 | 指標 1–3 IP-OUTSIDE | 第五點排除在 MeasureReport 中如何呈現 | 列為 denominator exclusion（指標 2 與特殊組織型態合併），另以 supplemental data `Outside Data Excluded n` 列出被排除的腫瘤 | 國衛院研究團隊 |
