{% include disclaimer.md %}

| 層次 | 工具 | 檢查內容 |
|---|---|---|
| FSH | SUSHI 3.20.0 | 0 errors、0 warnings |
| CQL 翻譯 | cql-to-elm-cli 3.26.0 | 翻譯成功且無 error |
| CQL 執行（JavaScript） | cql-execution 3.3.2、cql-exec-fhir 2.1.6 | 90 個合成個案，每個個案的 8 個 population 都與 Python 參考實作的結果逐一比對；另以全部個案彙總，必須重現 3 份摘要 MeasureReport 的計數 |
| CQL 執行（Java 參考引擎） | info.cqframework engine-fhir 3.26.0 | 同一批 90 個個案、同樣比對 Python 參考實作；JavaScript 與 Java 兩個引擎必須得到相同結果 |
| 參考實作 | pytest | Python 參考實作（`reference/crc_indicators.py`、`reference/cohort.py`）通過手寫預期值；產生 CQL 測試資料時，參考實作的結果若與手寫預期值不符，建置即失敗 |
| IG Publisher | HL7 IG Publisher 3.0.5（鎖定版本） | QA 0 errors、0 broken links。Publisher 即使有 QA 錯誤仍會回傳成功，因此 `scripts/check_qa.py` 讀取 `qa.json`，只要有任何 error、broken link，或報告格式缺少預期欄位，就讓建置失敗 |
| 術語候選 | pytest、`scripts/verify_terminology.py` | CSV 格式、ConceptMap 與審核表由 CSV 產生且一致；`verify_terminology.py` 連線 tx.fhir.org 確認每個候選代碼存在、為 active、名稱未變（需網路，不在 CI 中執行） |
| OID | pytest、CI | OID 根節點由 canonical URL 推導；`ig/oids.ini` 涵蓋所有 canonical 資源、無重複、都在根節點之下；CI 建置若分配了未 commit 的 OID 即失敗 |
| 規格一致性 | pytest | criterion_id 唯一；CSV 指向的 define 存在；已實作的 criterion 同時出現在 CQL 與 Python 中；Measure 的 population 都對應到 define；來源 PDF 的 SHA-256 吻合 |

## 本機執行

```bash
# 1. FSH → FHIR
cd ig && npm ci --prefix tools && node tools/node_modules/fsh-sushi/dist/app.js . && cd ..
# 2. 測試資料
python3 scripts/build_fixtures.py
# 3. Python 參考實作與規格一致性
python3 -m pytest -q
# 4. CQL 翻譯與執行：JavaScript 引擎，再以 Java 參考引擎交叉驗證（需 Java 17+）
scripts/run_cql.sh
scripts/run_cql_java.sh
# 5. HTML IG（需 Ruby + Jekyll）
scripts/build_ig.sh
```

## 驗證找到的問題

以下問題都是由測試或獨立驗證找到，並已修正：

- **計算單位與欄位歸屬**：舊版 CQL 以病人為單位、未使用 `focus`，且以未排序清單的第一筆為欄位值；同一病人兩顆原發腫瘤，或同一欄位有 final 與 amended 兩筆時，結果不確定。
- **原始值正規化不一致**：CQL 與 Python 對空白、全形數字的處理不同，獨立驗證以 49 個對抗性個案找出 17 個不一致；現已統一為「只去除前後半形空白，只接受半形數字」。
- **JavaScript 引擎的陷阱**：`Version`、`Code` 是 CQL 保留字；以 FHIR `id` 元素排序比的是物件而非字串；`Coalesce` 的參數若是 List 會被展開成元素；未提供、無預設值的參數不是 null。
- **測試資料產生器的錯誤**：變數重複命名讓惡性息肉代碼寫到別的資源上；Python 參考實作讀的是抽象事實，所以只有讀 FHIR 資料的 CQL 抓得到。這正是讓兩個 CQL 引擎直接對照參考實作結果的原因。

開發過程中，CQL 執行測試抓到 JavaScript 引擎**不會拒絕** `Date(2025, 2, 31)`，`20250231` 因此會被算成有效日期並計入指標 3 的分子。現在的 `Registry Date` 函式會先明確檢查該月的天數。這正是需要兩份實作互相驗證的原因。
