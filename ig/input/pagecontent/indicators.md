{% include disclaimer.md %}

來源：「附件2_大腸癌診療公告指標」（115/06/18 更新），與主文件「貳、三、大腸癌診療」一致。每一列的 criterion_id 都可以在 `mappings/crc-core-indicator-criteria.csv`、CQL 與 Python 參考實作中找到。

## 適用範圍說明（115 年新增）

1. 結腸癌（Colon）：ICD-O-3 編碼為 C18.0–C18.9，**不包含 Appendix C18.1**，也不包含下列特殊組織型態（編碼 988）。
2. 特殊組織型態若為以下類型，各 SSF 欄位應編碼為 988：GIST（M-8935–8936）、NETs（M-8153、8240–8242、8246、8249）、High grade dysplasia（Severe dysplasia）。
3. SSF9 為同步結直腸癌的 SSF 欄位序號；結腸癌的 SSF9 欄位應編碼為 988（不適用）。

## 指標 1：惡性息肉 12 週內治癒性切除 — [crc-qi-01](Measure-crc-qi-01.html)

| 項目 | 內容 |
|---|---|
| 指標屬性 | 評估面：過程面；品質面：及時性(IOM)；正向指標；證據等級 1+ (SIGN) |
| 指標名稱 | malignant polyp (T1 cancer) 若有下列 A.B.C.D. 之一，於病理報告後 12 週內接受治癒性切除 (curative resection) 的比率 |
| 條件 | A. 大腸鏡檢報告指出息肉未完全被切除；B. 手術切除外緣之癌細胞呈陽性；C. 癌細胞已侵犯淋巴或靜脈組織；D. 病理顯示為第 3 級或屬分化不全之癌細胞（112 年修正） |
| 分母 | malignant polyp 病人，病理報告有 A–D 之一記錄的人數 |
| 分子 | 分母中，於病理報告後 12 週內接受治癒性切除的人數 |
| 資料來源 | 醫院自行申報。癌登資料指標分母僅能提供條件 B/D；條件 A/C 無法由現行癌登資料庫取得 |
| 備註 | malignant polyp 指含 T1 adenocarcinoma 的 polyp，**Tis 不算在內** |

| criterion_id | FHIR／CQL 表達 |
|---|---|
| D1-POLYP | 腫瘤本身（`CRCMalignantPolypCondition`，繼承原發腫瘤 Profile）的 code 含 malignant-polyp-t1，且 verificationStatus = confirmed |
| D1-FEATURE | 至少一筆 **focus 指向該腫瘤**的 `CRCColonoscopyHighRiskFeature`（條件 A）或 `CRCPathologyHighRiskFeature`（條件 B–D），valueBoolean = true |
| D1-REPORT | 該腫瘤 `Condition.evidence.detail` 所指、已定稿的 `CRCMalignantPolypPathologyReport`；取最早的 issued 日期 |
| N1-RESECT | **reasonReference 指向該腫瘤**、completed 的 `CRCCurativeResectionProcedure`，日期落在病理報告日起 0–84 天（含） |

所有指標 1 的事實都必須連到**同一顆腫瘤**：病人其他腫瘤的高風險條件、報告或手術不會被算進來。指標 1 雖然是醫院自行申報，共通收錄規則（class 1、2，113 年起新診斷）仍然適用，因此仍需要該腫瘤的癌登欄位 2.3、2.5。

## 指標 2：第 I–III 期結腸癌淋巴結 ≥12 顆 — [crc-qi-02](Measure-crc-qi-02.html)

| 項目 | 內容 |
|---|---|
| 指標屬性 | 評估面：過程面；品質面：有效性(IOM)；正向指標；證據等級 2+ (SIGN) |
| 指標名稱 | 病理期別第 I–III 期結腸癌 (Colon Ca) 手術病人，淋巴結病理檢查 12 顆以上的比率 |
| 分母 | 第 I–III 期結腸癌手術的人數；排除 Polyp 或 wide excision 之病人 |
| 分子 | 分母中，淋巴結病理檢查 12 顆以上的人數 |
| 資料來源 | 癌登資料庫 |

| criterion_id | 癌登欄位條件 | CQL define |
|---|---|---|
| D2-SITE | 部位＝Colon (C18)，但排除 Appendix (C18.1) | `Is Colon Excluding Appendix` |
| D2-SURG | 申報醫院原發部位手術方式(4.1.4)＝30~90 | `Has Resection Surgery 30 To 90` |
| D2-PSTAGE | 病理期別組合(3.13)＝I~III 期 | `Is Pathological Stage I To III` |
| X2-POLYP | 排除 Polyp 或 wide excision（4.1.4 < 30） | 與 D2-SURG 互斥，由 D2-SURG 實現 |
| X2-HIST | 特殊組織型態（GIST、NETs、high grade dysplasia）不屬結腸癌適用範圍 | `Denominator 2 Exclusion` |
| N2-LN12 | 區域淋巴結檢查數目(2.14)＝12~90 | `Numerator 2` |

## 指標 3：第 II、III 期直腸癌 6 週內開始治療 — [crc-qi-03](Measure-crc-qi-03.html)

| 項目 | 內容 |
|---|---|
| 指標屬性 | 評估面：過程面；品質面：及時性(IOM)；正向指標；證據等級 2+ (SIGN) |
| 指標名稱 | 第 II、III 期（臨床期別為主）直腸癌 (Rectum Ca) 病人，6 週內開始治療（手術或放療或 CCRT）的比率 |
| 分母 | 第 II、III 期（臨床期別為主）直腸癌的人數（僅納入 class 1） |
| 分子 | 分母中，6 週內開始治療的人數 |
| 資料來源 | 癌登資料庫 |
| 備註 | 限制診斷與治療同一醫院病人。參考 RAND 2000、SSAT 2000 |

| criterion_id | 癌登欄位條件 | CQL define |
|---|---|---|
| D3-SITE | 部位 C19–20（Rectosigmoid junction & Rectum） | `Is Rectosigmoid Or Rectum` |
| D3-CLASS | 僅納入 class＝1 | `Denominator 3` |
| D3-CSTAGE | 臨床期別組合(3.7)＝2、3 | `Is Clinical Stage II To III` |
| N3-42D | 首次療程開始日期(4.1) − 首次顯微鏡檢證實日期(2.12) ≦ 42 天 | `Numerator 3` |

## 值的判讀

- **期別**：以期別組合值的**第一碼**判斷（`1`、`1A` → I 期；`3C` → III 期）；`0`、`888`、`999` 不屬 I–III 期。
- **部位**：比對前去除小數點（`C18.7` 等同 `C187`）。
- **日期**：只接受實際存在的 `YYYYMMDD`；`00000000`、`99999999`、月或日不詳、或不存在的日期（例如 `20250231`）一律視為無日期，不計入分子。
- **數值欄位**（2.14、4.1.4）：只接受純數字；值域以閉區間比較。
