{% include disclaimer.md %}

來源：「115 年癌症診療核心測量指標」壹、收錄資料說明（第 i–ii 頁）。

## 計算單位與 population basis

原文的分子與分母都是「…的人數」。依註1，同一醫院內同一人、同一癌別只保留一筆個案，所以在同一醫院內，計數保留下來的個案就等於計數人數。三個 Measure 的 population basis 設為 `Condition`（保留下來的那顆原發腫瘤），目的是讓每個癌登欄位正確歸屬到該筆個案：一顆腫瘤的欄位不會被讀成另一顆的。同院同步結腸癌與直腸癌屬同一癌別，只保留一筆（見「[個案組裝](case-assembly.html)」C-01）；由不同醫院申報時則各自計算。

癌登欄位以 `Observation.focus` 歸屬到腫瘤；同一欄位有多筆申報值時取 `issued` 最晚者（criterion IP-CURRENT）。

### 實作假設

- **一人一個 Patient**：去重在 CQL 的 Patient context 內進行，無法合併同一人的兩個 Patient 資源；送進評估的資料必須先完成病人身分整合（以 1.4 身分證號）。
- **參照**：支援 `Condition/id`、以其結尾的絕對 URL，以及帶 `/_history/n` 的版本參照；`urn:uuid:` 參照需在評估前解析。
- **原始值**：所有癌登值只去除前後的半形空白與 tab，其餘不變，內含空白即為格式錯誤；數字只接受半形 ASCII 數字。
- **病情記錄錯誤**：`verificationStatus` 為 `entered-in-error` 或 `refuted` 的 Condition 不是個案；同時 focus 多個 Condition 的癌登欄位不歸屬任何一方。

| criterion_id | 原文 | 實作位置 | 表達 |
|---|---|---|---|
| IP-DXDATE | 各癌症診療測量指標收錄對象為自 113 年 1 月 1 日起新診斷個案 | CQL `Initial Population` | 最初診斷日期(2.5) 為有效日期、不早於 2024-01-01，且落在 Measurement Period 內 |
| IP-CLASS | 選取個案分類為 class 1、2 者 | CQL `Initial Population` | 個案分類(2.3) ∈ {1, 2} |
| IP-CROSS | 排除主要治療有跨院情形（註3：class 2、診斷狀態 2、治療狀態分類 3） | CQL `Cross Hospital Treatment` | 個案分類(2.3)=2、診斷狀態分類(2.3.1)=2、治療狀態分類(2.3.2)=3 三者同時成立即排除 |
| IP-SCOPE | 註1 以「癌別」判定重複；大腸癌適用 C18（不含 C18.1）與 C19–20 | CQL `Is Colorectal Category` | 2.6 ∈ C18.0、C18.2–C18.9、C19.9、C20.9 |
| IP-DUP | 排除院內重複個案：醫院代碼＋癌別＋身分證號，選診斷較早者；同一天則選期別較嚴重者 | CQL `Is Duplicate` | 演算法見「[個案組裝](case-assembly.html)」 |
| IP-DEATH | 排除治療前已死亡 | CQL `Died Before Treatment` | 依 2.3.2、4.1、5.3、5.4 判定，見「[個案組裝](case-assembly.html)」 |
| IP-OUTSIDE | 外院資料原則（第五點） | CQL 參數 `Outside Data Excluded QI01`／`QI02`／`QI03` | 是否取得外院資料不在癌登欄位中，由醫院逐指標提供要排除的腫瘤 id；自該指標分母移除 |

## 指標專屬的覆寫

- 指標 3 **僅納入 class 1**（「限制診斷與治療同一醫院病人」），比共通的 class 1、2 更窄。

## 外院資料原則（說明檔第五點）

1. 分子與分母皆屬外院資料：不列入計算。
2. 分母屬本院、分子屬外院：申報醫院**能取得**外院處置資訊時，必須納入分子與分母；只知道病人屬於分母對象、卻取不到外院分子資料時，不列入計算。

第 2 點取決於資料是否取得，無法從癌登資料判斷，因此由醫院逐指標提供排除清單（CQL 參數 `Outside Data Excluded QI0n`），CQL 據以自該指標分母移除。

## 期別

說明檔第七點：涉及手術處置、病理報告資訊的指標，除非個別指標另有規定，否則期別指病理分期。指標 2 用病理期別組合(3.13)；指標 3 明文寫「臨床期別為主」，因此用臨床期別組合(3.7)。
