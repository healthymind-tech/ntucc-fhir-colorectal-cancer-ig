{% include disclaimer.md %}

| 層次 | 工具 | 檢查內容 |
|---|---|---|
| FSH | SUSHI 3.20.0 | 0 errors、0 warnings |
| CQL 翻譯 | cql-to-elm-cli 3.26.0 | 翻譯成功且無 error |
| CQL 執行 | cql-execution 3.3.2、cql-exec-fhir 2.1.6 | 44 個合成個案逐一斷言；每個 Measure 引用的 define 對每個個案都實際執行，避免某條分支在執行時才出錯 |
| 參考實作 | pytest | Python 參考實作通過同一批個案；每個分母與分子都有 true 與 false 兩種個案 |
| IG Publisher | HL7 IG Publisher | 49 個資源 0 個驗證錯誤；剩下的 warnings 均已在 `ignoreWarnings.txt` 說明 |
| 規格一致性 | pytest | criterion_id 唯一；CSV 指向的 define 存在；已實作的 criterion 同時出現在 CQL 與 Python 中；Measure 的 population 都對應到 define；來源 PDF 的 SHA-256 吻合 |

## 本機執行

```bash
# 1. FSH → FHIR
cd ig && npm ci --prefix tools && node tools/node_modules/fsh-sushi/dist/app.js . && cd ..
# 2. 測試資料
python3 scripts/build_fixtures.py
# 3. Python 參考實作與規格一致性
python3 -m pytest -q
# 4. CQL 翻譯與執行（需 Java 17+，classpath 解析方式見 .github/workflows/build.yml）
scripts/run_cql.sh
# 5. HTML IG（需 Ruby + Jekyll）
scripts/build_ig.sh
```

## 驗證找到的問題

開發過程中，CQL 執行測試抓到 JavaScript 引擎**不會拒絕** `Date(2025, 2, 31)`，`20250231` 因此會被算成有效日期並計入指標 3 的分子。現在的 `Registry Date` 函式會先明確檢查該月的天數。這正是需要兩份實作互相驗證的原因。
