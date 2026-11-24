// 癌症登記長表欄位代碼：只收錄 115 年大腸癌核心測量指標與共通收錄規則實際引用的欄位。
// 代碼即國健署指標文件所寫的長表欄位序號（例如 2.6、4.1.4），方便逐條對回原文。
// 本 CodeSystem 保存「欄位身分」，不取代國健署公布之長表摘錄手冊。

CodeSystem: CRCTCRFieldCodeSystem
Id: crc-tcr-field
Title: "大腸癌核心指標引用之癌登長表欄位"
Description: "115 年大腸癌診療核心測量指標與共通收錄規則所引用的台灣癌症登記長表欄位。代碼為指標文件中的欄位序號；CLASS-DX-STATUS 與 CLASS-TX-STATUS 兩項在指標文件中只有文字描述、沒有欄位序號，因此使用描述性代碼。非官方彙整。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* ^caseSensitive = true
* ^content = #complete
* #2.3 "個案分類"
* #CLASS-DX-STATUS "診斷狀態分類"
    "指標說明檔註3所稱之「診斷狀態」。長表欄位序號待依長表摘錄手冊核對。"
* #CLASS-TX-STATUS "治療狀態分類"
    "指標說明檔註3所稱之「治療狀態分類」。長表欄位序號待依長表摘錄手冊核對。"
* #2.5 "最初診斷日期"
* #2.6 "原發部位"
* #2.8 "組織型態"
* #2.9 "性態碼"
* #2.12 "首次顯微鏡檢證實日期"
* #2.14 "區域淋巴結檢查數目"
* #3.7 "臨床期別組合"
* #3.13 "病理期別組合"
* #4.1 "首次療程開始日期"
* #4.1.4 "申報醫院原發部位手術方式"

ValueSet: CRCTCRFieldValueSet
Id: crc-tcr-field-vs
Title: "大腸癌核心指標癌登欄位值集"
Description: "可作為 CRC TCR Data Item Observation.code 的癌登欄位。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* include codes from system CRCTCRFieldCodeSystem
