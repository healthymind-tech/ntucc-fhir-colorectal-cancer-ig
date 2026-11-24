{% include disclaimer.md %}

本實作指引依衛生福利部國民健康署公告之「**115 年癌症診療核心測量指標**」（115/04/20 發布，115/06/25 更新），把其中**大腸癌 3 項強制申報指標**表達為可執行的 FHIR Measure 與 CQL。架構沿用乳癌 FHIR IG 的分層方式：共同資料層、癌登欄位層、指標層分開管理。

## 版本與基礎

- Package ID：`io.github.healthymind-tech.ntucc-colorectal-cancer`
- Canonical：`https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig`
- 版本：`0.1.0-preview.1`
- 狀態：`draft`／`experimental`
- FHIR：R4 `4.0.1`
- 結構基礎：`tw.gov.mohw.twcore#1.0.0`
- 邏輯表達：CQL 1.5（`hl7.fhir.uv.cql#2.0.0`）

## 三項指標

| Measure | 指標 | 資料來源 |
|---|---|---|
| [crc-qi-01](Measure-crc-qi-01.html) | malignant polyp（T1）若符合 A–D 之一，於病理報告後 12 週內接受治癒性切除的比率 | 醫院自行申報 |
| [crc-qi-02](Measure-crc-qi-02.html) | 病理期別第 I–III 期結腸癌手術病人，淋巴結病理檢查 12 顆以上的比率 | 癌登資料庫 |
| [crc-qi-03](Measure-crc-qi-03.html) | 第 II、III 期（臨床期別為主）直腸癌病人，6 週內開始治療的比率 | 癌登資料庫 |

完整定義見「[大腸癌核心測量指標](indicators.html)」，共通收錄規則見「[共通收錄規則](inclusion-rules.html)」。

## 設計原則

1. **逐字對回原文**：指標 2、3 的 CQL 直接讀取國健署文件寫明的癌登長表欄位（例如 `4.1.4`、`2.14`），欄位代碼就是文件中的欄位序號。
2. **原值保存**：癌登值以 `valueString` 保存原始字串，日期 `00000000`／`99999999` 等特殊值不被推論成日期。
3. **雙實作互驗**：每條規則有 criterion_id；CQL 與 Python 參考實作分別實作同一張規則表，並以同一批合成個案驗證。
4. **不替官方做決定**：原文沒寫清楚之處不自行補規則，列入「[已知歧義](known-ambiguities.html)」。
5. **個案組裝也寫在 Measure 邏輯中**：院內重複個案去重、治療前已死亡等收錄規則都由 CQL 計算（見「[個案組裝](case-assembly.html)」）；只有第五點「外院資料」取決於醫院能否取得資料，由醫院以參數提供排除清單。
