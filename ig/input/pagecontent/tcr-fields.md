{% include disclaimer.md %}

每一個癌登長表欄位對應一筆 [CRCTCRDataItemObservation](StructureDefinition-crc-tcr-data-item-observation.html)：

| Observation 元素 | 內容 |
|---|---|
| `code` | `https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/CodeSystem/crc-tcr-field#<欄位序號>` |
| `valueString` | 長表原始值，原樣保存（例如 `20250110`、`30`、`3B`、`C18.7`） |
| `subject` | 病人 |
| `focus` | 此欄位所屬的原發腫瘤（ColorectalCancerPrimaryCondition） |
| `status` | final／amended／corrected 才會被指標讀取 |
| `issued` | 必填。同一顆腫瘤的同一欄位有多筆申報值時，`issued` 最晚者為現行值；`issued` 相同時取 Observation.id 最大者（應視為資料品質問題） |
| `derivedFrom` | 摘錄來源文件（選用） |

## 指標引用的欄位

| 欄位 | 名稱 | 使用者 |
|---|---|---|
| 1.1 | 申報醫院代碼 | 共通（IP-DUP） |
| 2.3 | 個案分類 | 共通（IP-CLASS、IP-CROSS）、指標 3（D3-CLASS） |
| 2.3.1 | 診斷狀態分類 | 共通（IP-CROSS） |
| 2.3.2 | 治療狀態分類 | 共通（IP-CROSS、IP-DEATH） |
| 2.5 | 最初診斷日期 | 共通（IP-DXDATE、IP-DUP） |
| 2.6 | 原發部位 | 指標 2（D2-SITE）、指標 3（D3-SITE） |
| 2.8 | 組織型態 | 指標 2（X2-HIST） |
| 2.9 | 性態碼 | 指標 2（X2-HIST） |
| 2.12 | 首次顯微鏡檢證實日期 | 指標 3（N3-42D） |
| 2.14 | 區域淋巴結檢查數目 | 指標 2（N2-LN12） |
| 3.7 | 臨床期別組合 | 指標 3（D3-CSTAGE）、共通（IP-DUP 同日期別比較的備援） |
| 3.13 | 病理期別組合 | 指標 2（D2-PSTAGE）、共通（IP-DUP 同日期別比較） |
| 4.1 | 首次療程開始日期 | 指標 3（N3-42D）、共通（IP-DEATH） |
| 4.1.4 | 申報醫院原發部位手術方式 | 指標 2（D2-SURG、X2-POLYP） |
| 5.3 | 最後聯絡或死亡日期 | 共通（IP-DEATH） |
| 5.4 | 生存狀態 | 共通（IP-DEATH） |

指標文件註3只以文字提到「診斷狀態」與「治療狀態分類」，沒有寫欄位序號；2.3.1、2.3.2 依[台灣癌症登記長表實作指引（TWCR_LF）](twcr-lf.html)的邏輯模型確認。

## ICD-O-3 與 LOINC

- 原發部位（2.6）、組織型態（2.8）、性態碼（2.9）同時以 ICD-O-3 代碼表達在原發腫瘤 Condition 上（`bodySite` 與 `histologyMorphologyBehavior` extension），轉換規則見「[術語對應與審核](terminology-review.html#icd-o-3)」。
- 各欄位對應的 LOINC 觀察碼候選列在 ConceptMap [crc-tcr-field-to-loinc](ConceptMap-tcr-field-to-loinc.html)，目前全部待審核。

## 為什麼值用字串？

癌登欄位混有日期、代碼、數字與特殊值（`00000000` 無、`99999999` 不詳、`988` 不適用）。如果在摘錄層就轉成 date 或 integer，特殊值就會遺失或被誤判。本 IG 保存原始字串，由 CQL 的 `Registry Date`、`Registry Integer` 等函式在計算時明確判讀，判讀規則可以測試，也可以還原。
