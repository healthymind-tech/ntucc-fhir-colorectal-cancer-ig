{% include disclaimer.md %}

```text
原始臨床資料（病理報告、大腸鏡檢報告、手術紀錄、放化療紀錄）
        │
        ├──► 大腸癌共同層：ColorectalCancerPatient、ColorectalCancerPrimaryCondition
        │
        ├──► 癌登欄位層：CRCTCRDataItemObservation（一個長表欄位一筆，focus 指向原發腫瘤）
        │         │
        │         └──► 指標 2、3（癌登資料庫）
        │
        └──► 指標 1 臨床事實：CRCMalignantPolypCondition、CRCMalignantPolypPathologyReport、
                  CRCMalignantPolypHighRiskFeature（A–D）、CRCCurativeResectionProcedure
                  │
                  └──► 指標 1（醫院自行申報）

Task 層（評估前）：組 Group、院內重複個案去重、排除治療前死亡
        │
        ▼
Library ColorectalCancerCoreIndicators（CQL）──► Measure crc-qi-01 / 02 / 03 ──► MeasureReport
```

## 為什麼指標 2、3 讀癌登欄位，而不是臨床資源？

國健署文件中，指標 2、3 的「癌登資料選用欄位」已逐條寫出長表欄位與值域（例如「申報醫院原發部位手術方式(4.1.4)＝30~90」）。直接讀取這些欄位，計算結果才能與國健署及癌登中心的核算方式一致。如果改從 Procedure、Observation 等臨床資源推導，每個欄位都要多一層臨床到癌登的轉換，誤差來源也會變多。範例乳癌 IG 的指標 3 就是因為缺少劑量欄位，只能算出上界。

臨床資料轉成癌登欄位（摘錄）屬於癌登 Task 的工作，與本 IG 的指標層分開。

## 為什麼指標 1 不讀癌登欄位？

原文寫明：「癌登資料指標分母僅能提供條件 B/D；條件 A/C 無法由現行癌登資料庫取得」，「癌登資料選用欄位：醫院自行申報」。因此指標 1 讀取臨床來源事實：大腸鏡檢報告（條件 A）、病理報告（條件 B、C、D）及後續手術。

## Artifacts

| 類型 | Artifact |
|---|---|
| Profile | ColorectalCancerPatient、ColorectalCancerPrimaryCondition、CRCTCRDataItemObservation、CRCMalignantPolypCondition、CRCMalignantPolypPathologyReport、CRCMalignantPolypHighRiskFeature、CRCCurativeResectionProcedure |
| CodeSystem | crc-tcr-field（癌登欄位）、crc-indicator-concept（指標 1 本地概念）、fixture-tag |
| Library | ColorectalCancerCoreIndicators |
| Measure | crc-qi-01、crc-qi-02、crc-qi-03 |
