// ICD-O-3 coding of the primary tumour, for international semantic interoperability.
//
// The registry Observations keep the raw long-form strings (2.6 "C187", 2.8 "8140",
// 2.9 "3") because the indicators are defined on them. The same facts are also
// carried here as ICD-O-3 codes on the Condition, following the shape mCODE uses
// for PrimaryCancerCondition (bodySite for topography, an extension for
// histology-morphology-behavior). The transformation is deterministic; see the
// TCR field page.

Alias: $ICDO3 = http://terminology.hl7.org/CodeSystem/icd-o-3

Extension: CRCHistologyMorphologyBehavior
Id: crc-histology-morphology-behavior
Title: "Histology Morphology Behavior (ICD-O-3)"
Description: "原發腫瘤的 ICD-O-3 組織型態與性態碼（例如 8140/3），由癌登 2.8 組織型態與 2.9 性態碼組成。語意對應 mCODE 的 HistologyMorphologyBehavior extension；本 IG 不相依 mCODE（美國 realm），因此另行定義。"
* ^status = #draft
* ^experimental = true
* ^language = #zh-TW
* ^context[0].type = #element
* ^context[0].expression = "Condition"
* value[x] only CodeableConcept
* valueCodeableConcept 1..1
* valueCodeableConcept.coding 1..*
* valueCodeableConcept.coding ^slicing.discriminator.type = #value
* valueCodeableConcept.coding ^slicing.discriminator.path = "system"
* valueCodeableConcept.coding ^slicing.rules = #open
* valueCodeableConcept.coding contains icdo3 1..1 MS
* valueCodeableConcept.coding[icdo3].system = $ICDO3 (exactly)
* valueCodeableConcept.coding[icdo3].code 1..1
* valueCodeableConcept.coding[icdo3].code ^short = "ICD-O-3 morphology/behavior，例如 8140/3"
* valueCodeableConcept.coding[icdo3].code obeys crc-icdo3-morphology-format

Invariant: crc-icdo3-morphology-format
Description: "ICD-O-3 morphology/behavior 須為 4 位組織型態碼、斜線、1 位性態碼（例如 8140/3）。"
Severity: #error
Expression: "matches('^[0-9]{4}/[0-36]$')"

Invariant: crc-icdo3-topography-format
Description: "ICD-O-3 topography 須為 C、2 位數字、小數點、1 位數字（例如 C18.7）。"
Severity: #error
Expression: "matches('^C[0-9]{2}[.][0-9]$')"
