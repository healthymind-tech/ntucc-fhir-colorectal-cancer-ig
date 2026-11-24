{% include disclaimer.md %}

| 文件 | 發布 | SHA-256 |
|---|---|---|
| 115年癌症診療核心測量指標.pdf（59 頁） | 115/04/20 | `4fde49abed511811d98aa9a8db9023b408e0edebc227f24d3f79f1bbed48f7e3` |
| 115年癌症診療核心測量指標 修訂對照表.pdf（41 頁） | 115/04/20 | `7c42f4d4e24962ac6193dae30d8a434c856217275753b1d55fa817157a7bcc54` |
| 附件1_大腸癌公告指標修訂對照表.pdf（2 頁） | 115/06/25 | `d1198d56e3844d5dba19e1633ee214b9f6b0f70fb4c7a15818b6428b414a9d13` |
| 附件2_大腸癌診療公告指標.pdf（5 頁） | 115/06/25 | `efc42f79f1be75a5d8c6dcb8523dbe5b2e841657bb6d6b74e54dd70858e87763` |

- 公告頁：衛生福利部國民健康署「公告修訂『115年癌症診療核心測量指標』」，`https://www.hpa.gov.tw/Pages/Detail.aspx?nodeid=129&pid=20013`，發布單位：癌症防治組。
- 原檔保存在 repository 的 `sources/hpa-115/`，`SHA256SUMS` 由測試檢查。
- 若國健署更新附件，必須同時更新原檔、雜湊值、`mappings/crc-core-indicator-criteria.csv`、CQL、參考實作與測試個案，並在「[115 年修訂重點](revision-115.html)」記錄差異。

## 追溯鏈

```text
PDF 原文（頁碼）
  → mappings/crc-core-indicator-criteria.csv（criterion_id、source_page）
    → ig/input/cql/ColorectalCancerCoreIndicators.cql（註解標 criterion_id）
    → reference/crc_indicators.py（註解標 criterion_id）
      → tests/fixtures/synthetic-cases.json（手寫預期值）
        → Measure crc-qi-0x（population.criteria.expression = define 名稱）
```
