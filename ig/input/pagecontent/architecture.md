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

個案組裝（CQL 內）：癌別、院內重複個案去重、class、跨院、治療前死亡；第五點外院資料由醫院以 CRCOutsideDataExclusion 資料宣告
        │
        ▼
Library ColorectalCancerCoreIndicators（CQL，population basis＝保留的原發腫瘤 Condition）──► Measure crc-qi-01 / 02 / 03（CQM proportion measure）──► MeasureReport
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
| ColorectalCancerPrimaryCondition | TW Core Condition | 需 clinicalStatus 與 category；診斷碼用國際 ICD-10-CM 或 TW Core icd-10-cm-*-tw 皆可（code 1..1，不另綁定） |
| CRCMalignantPolypCondition | TW Core Condition | |
| CRCMalignantPolypPathologyReport | TW Core DiagnosticReport | category 另要求 v2-0074#SP |
| CRCPathologyHighRiskFeature（B、C、D） | TW Core Observation Laboratory Result | TW Core DiagnosticReport.result 只能指向檢驗結果 Observation；以 LOINC 問題加答案表達，符合 TW Core 對 LOINC 的 extensible 綁定 |
| CRCColonoscopyHighRiskFeature（A） | TW Core Observation Clinical Result | category = procedure（來自大腸鏡檢報告） |
| CRCCurativeResectionProcedure | TW Core Procedure | |
| CRCTCRDataItemObservation | **FHIR R4 Observation**（刻意不繼承 TW Core） | 見下方說明 |
| CRCOutsideDataExclusion | **FHIR R4 Observation**（刻意不繼承 TW Core） | 第五點外院資料排除：醫院的管理性宣告，不是臨床結果，理由同 CRCTCRDataItemObservation |

**為什麼癌登欄位 Observation 不繼承 TW Core？** 結構上其實可行：TW Core Observation Clinical Result 的 `effective[x]` 為 0..1，category 的 binding 只是 preferred，加上本地類別代碼就能通過驗證。但它的語意是「臨床檢驗檢查結果」，而「癌登長表第 4.1.4 欄的申報值」不是臨床結果；標成 Clinical Result 會讓接收端誤判資料性質，也帶不來實際的互通效益。其餘 TW Core Observation Profile 不是固定特定代碼（職業、性傾向等），就是要求觀察時間與臨床類別（Simple Observation），都不適用。因此本 Profile 直接繼承 FHIR R4 Observation，並在 Profile 說明中寫明理由。

**診斷碼為什麼用國際 ICD-10-CM？** TW Core 1.0.0 以台灣版 ICD-10-CM CodeSystem（`icd-10-cm-*-tw`）定義 Condition 代碼的 slice，但套件中該 CodeSystem 標為 complete 卻只收 11 個代碼，`C18.7`、`C20` 會驗證失敗。TW Core 的 `code.coding` slicing 為 open，國際 ICD-10-CM（`http://hl7.org/fhir/sid/icd-10-cm`）是允許的寫法；接收端應同時接受兩種代碼系統。

## 標準符合度

| 標準 | 本 IG 的宣告 |
|---|---|
| HL7 Quality Measure IG（`hl7.fhir.uv.cqm` 2.0.0） | Measure 宣告 `cqm-proportionmeasure`、`cqm-cqlmeasure`，以 `cqm-populationBasis` 宣告 population basis，group 與 population 帶 linkId。**未宣告** `cqm-publishablemeasure`：它要求版本無關／版本專屬／簡稱三種正式識別碼與背書資料，草稿不具備 |
| CRMI（`hl7.fhir.uv.crmi` 2.0.0） | Library 宣告 `crmi-shareablelibrary`、`crmi-computablelibrary`、`crmi-publishablelibrary`、`crmi-executablelibrary`（Publisher 由 CQL 產生 ELM、`parameter` 與 `dataRequirement`） |
| Using CQL（`hl7.fhir.uv.cql` 2.0.0） | Library 宣告 `cql-library`。翻譯器選項 extension `cqf-cqlOptions` 在該 Profile 為 0..1，本版未提供 |
| TW Core 1.0.0 | 臨床 Profile 皆繼承 TW Core（癌登欄位 Observation 與第五點外院資料 Observation 除外，理由見上） |
| mCODE | 只借用原發腫瘤的部位與組織型態形狀（bodySite、histology-morphology-behavior）；期別與治療不以 mCODE 臨床資源表達，因指標定義在癌登欄位上 |
| 台灣癌症登記長表實作指引（TWCR_LF） | 不相依、不繼承；欄位對照見「[與 TWCR_LF 的關係](twcr-lf.html)」 |

**為什麼條件 A 與 B–D 分成兩個 Profile？** 條件 A 來自大腸鏡檢報告，屬於處置結果；B、C、D 來自病理報告，屬於檢驗結果，而且 TW Core 規定病理報告的 `result` 只能指向檢驗結果 Observation。CQL 讀取的值集同時包含 A–D 四個代碼，所以計算邏輯不受影響。

## 執行參數

Library 只有一個輸入參數：

| CQL 參數 | 型別 | 說明 |
|---|---|---|
| `Measurement Period` | `Interval<DateTime>` | 量測期間 |

以 `Measure/$evaluate-measure`（FHIR R4）計算時，量測期間由標準輸入 `periodStart`／`periodEnd` 提供，不需要其他參數：

```json
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "periodStart", "valueDate": "2025-01-01" },
    { "name": "periodEnd", "valueDate": "2025-12-31" },
    { "name": "reportType", "valueCode": "summary" }
  ]
}
```

直接以 `Library/$evaluate` 執行時，量測期間放在 `parameters` 中：`{ "name": "Measurement Period", "valuePeriod": { "start": "2025-01-01T00:00:00+08:00", "end": "2025-12-31T23:59:59.999+08:00" } }`。

**刻意不用參數的兩項輸入：**

- **第五點外院資料**：醫院以資料宣告，每顆腫瘤、每項指標一筆 [CRCOutsideDataExclusion](StructureDefinition-crc-outside-data-exclusion.html) Observation（`code` 為排除的指標，`value` 為第五點 1 或 2，`focus` 指向腫瘤）。早期版本以 CQL 參數傳腫瘤 id 清單，但 R4 的 `$evaluate-measure` 沒有傳 CQL 參數的輸入、腫瘤 id 由各伺服器自訂，而且無法驗證與稽核，因此改為資料。
- **收錄起始日（2024-01-01）**：收錄資料說明第一點「自 113 年 1 月 1 日起新診斷個案」屬於 115 年指標定義本身，寫在 CQL define `Collection Start Date`，不由呼叫端提供。若作為參數，同一版 Measure 可被算出不同結果；MeasureReport 的標準欄位只記錄 `Measure|version`（參數值須另以 `cqf-inputParameters` extension 記錄），結果難以重現；R4 `$evaluate-measure` 也沒有傳 CQL 參數的標準輸入。Measure 與 Library 版本一律同步（目前皆為 `0.1.0-preview.2`，由測試檢查），Measure 版本因此對應唯一一版 CQL。Measure.library 未帶 `|version`：IG Publisher 3.0.5 的 Measure 頁面無法解析帶版本的 library canonical（population 連結全部失效），部署時應載入同版的 Library。年度改版的修改點見下方「年度改版檢查清單」。
- **5.4 生存狀態的死亡代碼**：長表摘錄手冊（民國 114 年版）第 314 頁規定 `0`＝死亡、`1`＝存活，CQL 直接使用，不由呼叫端提供。早期版本以參數提供且預設 `true`，若呼叫端沿用預設值，「治療前已死亡」的 (b)、(c) 永遠不成立而不會報錯，因此移除。

### 年度改版檢查清單

國健署公告新年度指標時，除了依修訂對照表修改 CQL 邏輯外，下列各處須一併檢查：

- **收錄起始日**：CQL `Collection Start Date`；參考實作 `reference/cohort.py` 的 `REGISTRY_START`；三個 Measure 的 narrative（`ig/input/fsh/measures.fsh`「2024-01-01 起新診斷」）；`inclusion-rules.md` IP-DXDATE、`case-assembly.md` 步驟 3；`mappings/crc-core-indicator-criteria.csv` IP-DXDATE；合成個案 `ip-dx-before-collection-start`、`ip-dx-on-collection-start`（`scripts/build_fixtures.py`）。
- **版本**：`sushi-config.yaml`、CQL `library` 宣告、`measures.fsh`（Measure.version）、`conceptmaps.fsh`、`index.md`、`scripts/build_fixtures.py`、`scripts/build_terminology.py`；之後重新產生 `measure-reports.fsh` 與 `tests/fixtures/cql/`。
- **適用期間**：Measure.effectivePeriod（見「[已知歧義](known-ambiguities.html)」A-16）。
- **來源**：`sources/` 新年度 PDF 與 SHA256SUMS、`source-traceability.md`、修訂對照頁。

## Artifacts

| 類型 | Artifact |
|---|---|
| Profile | ColorectalCancerPatient、ColorectalCancerPrimaryCondition、CRCTCRDataItemObservation、CRCMalignantPolypCondition、CRCMalignantPolypPathologyReport、CRCPathologyHighRiskFeature、CRCColonoscopyHighRiskFeature、CRCCurativeResectionProcedure、CRCOutsideDataExclusion（第五點外院資料） |
| Extension | CRCHistologyMorphologyBehavior（ICD-O-3 組織型態與性態） |
| CodeSystem | crc-tcr-field（癌登欄位）、crc-indicator-concept（指標 1 本地概念）、crc-outside-data（第五點排除的指標與理由）、fixture-tag |
| Library | ColorectalCancerCoreIndicators |
| Measure | crc-qi-01、crc-qi-02、crc-qi-03 |
