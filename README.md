# NTUCC FHIR Colorectal Cancer Implementation Guide

**大腸癌診療核心測量指標 FHIR 實作指引（草稿）**

[![Build](https://github.com/healthymind-tech/ntucc-fhir-colorectal-cancer-ig/actions/workflows/build.yml/badge.svg)](https://github.com/healthymind-tech/ntucc-fhir-colorectal-cancer-ig/actions/workflows/build.yml)
[![Publish](https://github.com/healthymind-tech/ntucc-fhir-colorectal-cancer-ig/actions/workflows/pages.yml/badge.svg)](https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/)
![FHIR R4](https://img.shields.io/badge/FHIR-R4%204.0.1-orange)
![Status](https://img.shields.io/badge/status-draft-lightgrey)
![License](https://img.shields.io/badge/license-CC%20BY%204.0-blue)

📖 **IG 網站：<https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/>**

[中文](#中文) · [English](#english)

---

## 中文

### 這是什麼

衛生福利部國民健康署每年公告「癌症診療核心測量指標」，醫院必須依指標定義申報。本專案把 **115 年版的大腸癌 3 項指標**（含 115/06/18 修訂）轉成**可執行、可驗證**的 FHIR 規格：

- **FHIR Measure** 定義每項指標的分子、分母與排除條件
- **CQL** 把官方文字逐條寫成可執行的邏輯
- **Profiles** 描述計算所需的資料長什麼樣子
- **合成測試個案**涵蓋每條規則的邊界值

目標是讓醫院資訊系統能**用同一份規格自動計算指標**，計算結果可以逐條追溯回國健署原文。

### 三項指標

| Measure | 指標 | 資料來源 |
|---|---|---|
| `crc-qi-01` | malignant polyp（T1）若符合 A–D 任一高風險條件，於病理報告後 **12 週內**接受治癒性切除的比率 | 醫院自行申報（臨床資料） |
| `crc-qi-02` | 病理期別第 I–III 期**結腸癌**手術病人，淋巴結病理檢查 **≥12 顆**的比率 | 癌症登記長表 |
| `crc-qi-03` | 第 II、III 期（臨床期別為主）**直腸癌**病人，**6 週內**開始治療的比率 | 癌症登記長表 |

### 設計重點

```text
國健署 PDF 原文（含頁碼）
   └─► mappings/crc-core-indicator-criteria.csv     每條規則一個 criterion_id
         ├─► ig/input/cql/*.cql                     CQL 實作（註解標 criterion_id）
         ├─► reference/crc_indicators.py            獨立 Python 參考實作
         └─► tests/fixtures/synthetic-cases.json    手寫預期值的合成個案
               └─► Python 參考實作、JavaScript 與 Java 兩個 CQL 引擎的結果必須一致
```

- **直接讀癌登欄位**：官方定義寫的就是長表欄位（例如「4.1.4＝30~90」），指標 2、3 直接讀這些欄位，算出來的結果才會和官方核算一致。
- **原值保存**：癌登值以原始字串保存，`00000000`、`99999999` 等特殊值不會被誤判成日期。
- **三方互相驗證**：CQL 與 Python 各自實作同一張規則表，CQL 再分別在 JavaScript 與 Java 兩個引擎上執行，三者對每個個案的結果必須相同。這個機制抓到了多個只在單一實作或單一引擎出現的問題（見「驗證方法」頁）。
- **不替官方做決定**：原文沒寫清楚之處列入「[已知歧義](ig/input/pagecontent/known-ambiguities.md)」，不自行補規則。

### 快速開始

需要：Node.js 20+、Python 3.11+、Java 17+；產出網頁另需 Ruby + Jekyll。

```bash
# 1. FHIR Shorthand → FHIR 資源
cd ig && npm ci --prefix tools && node tools/node_modules/fsh-sushi/dist/app.js . && cd ..

# 2. 產生合成測試資料
python3 scripts/build_fixtures.py

# 3. Python 參考實作與規格一致性測試
python3 -m venv .venv && .venv/bin/pip install -e ".[test]" && .venv/bin/python -m pytest -q

# 4. CQL 翻譯並執行全部合成個案
scripts/run_cql.sh

# 5. 產出 HTML IG（輸出在 ig/output/index.html）
scripts/build_ig.sh
```

> HL7 IG Publisher 不接受路徑中含空格。`scripts/build_ig.sh` 會自動把專案複製到 `/tmp/tw-crc-ig-build` 建置，再把網頁複製回來。

### 驗證狀態

| 檢查 | 結果 |
|---|---|
| SUSHI | 0 errors、0 warnings |
| HL7 IG Publisher 3.0.5 | QA 0 errors、0 broken links（CI 遇到 QA error 或 broken link 即失敗） |
| CQL 翻譯 | 成功 |
| CQL 執行 | 118 個合成個案，JavaScript 與 Java 兩個引擎都與 Python 參考實作一致；重現 3 份摘要 MeasureReport |
| pytest | 371 passed |

每次 push 都由 GitHub Actions 重跑；推送到 `main` 後會自動建置並發布到 GitHub Pages。

### 專案結構

```text
.
├── ig/                          IG 原始檔
│   ├── sushi-config.yaml        IG 設定（canonical、相依套件、選單）
│   ├── input/fsh/               Profiles、CodeSystems、ValueSets、Measures、Examples
│   ├── input/cql/               CQL Library
│   ├── input/pagecontent/       IG 頁面（Markdown）
│   ├── local-template/          繼承 fhir2.base.template，只修正一個上游 layout 錯誤
│   └── tools/                   SUSHI 與 CQL 執行環境
├── mappings/                    規則表、術語候選對應表（單一來源）
├── reference/                   Python 參考實作
├── scripts/                     測試資料產生、CQL 執行、IG 建置
├── sources/hpa-115/             國健署原始 PDF 與 SHA256SUMS
├── OID_ASSIGNMENT.md            OID 根節點與分配規則（register 在 ig/oids.ini）
├── tests/                       pytest 與合成測試個案
└── .github/workflows/           CI 與 GitHub Pages 發布
```

### 尚待確認

正式使用前，請先閱讀「[已知歧義與待確認事項](ig/input/pagecontent/known-ambiguities.md)」。表中為 A 系列共 26 項（A-01～A-26，其中 A-01 已解決）；個案組裝的決定與待確認問題另列於個案組裝頁（C 系列）。主要包括：

- 同一病人多原發大腸癌如何保留個案（A-15，第一優先確認）
- 特殊組織型態排除是否也適用於直腸癌（A-12）
- 指標 1 惡性息肉、條件 A 與治癒性切除的本地概念代碼尚未對應到 SNOMED CT／LOINC（A-07）
- 指標未依醫院分層，一次評估只能涵蓋單一醫院的資料（A-25）

### 擴充到其他癌別

國健署指標共 13 癌、60 項，本專案先做大腸癌。新增癌別時沿用同一模式：規則表加上 criterion → 補上引用的癌登欄位 → CQL 與 Python 各自實作 → 補上邊界值合成個案。

---

## English

### Overview

A FHIR R4 implementation guide that turns the three **colorectal cancer core quality indicators** published by Taiwan's Health Promotion Administration (*2026 Cancer Care Core Measures*, revised 2026-06-18) into executable, testable artifacts:

| Measure | Indicator | Data source |
|---|---|---|
| `crc-qi-01` | Malignant (T1) polyp with any of high-risk features A–D: curative resection within 12 weeks of the pathology report | Hospital-reported clinical facts |
| `crc-qi-02` | Stage I–III colon cancer resection: ≥12 lymph nodes examined | Taiwan Cancer Registry long form |
| `crc-qi-03` | Clinical stage II–III rectal cancer (class 1): treatment started within 42 days of microscopic confirmation | Taiwan Cancer Registry long form |

Each rule in the official text has a `criterion_id` in `mappings/crc-core-indicator-criteria.csv`. The rules are implemented twice, independently, in **CQL** and in a **Python reference implementation**, and both must agree on the same hand-specified synthetic cases (118 at present), checked on two CQL engines (JavaScript and Java). Registry values are kept as raw strings so that special codes such as `99999999` (unknown) are never mistaken for dates.

All clinical profiles derive from **TW Core IG 1.0.0**; only the registry data-item Observation and the outside-data exclusion Observation derive from base R4 Observation, because neither is a clinical result and no TW Core Observation category fits them. See *Quick start* above for build commands; the published site is at <https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/>.

---

## 來源 · Sources

- 衛生福利部國民健康署，〈公告修訂「115年癌症診療核心測量指標」〉，115/04/20 發布、115/06/25 更新：<https://www.hpa.gov.tw/Pages/Detail.aspx?nodeid=129&pid=20013>
- 原始 PDF 與 SHA-256 保存在 [`sources/hpa-115/`](sources/hpa-115/)，用於逐條追溯；檔案內容未經修改。

## 聲明 · Disclaimer

本專案為**非官方草稿**，不是衛生福利部、國民健康署、國家衛生研究院、HL7 International 或 HL7 Taiwan 的出版品，也未經上述機構認可。指標的正式定義以國民健康署公告為準。本專案不得取代官方申報規格、癌症登記長表摘錄手冊或臨床判斷。所有範例與測試資料皆為完全合成，不含任何真實病人資料。

*This is an unofficial draft. It is not endorsed by Taiwan's Ministry of Health and Welfare, the Health Promotion Administration, or HL7. All example and test data are fully synthetic.*

## 授權 · License

原創內容依 [CC BY 4.0](LICENSE) 授權。所引用的第三方文件與規格，權利仍屬各該權利人所有。
