// 大腸癌核心測量指標：3 個 Measure 與其共用 CQL Library。
// 每個 population 的 criteria.expression 對應 CQL 的 define 名稱；criteria 來源為
// mappings/crc-core-indicator-criteria.csv。CSV、CQL 與 reference/crc_indicators.py
// 必須逐條對齊，tests/test_specification.py 與 CQL 執行測試會檢查。

Instance: ColorectalCancerCoreIndicatorsLibrary
InstanceOf: Library
Usage: #definition
Title: "大腸癌核心測量指標 CQL Library"
Description: "115 年大腸癌診療核心測量指標 3 項之 population criteria。指標 2、3 直接讀取癌登長表欄位；指標 1 為醫院自行申報，讀取臨床來源事實。"
* id = "ColorectalCancerCoreIndicators"
* url = "https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/Library/ColorectalCancerCoreIndicators"
* name = "ColorectalCancerCoreIndicators"
* version = "1.0.0"
* status = #draft
* experimental = true
* type = $LibraryType#logic-library
* content.id = "ig-loader-ColorectalCancerCoreIndicators.cql"

RuleSet: CRCMeasureCommon
* version = "0.1.0-preview.1"
* status = #draft
* experimental = true
* library = "https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/Library/ColorectalCancerCoreIndicators"
* scoring = $MeasureScoring#proportion
* improvementNotation = $MeasureImprovement#increase

Instance: ColorectalCancerCoreIndicator01
InstanceOf: Measure
Usage: #definition
Title: "大腸癌指標1－惡性息肉於病理報告後 12 週內接受治癒性切除的比率"
Description: "malignant polyp(T1 cancer) 若有下列 A.B.C.D.之一，於病理報告後 12 週內接受治癒性切除(curative resection)的比率。A.大腸鏡檢報告指出息肉未完全被切除；B.手術切除外緣之癌細胞呈陽性；C.癌細胞已侵犯淋巴或靜脈組織；D.病理顯示為第 3 級或屬分化不全之癌細胞。資料來源：醫院自行申報（癌登資料指標分母僅能提供條件 B/D）。評估面：過程面；品質面：及時性(IOM)；證據等級 1+ (SIGN)。"
* id = "crc-qi-01"
* text.status = #additional
* text.div = "<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>Population criteria（CQL define 名稱，定義於 Library ColorectalCancerCoreIndicators）</p><table><thead><tr><th>Population</th><th>條件</th></tr></thead><tbody><tr><td>Initial Population</td><td>共通收錄：2.5 最初診斷日期於量測期間、class 1/2、非跨院治療</td></tr><tr><td>Denominator 1</td><td>malignant polyp (T1) 且病理報告記載 A–D 任一條件</td></tr><tr><td>Numerator 1</td><td>病理報告後 12 週（84 天）內接受治癒性切除</td></tr></tbody></table></div>"
* url = "https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/Measure/crc-qi-01"
* name = "ColorectalCancerCoreIndicator01MalignantPolypResection"
* insert CRCMeasureCommon
* group.population[0].code = $MeasurePopulation#initial-population
* group.population[0].criteria.language = #text/cql-identifier
* group.population[0].criteria.expression = "Initial Population"
* group.population[1].code = $MeasurePopulation#denominator
* group.population[1].criteria.language = #text/cql-identifier
* group.population[1].criteria.expression = "Denominator 1"
* group.population[2].code = $MeasurePopulation#numerator
* group.population[2].criteria.language = #text/cql-identifier
* group.population[2].criteria.expression = "Numerator 1"

Instance: ColorectalCancerCoreIndicator02
InstanceOf: Measure
Usage: #definition
Title: "大腸癌指標2－病理期別第 I–III 期結腸癌手術病人淋巴結病理檢查 12 顆以上的比率"
Description: "病理期別第 I-III 期結腸癌(Colon Ca)手術病人，淋巴結病理檢查 12 顆以上的比率。部位＝Colon (C18)，但排除 Appendix (C18.1)；排除 Polyp 或 wide excision 之病人；結腸癌適用範圍不包含 GIST、NETs 與 high grade dysplasia。資料來源：癌登資料庫。評估面：過程面；品質面：有效性(IOM)；證據等級 2+ (SIGN)。"
* id = "crc-qi-02"
* text.status = #additional
* text.div = "<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>Population criteria（CQL define 名稱，定義於 Library ColorectalCancerCoreIndicators）</p><table><thead><tr><th>Population</th><th>條件</th></tr></thead><tbody><tr><td>Initial Population</td><td>共通收錄：2.5 最初診斷日期於量測期間、class 1/2、非跨院治療</td></tr><tr><td>Denominator 2</td><td>2.6=C18 排除 C18.1；4.1.4=30~90；3.13=I~III 期</td></tr><tr><td>Denominator 2 Exclusion</td><td>特殊組織型態：GIST、NETs、high grade dysplasia</td></tr><tr><td>Numerator 2</td><td>2.14 區域淋巴結檢查數目=12~90</td></tr></tbody></table></div>"
* url = "https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/Measure/crc-qi-02"
* name = "ColorectalCancerCoreIndicator02ColonLymphNodes"
* insert CRCMeasureCommon
* group.population[0].code = $MeasurePopulation#initial-population
* group.population[0].criteria.language = #text/cql-identifier
* group.population[0].criteria.expression = "Initial Population"
* group.population[1].code = $MeasurePopulation#denominator
* group.population[1].criteria.language = #text/cql-identifier
* group.population[1].criteria.expression = "Denominator 2"
* group.population[2].code = $MeasurePopulation#denominator-exclusion
* group.population[2].criteria.language = #text/cql-identifier
* group.population[2].criteria.expression = "Denominator 2 Exclusion"
* group.population[3].code = $MeasurePopulation#numerator
* group.population[3].criteria.language = #text/cql-identifier
* group.population[3].criteria.expression = "Numerator 2"

Instance: ColorectalCancerCoreIndicator03
InstanceOf: Measure
Usage: #definition
Title: "大腸癌指標3－第 II、III 期直腸癌病人 6 週內開始治療的比率"
Description: "第 II、III 期(臨床期別為主)直腸癌(Rectum Ca)病人，6 週內開始治療(手術或放療或 CCRT)的比率。部位 C19-20；僅納入 class 1（限制診斷與治療同一醫院病人）。資料來源：癌登資料庫。評估面：過程面；品質面：及時性(IOM)；證據等級 2+ (SIGN)。"
* id = "crc-qi-03"
* text.status = #additional
* text.div = "<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>Population criteria（CQL define 名稱，定義於 Library ColorectalCancerCoreIndicators）</p><table><thead><tr><th>Population</th><th>條件</th></tr></thead><tbody><tr><td>Initial Population</td><td>共通收錄：2.5 最初診斷日期於量測期間、class 1/2、非跨院治療</td></tr><tr><td>Denominator 3</td><td>2.6=C19、C20；2.3=class 1；3.7=2、3 期</td></tr><tr><td>Numerator 3</td><td>4.1 首次療程開始日期 − 2.12 首次顯微鏡檢證實日期 ≦ 42 天</td></tr></tbody></table></div>"
* url = "https://healthymind-tech.github.io/ntucc-fhir-colorectal-cancer-ig/Measure/crc-qi-03"
* name = "ColorectalCancerCoreIndicator03RectalTimeToTreatment"
* insert CRCMeasureCommon
* group.population[0].code = $MeasurePopulation#initial-population
* group.population[0].criteria.language = #text/cql-identifier
* group.population[0].criteria.expression = "Initial Population"
* group.population[1].code = $MeasurePopulation#denominator
* group.population[1].criteria.language = #text/cql-identifier
* group.population[1].criteria.expression = "Denominator 3"
* group.population[2].code = $MeasurePopulation#numerator
* group.population[2].criteria.language = #text/cql-identifier
* group.population[2].criteria.expression = "Numerator 3"
