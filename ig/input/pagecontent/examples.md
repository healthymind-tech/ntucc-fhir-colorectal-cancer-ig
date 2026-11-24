{% include disclaimer.md %}

本 IG 的所有範例與測試資料皆為**完全合成**，不代表任何真實病人，不可用於臨床或申報。

## IG 範例

| 情境 | 資源 | 預期 |
|---|---|---|
| 直腸癌臨床 2A 期，確診後第 42 天開始治療 | [crc-patient-rectum](Patient-crc-patient-rectum.html) 與其 `crc-tcr-rectum-*` 欄位 | crc-qi-03 分母與分子 |
| 乙狀結腸癌病理 3B 期，部分結腸切除，檢查 15 顆淋巴結 | [crc-patient-colon](Patient-crc-patient-colon.html) 與其 `crc-tcr-colon-*` 欄位 | crc-qi-02 分母與分子 |
| 惡性息肉，大腸鏡未完全切除（條件 A）且切緣陽性（條件 B），病理報告後第 84 天治癒性切除 | [crc-patient-polyp](Patient-crc-patient-polyp.html)、[條件 A](Observation-crc-polyp-feature-a.html)、[條件 B](Observation-crc-polyp-feature-b.html)、[病理報告](DiagnosticReport-crc-polyp-pathology-report.html)、[切除](Procedure-crc-curative-resection.html) | crc-qi-01 分子條件 |

## 測試個案

`tests/fixtures/synthetic-cases.json` 有 44 個合成個案，涵蓋每條規則的邊界值，例如：

- 淋巴結 11／12／90／95 顆
- 手術方式 27／30／90／99
- 第 42 天與第 43 天開始治療
- 病理報告後第 0／84／85 天切除，以及報告前一天切除
- 闌尾 C18.1、帶小數點的部位碼、GIST／NET、跨院治療、class 0／2／3
- 不存在的日期（20250231）

每個個案的預期值都依原文手寫，不從任何一份實作的輸出複製。`scripts/build_fixtures.py` 會把同一批個案轉成 FHIR Bundle，供 CQL 執行測試使用。
