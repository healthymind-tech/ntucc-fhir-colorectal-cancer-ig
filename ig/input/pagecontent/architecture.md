{% include disclaimer.md %}

```text
原始臨床資料（病理報告、大腸鏡檢報告、手術紀錄、放化療紀錄）
        │
        ├──► 大腸癌共同層：ColorectalCancerPatient、ColorectalCancerPrimaryCondition
        │
        ├──► 癌登欄位層：CRCTCRDataItemObservation（一個長表欄位一筆，focus 指向原發腫瘤）
        │         │
        │         └──► 指標 2、3（癌登資料庫）
        │
        └──► 指標 1 臨床事實：CRCMalignantPolypCondition、CRCMalignantPolypPathologyReport、
                  CRCColonoscopyHighRiskFeature（A）、CRCPathologyHighRiskFeature（B–D）、
                  CRCCurativeResectionProcedure
                  │
                  └──► 指標 1（醫院自行申報）

Task 層（評估前）：組 Group、院內重複個案去重、排除治療前死亡
        │
        ▼
Library ColorectalCancerCoreIndicators（CQL，計算單位＝原發腫瘤 Condition）──► Measure crc-qi-01 / 02 / 03 ──► MeasureReport
```

## 為什麼指標 2、3 讀癌登欄位，而不是臨床資源？

國健署文件中，指標 2、3 的「癌登資料選用欄位」已逐條寫出長表欄位與值域（例如「申報醫院原發部位手術方式(4.1.4)＝30~90」）。直接讀取這些欄位，計算結果才能與國健署及癌登中心的核算方式一致。如果改從 Procedure、Observation 等臨床資源推導，每個欄位都要多一層臨床到癌登的轉換，誤差來源也會變多。範例乳癌 IG 的指標 3 就是因為缺少劑量欄位，只能算出上界。

臨床資料轉成癌登欄位（摘錄）屬於癌登 Task 的工作，與本 IG 的指標層分開。

## 為什麼指標 1 不讀癌登欄位？

原文寫明：「癌登資料指標分母僅能提供條件 B/D；條件 A/C 無法由現行癌登資料庫取得」，「癌登資料選用欄位：醫院自行申報」。因此指標 1 讀取臨床來源事實：大腸鏡檢報告（條件 A）、病理報告（條件 B、C、D）及後續手術。

## 與 TW Core 的關係

所有臨床資源 Profile 都繼承 TW Core IG 1.0.0 對應的 Profile，TW Core 的必填欄位、值集與 slicing 一併適用：**符合本 IG Profile 的實例，同時也符合 TW Core**。反方向不成立——本 IG 另要求本地概念代碼（指標 1 的息肉、病理報告、高風險條件、治癒性切除）與病理報告 category `v2-0074#SP`，一般的 TW Core 資料須補上這些內容才符合本 IG。

| Profile | 父 Profile | 說明 |
|---|---|---|
| ColorectalCancerPatient | TW Core Patient | |
| ColorectalCancerPrimaryCondition | TW Core Condition | 需 clinicalStatus 與 category；診斷碼用 ICD-10-CM |
| CRCMalignantPolypCondition | TW Core Condition | |
| CRCMalignantPolypPathologyReport | TW Core DiagnosticReport | category 另要求 v2-0074#SP |
| CRCPathologyHighRiskFeature（B、C、D） | TW Core Observation Laboratory Result | TW Core DiagnosticReport.result 只能指向檢驗結果 Observation |
| CRCColonoscopyHighRiskFeature（A） | TW Core Observation Clinical Result | category = procedure（來自大腸鏡檢報告） |
| CRCCurativeResectionProcedure | TW Core Procedure | |
| CRCTCRDataItemObservation | **FHIR R4 Observation**（刻意不繼承 TW Core） | 見下方說明 |

**為什麼癌登欄位 Observation 不繼承 TW Core？** 結構上其實可行：TW Core Observation Clinical Result 的 `effective[x]` 為 0..1，category 的 binding 只是 preferred，加上本地類別代碼就能通過驗證。但它的語意是「臨床檢驗檢查結果」，而「癌登長表第 4.1.4 欄的申報值」不是臨床結果；標成 Clinical Result 會讓接收端誤判資料性質，也帶不來實際的互通效益。其餘 TW Core Observation Profile 不是固定特定代碼（職業、性傾向等），就是要求觀察時間與臨床類別（Simple Observation），都不適用。因此本 Profile 直接繼承 FHIR R4 Observation，並在 Profile 說明中寫明理由。

**診斷碼為什麼用國際 ICD-10-CM？** TW Core 1.0.0 以台灣版 ICD-10-CM CodeSystem（`icd-10-cm-*-tw`）定義 Condition 代碼的 slice，但套件中該 CodeSystem 標為 complete 卻只收 11 個代碼，`C18.7`、`C20` 會驗證失敗。TW Core 的 `code.coding` slicing 為 open，國際 ICD-10-CM（`http://hl7.org/fhir/sid/icd-10-cm`）是允許的寫法；接收端應同時接受兩種代碼系統。

**為什麼條件 A 與 B–D 分成兩個 Profile？** 條件 A 來自大腸鏡檢報告，屬於處置結果；B、C、D 來自病理報告，屬於檢驗結果，而且 TW Core 規定病理報告的 `result` 只能指向檢驗結果 Observation。CQL 讀取的值集同時包含 A–D 四個代碼，所以計算邏輯不受影響。

## Artifacts

| 類型 | Artifact |
|---|---|
| Profile | ColorectalCancerPatient、ColorectalCancerPrimaryCondition、CRCTCRDataItemObservation、CRCMalignantPolypCondition、CRCMalignantPolypPathologyReport、CRCPathologyHighRiskFeature、CRCColonoscopyHighRiskFeature、CRCCurativeResectionProcedure |
| CodeSystem | crc-tcr-field（癌登欄位）、crc-indicator-concept（指標 1 本地概念）、fixture-tag |
| Library | ColorectalCancerCoreIndicators |
| Measure | crc-qi-01、crc-qi-02、crc-qi-03 |
