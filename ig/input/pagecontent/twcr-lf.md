{% include disclaimer.md %}

本頁說明本 IG 與「台灣癌症登記長表實作指引」（TWCR_LF）的關係，並列出本 IG 引用的每個長表欄位在 TWCR_LF 中的對應位置。對照表的機器可讀版本為 `mappings/twcr-lf-crosswalk.csv`，以下所有內容均取自 TWCR_LF 0.1.1 套件檔案（`package.json`、`StructureDefinition-TWCRLF.json`、各 profile、extension 與 CodeSystem），不是憑記憶整理。

### TWCR_LF 是什麼

| 項目 | 內容 |
|---|---|
| 名稱 | 台灣癌症登記長表實作指引 (Taiwan Cancer Registry Long Form Implementation Guide) |
| 套件 | `fhir.TWCRLF` 版本 0.1.1（套件日期 2024-08-01） |
| 網站 | <https://mitw.dicom.org.tw/IG/TWCR_LF/> |
| Canonical | `https://hapi.fhir.tw/fhir` |
| FHIR 版本 | R4（4.0.1） |
| 狀態 | 邏輯模型 `status = draft`；`package.json` 標示 `notForPublication: true`；作者欄為個人（Kuo），不是衛生福利部、國民健康署或 HL7 Taiwan 的官方出版物 |
| 相依套件 | 只有 `hl7.fhir.r4.core` 4.0.1、`hl7.terminology.r4` 6.0.2、`hl7.fhir.uv.extensions.r4` 5.1.0；**沒有**相依 TW Core（`tw.gov.mohw.twcore`） |
| 範圍 | 整份癌登長表：邏輯模型 `TWCRLF` 分為個案確認、癌症確認、癌症最初診斷期別、首次療程、結果、個案行政、其他因子、癌症部位特定因子（SSF）八個章節；套件含 77 個 profile、19 個 extension、198 個 CodeSystem 與 198 個 ValueSet |

所有 profile 都直接衍生自 FHIR R4 基礎資源（Condition、Observation、Procedure、Patient、Organization 等），套件中沒有任何 profile 的 `baseDefinition` 指向 TW Core。

### 兩種表示方式的差異

**TWCR_LF：一個欄位一個 profile（或 slice／extension），值轉成代碼。** 每個長表欄位對應到某個 FHIR 資源的特定元素，例如個案分類、診斷狀態分類、治療狀態分類是 `lf-Condition-profile` 的三個 `Condition.category` slice；組織型態與性態碼是 `lf-PrimaryCancer-profile` 上的兩個 extension；首次療程開始日期是 `lf-FirCouOfTreatment-profile`（Procedure）的 `performedPeriod.start`。有代碼表的欄位幾乎都有專屬 CodeSystem，並以 required 強度綁定。

**本 IG：一個欄位一筆 [CRCTCRDataItemObservation](StructureDefinition-crc-tcr-data-item-observation.html)，保存原始字串。** `Observation.code` 為 `crc-tcr-field` 中的欄位序號，`valueString` 原樣保存長表申報值。採用這種做法的原因是國健署核心指標直接以長表原始值定義（例如「2.14 = 12~90」、「4.1.4 < 30」、「個案分類 ∈ {1, 2}」），CQL 需要讀到與申報檔完全相同的值；把值轉成 FHIR 代碼或日期型別再轉回，可能失去資訊。TWCR_LF 本身就有這類例子：

- **2.14 區域淋巴結檢查數目**：CodeSystem 以 `0A` 代表「檢查顆數 1-89 顆」。若以代碼申報，就無法判斷指標 2 的 12~90 門檻；只有使用 `valueQuantity` 才保有顆數。
- **4.1.4 申報醫院原發部位手術方式**：CodeSystem 只有 `00`、`10-19`、`20-80`、`90`、`98`、`99` 六個代碼，`10-19` 與 `20-80` 是「依特定部位編碼」的區間代碼，表示不了大腸癌的部位別手術碼（例如 30、40），因此無法判斷「4.1.4 < 30」。
- **日期欄位**（2.5、2.12、4.1）：TWCR_LF 使用 FHIR `dateTime`／`Period`，沒有說明長表的「不詳」值（例如 `99999999`）如何表示；本 IG 保留原始字串，由 CQL 依指標規則處理。

### 本 IG 不相依、也不繼承 TWCR_LF

本 IG 不把 `fhir.TWCRLF` 列為相依套件，也沒有任何 profile 衍生自 TWCR_LF，原因如下：

1. **非官方草稿、版本早期**：TWCR_LF 為 0.1.1 版，邏輯模型狀態為 draft，套件標示 `notForPublication: true`，並由個人作者發布。
2. **沒有相依 TW Core**：本 IG 的病人、病況等 profile 衍生自 TW Core；TWCR_LF 直接衍生自 FHIR R4 基礎資源，兩者無法在同一條繼承鏈上整合。
3. **未發布於 FHIR 套件登錄**：2026-11-24 查詢 <https://packages.fhir.org/fhir.TWCRLF> 回傳 HTTP 404，`https://packages.fhir.org/catalog?name=fhir.TWCRLF` 回傳空清單（同一 catalog 查詢 `tw.gov` 可找到 TW Core 等其他台灣套件），表示 IG Publisher／SUSHI 無法以套件名稱取得 TWCR_LF。
4. **表示方式不同**：如上所述，本 IG 的指標需要原始長表值，TWCR_LF 的代碼化表示有部分欄位無法還原原始值。

因此本 IG 只把 TWCR_LF 當作**參考文件**：下表讓已採用 TWCR_LF 的系統知道每個欄位在兩邊的位置，方便撰寫轉換程式。

### 代碼表：原始值的意義

本 IG 讀取的是原始代碼，代碼的意義以國民健康署公布之長表摘錄手冊為準。TWCR_LF 的 CodeSystem 收錄了這些代碼表的文字，可作為方便查閱的參考：

- **個案分類（2.3）**，`lf-ClassOfCase-codesystem`：收錄 0、1、2、3、5、7、8、9 共 8 個代碼（沒有 4、6）。指標的共通收錄規則選取 class 1（申報醫院診斷，並於申報醫院接受全部或部份的首次療程）與 class 2（他院診斷，於申報醫院接受全部或部份的首次療程）。
- **診斷狀態分類（2.3.1）**，`lf-ClassOfDiaSta-codesystem`：收錄 1、2、3、5、7、8 共 6 個代碼。代碼 2 為「於他院診斷，因該癌症於首次療程內/未復發/復發狀況不明下，至申報醫院就診」。
- **治療狀態分類（2.3.2）**，`lf-ClassOfTreatSta-codesystem`：收錄 0–9 共 10 個代碼。

共通收錄規則 IP-CROSS（指標說明檔註3）排除「個案分類 2、診斷狀態分類 2、治療狀態分類 3」同時成立的主要治療跨院個案。TWCR_LF 對**治療狀態分類代碼 3** 的說明為：

> 於申報醫院接受部分首次療程，也於他院接受部分首次療程/申報醫院委託他院執行部分放射治療

注意：TWCR_LF 的治療狀態分類代碼 5 與 6 顯示文字相同（皆為「首次療程僅為另類治療」），疑為該套件的錯誤；本 IG 的指標不使用這兩個代碼。

### 欄位對照表

TWCR_LF 欄位位置取自邏輯模型 `StructureDefinition-TWCRLF.json` 的元素說明（例如「2.3.1 診斷狀態分類（Condition Profile.category）」），並逐一核對實際 profile。Profile 與 CodeSystem 的 canonical 前綴皆為 `https://hapi.fhir.tw/fhir/`，下表省略。

| 本 IG 欄位 | 名稱 | TWCR_LF 邏輯模型元素 | TWCR_LF profile | 元素路徑 | 型別 | TWCR_LF CodeSystem |
|---|---|---|---|---|---|---|
| 1.1 | 申報醫院代碼 | `caseConfirmation.organizationIdentifier` | `lf-Organization-profile` | `Organization.identifier` | Identifier | — |
| 2.3 | 個案分類 | `diagnosis.classOfCase` | `lf-Condition-profile` | `Condition.category:ClassOfCase.coding` | CodeableConcept | `lf-ClassOfCase-codesystem` |
| 2.3.1 | 診斷狀態分類 | `diagnosis.classOfDiagnosisStatus` | `lf-Condition-profile` | `Condition.category:ClassOfDiagnosisStatus.coding` | CodeableConcept | `lf-ClassOfDiaSta-codesystem` |
| 2.3.2 | 治療狀態分類 | `diagnosis.classOfTreatmentStatus` | `lf-Condition-profile` | `Condition.category:ClassOfTreatmentStatus.coding` | CodeableConcept | `lf-ClassOfTreatSta-codesystem` |
| 2.5 | 最初診斷日期 | `diagnosis.dateOfInitialDiagnosis` | `lf-DateOfDiaCondition-profile` | `Condition.onset[x]:onsetPeriod.start` | dateTime | — |
| 2.6 | 原發部位 | `primaryCancer.primarySite` | `lf-PrimaryCancer-profile` | `Condition.bodySite:PrimarySite.coding` | CodeableConcept | `lf-PrimarySite-codesystem` |
| 2.8 | 組織型態 | `primaryCancer.histology` | `lf-PrimaryCancer-profile` | `Condition.extension:Histology.value[x]` | CodeableConcept | `lf-Histology-codesystem` |
| 2.9 | 性態碼 | `primaryCancer.behaviorCode` | `lf-PrimaryCancer-profile` | `Condition.extension:BehaviorCode.value[x]` | CodeableConcept | `lf-BehaviorCode-codesystem` |
| 2.12 | 首次顯微鏡檢證實日期 | `cancerConfirmation.dateOfFirstMicroscopicConfirmation` | `lf-DateOfFirMicroConfirm-profile` | `Condition.onset[x]:onsetDateTime` | dateTime | — |
| 2.14 | 區域淋巴結檢查數目 | `regionalLymphNodes.regionalLymphNodesExamined` | `lf-RegLymNodesExa-profile` | `Observation.value[x]:valueQuantity` 或 `:valueCodeableConcept` | Quantity 或 CodeableConcept | `lf-RegLymNodesExa-codesystem` |
| 3.7 | 臨床期別組合 | `clinical.clinicalStage` | `lf-CliStage-profile` | `Observation.value[x]:valueCodeableConcept.coding` | CodeableConcept | `lf-CliStageGroup-codesystem` |
| 3.13 | 病理期別組合 | `pathologic.pathologicStage` | `lf-PathStage-profile` | `Observation.value[x]:valueCodeableConcept.coding` | CodeableConcept | `lf-PathStageGroup-codesystem` |
| 4.1 | 首次療程開始日期 | `firstCourseOfTreatment.firstCourseOfTreatmentDate` | `lf-FirCouOfTreatment-profile` | `Procedure.performed[x]:performedPeriod.start` | dateTime | — |
| 4.1.4 | 申報醫院原發部位手術方式 | `surgicalProcedureOfPrimarySite.surgicalProcedureOfPrimarySiteAtThisFacility` | `lf-SurProcOfPriSite-profile` | `Procedure.code.coding` | CodeableConcept | `lf-SurProcOfPriSite-codesystem` |
| 5.3 | 最後聯絡或死亡日期 | `outcome.dateOfLastContactOrDeath` | `lf-Patient-profile` | `Patient.extension:LastContactOrDeath`（valueDateTime） | dateTime | — |
| 5.4 | 生存狀態 | `outcome.vitalStatus` | `lf-Patient-profile` | `Patient.deceased[x]:deceasedBoolean` | boolean（邏輯模型標為 dateTime，與對應元素不一致） | —（TWCR_LF 未提供代碼表） |

### 對照時發現的問題

- **2.3、2.3.1、2.3.2 在同一個 Condition**：三者是 `lf-Condition-profile` 的 `Condition.category` slice（category 最少 3 筆），與承載原發部位、組織型態的 `lf-PrimaryCancer-profile` 是不同的 Condition 資源。轉換時需先確認兩個 Condition 屬於同一顆原發腫瘤。
- **2.12 邏輯模型說明與實際 profile 不一致**：邏輯模型寫「Date Of Diagnosis Condition Profile.onsetDateTime」，但 `lf-DateOfDiaCondition-profile` 只定義 `onsetPeriod`（2.5 使用）。實際承載 2.12 的是 `lf-DateOfFirMicroConfirm-profile` 的 `onsetDateTime`，Bundle、Composition profile 與範例也使用這個 profile，本表採用實際 profile。
- **2.14 型別不一致**：邏輯模型型別為 Quantity，說明卻寫 valueCodeableConcept；profile 兩者都開放。指標需要實際顆數，應使用 `valueQuantity`。
- **2.6 原發部位代碼**不含小數點（例如 `C187`、`C209`），與長表原始值寫法相同；本 IG 的 CQL 比較時也去掉小數點。
- **3.7、3.13** 的 profile 另要求 AJCC 版本（`Observation.method`）及 T、N、M 三筆 `hasMember`，只有期別組合的資料無法通過 TWCR_LF 驗證。
- **4.1.4** 的 CodeSystem 只有區間代碼，見上文。
