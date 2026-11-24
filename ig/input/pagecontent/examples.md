{% include disclaimer.md %}

本 IG 的所有範例與測試資料皆為**完全合成**，不代表任何真實病人，不可用於臨床或申報。

## IG 範例

| 情境 | 資源 | 預期 |
|---|---|---|
| 直腸癌臨床 2A 期，確診後第 42 天開始治療 | [crc-patient-rectum](Patient-crc-patient-rectum.html) 與其 `crc-tcr-rectum-*` 欄位 | crc-qi-03 分母與分子 |
| 乙狀結腸癌病理 3B 期，部分結腸切除，檢查 15 顆淋巴結 | [crc-patient-colon](Patient-crc-patient-colon.html) 與其 `crc-tcr-colon-*` 欄位 | crc-qi-02 分母與分子 |
| 惡性息肉，大腸鏡未完全切除（條件 A）且切緣陽性（條件 B），病理報告後第 84 天治癒性切除 | [crc-patient-polyp](Patient-crc-patient-polyp.html)、[條件 A](Observation-crc-polyp-feature-a.html)、[條件 B](Observation-crc-polyp-feature-b.html)、[病理報告](DiagnosticReport-crc-polyp-pathology-report.html)、[切除](Procedure-crc-curative-resection.html) | crc-qi-01 分子條件 |

## 測試個案

`tests/fixtures/synthetic-cases.json` 收錄涵蓋每條規則邊界值的合成個案，例如：

- 淋巴結 11／12／90／95 顆
- 手術方式 27／30／90／99
- 第 42 天與第 43 天開始治療
- 病理報告後第 0／84／85 天切除，以及報告前一天切除
- 闌尾 C18.1、帶小數點的部位碼、GIST／NET、跨院治療、class 0／2／3
- 不存在的日期（20250231）

每個個案的預期值都依原文手寫，不從任何一份實作的輸出複製。`scripts/build_fixtures.py` 會把同一批個案轉成 FHIR Bundle，供 CQL 執行測試使用。

## 摘要 MeasureReport

`scripts/build_fixtures.py` 也以 Python 參考實作計算全部合成個案，為 3 個指標各產生一份摘要（`type = summary`）MeasureReport，示範輸出格式；CQL 執行測試必須重現其計數與 measureScore。這些數字只反映合成資料，不代表任何醫院的實際表現。

| 指標 | 摘要報告 |
|---|---|
| crc-qi-01 | [synthetic-summary-crc-qi-01](MeasureReport-synthetic-summary-crc-qi-01.html) |
| crc-qi-02 | [synthetic-summary-crc-qi-02](MeasureReport-synthetic-summary-crc-qi-02.html) |
| crc-qi-03 | [synthetic-summary-crc-qi-03](MeasureReport-synthetic-summary-crc-qi-03.html) |
