{% include disclaimer.md %}

本頁列出本地代碼與國際標準術語（LOINC、SNOMED CT）的**候選對應**，供術語與臨床專家審核。對應以 [ConceptMap crc-tcr-field-to-loinc](ConceptMap-tcr-field-to-loinc.html) 與 [ConceptMap indicator-concept-to-standard](ConceptMap-indicator-concept-to-standard.html) 發布，兩者都是 `draft`、`experimental`。

> **狀態：全部待審核。** 每個候選代碼都已在 tx.fhir.org 查證**存在、為 active，且官方名稱與表內一致**（LOINC 2.83、SNOMED CT International 2026-07-01）。但「這個代碼是否就是正確的對應」屬於術語與臨床判斷，尚未經專家確認。審核完成前，這些對應**不得用於正式交換**，指標計算也不依賴它們。

## 審核方式

1. 逐列判斷「候選代碼」是否正確表達「來源概念」，以及「關係」是否恰當：
   - `equivalent`：語意相同。
   - `wider`：候選代碼的範圍比來源概念**寬**。
   - `narrower`：候選代碼的範圍比來源概念**窄**（例如條件 C 是「淋巴**或**靜脈」侵犯，要兩個代碼的聯集才等同）。
   - `relatedto`：相關但不同類型，例如 LOINC 觀察碼（問題）對應到本地的發現（答案）。
   - `unmatched`：找不到適合的國際代碼。
2. 在 `mappings/terminology-candidates.csv` 把 `review_status` 改為 `accepted` 或 `rejected`，填上 `reviewer` 與 `review_date`；需要時修改候選代碼或關係。
3. 執行 `python3 scripts/build_terminology.py` 重新產生 ConceptMap 與本表，再執行 `python3 scripts/verify_terminology.py` 確認代碼仍存在且名稱未變。
4. CI 會檢查產生的檔案與 CSV 一致。

## 需要專家特別判斷的項目

| 項目 | 問題 |
|---|---|
| 惡性息肉 `malignant-polyp-t1` | SNOMED CT `1259447005` 限腺瘤性息肉、不限 T1，標為 `inexact`。是否接受，或改用 Haggitt／Kikuchi 浸潤深度分類等更精確的表達？鋸齒狀病灶的惡性息肉如何表達？ |
| 條件 A（息肉未完全切除） | 候選 SNOMED CT `1295388007`（任何腫瘤切除後殘留）範圍較寬。是否接受，或維持本地代碼？ |
| 條件 C（淋巴或靜脈侵犯） | 有兩種表達方式：兩個 SNOMED 發現（淋巴 `395717001`、靜脈 `369732007`）的聯集；或觀察碼（LOINC `59544-7`、SNOMED `1286964009`）加上 present 答案。`1286964009` 只涵蓋淋巴與小血管，不含大靜脈。採用哪一種？ |
| 條件 D（第 3 級或分化不全） | 第 3 級即分化不全（G3），候選 SNOMED CT `369718005`（大腸直腸 G3 定義）標為 `equivalent`。是否同意兩者為同一概念？是否也要涵蓋 G4（未分化）？ |
| 治癒性切除 | `23968004`（結腸切除）與 `87677003`（直腸切除）都不含「治癒性」語意，標為 `inexact`。是否改為一組術式代碼的值集，再搭配手術意圖？ |
| 2.12 首次顯微鏡檢證實日期 | 候選 LOINC `21919-6` 只涵蓋切片（biopsy），標為 `narrower`。細胞學證實的個案如何表達？ |
| 3.7／3.13 期別 | LOINC 觀察碼確定，但癌登的期別代碼格式（`1A`、`3B`）轉成 AJCC 答案代碼的規則仍需定義 |

## 候選對應總表

{% include terminology-candidates-table.md %}

## ICD-O-3

原發部位與組織型態本來就是 WHO 的 ICD-O-3 代碼，不需要對應，只需要明確標示代碼系統。本 IG 在 [ColorectalCancerPrimaryCondition](StructureDefinition-colorectal-cancer-primary-condition.html) 上以 `http://terminology.hl7.org/CodeSystem/icd-o-3` 表達：

| 癌登欄位 | 原值 | FHIR 位置 | ICD-O-3 代碼 |
|---|---|---|---|
| 2.6 原發部位 | `C187` | `Condition.bodySite.coding[icdo3Topography]` | `C18.7`（第 3 碼後補小數點） |
| 2.8 組織型態＋2.9 性態碼 | `8140`、`3` | `Condition.extension[histologyMorphologyBehavior]` | `8140/3` |

這個轉換是確定性的，不需要人工判斷，規則實作在 `reference/icdo3.py` 並有單元測試；格式不符的值會直接報錯，不會產生看似合理的錯誤代碼。Profile 另以 invariant 檢查代碼格式（`C18.7`、`8140/3`）。

**驗證限制**：IG Publisher 會到 tx.fhir.org 驗證 ICD-O-3 代碼，但 tx.fhir.org 上的 ICD-O-3 只是版本 2000 的片段（fragment），只收 3 個組織型態代碼（8500/3、8140/3、8046/3），**沒有任何部位代碼**。因此本 IG 範例中的 `C18.7`、`C20.9` 會出現「未知代碼」警告，已在 `ignoreWarnings.txt` 註明理由後抑制。實際資料中的其他部位代碼，以及這 3 個以外的組織型態代碼（例如 `8140/2`、`8261/3`），驗證時也會出現同樣的警告；這反映的是伺服器收錄範圍，不是資料錯誤。
