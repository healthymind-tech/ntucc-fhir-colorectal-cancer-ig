"""Case assembly (reference/cohort.py) against hand-written expectations."""

from datetime import date

import pytest

from reference import cohort as c
from reference.cohort import assemble_cohort, cancer_category, died_before_treatment, stage_rank

PERIOD = (date(2024, 1, 1), date(2024, 12, 31))


def rec(tid, patient="A123456789", hospital="H1", **fields):
    base = {
        "2.3": "1",
        "2.3.1": "1",
        "2.3.2": "1",
        "2.5": "20240301",
        "2.6": "C187",
        "3.7": "2A",
        "3.13": "2A",
        "4.1": "20240310",
        "5.3": "20250101",
        "5.4": "1",
    }
    base.update({k.replace("_", "."): v for k, v in fields.items()})
    return {"tumour_id": tid, "patient_id": patient, "hospital_id": hospital, "fields": base}


def run(*records, **kw):
    kw.setdefault("period", PERIOD)
    return assemble_cohort(list(records), **kw)


# --- cancer_category -------------------------------------------------------
@pytest.mark.parametrize(
    "site,expected",
    [
        ("C180", "大腸癌"),
        ("C182", "大腸癌"),
        ("C187", "大腸癌"),
        ("C189", "大腸癌"),
        ("C18.7", "大腸癌"),
        (" c199 ", "大腸癌"),
        ("C199", "大腸癌"),
        ("C209", "大腸癌"),
        ("C181", None),  # appendix: 附件2 適用範圍 excludes it
        ("C210", None),  # anus: not in any HPA 115 site list
        ("C218", None),
        ("C160", None),
        ("C50", None),
        ("", None),
        (None, None),
    ],
)
def test_cancer_category(site, expected):
    assert cancer_category(site) == expected


def test_anus_and_appendix_are_flagged():
    r = run(rec("ANUS", **{"2_6": "C211"}), rec("APP", patient="B1", **{"2_6": "C181"}))
    assert r.excluded == {"ANUS": c.NOT_COLORECTAL, "APP": c.NOT_COLORECTAL}
    assert c.FLAG_ANUS_EXCLUDED in r.flags["ANUS"]
    assert c.FLAG_APPENDIX_EXCLUDED in r.flags["APP"]


# --- stage ordering ---------------------------------------------------------
def test_stage_order_colorectal_codes():
    codes = ["0", "1", "2A", "2B", "2C", "3A", "3B", "3C", "4A", "4B", "4C"]
    ranks = [stage_rank(x) for x in codes]
    assert ranks == sorted(ranks) and len(set(ranks)) == len(ranks)


def test_stage_bare_group_below_its_substages_above_previous_group():
    assert stage_rank("2C") < stage_rank("3") < stage_rank("3A")
    assert stage_rank("4") < stage_rank("4A")


@pytest.mark.parametrize("code", ["888", "999", "BBB", "OC", "", None, "X", "5"])
def test_unrankable_stage(code):
    assert stage_rank(code) is None


def test_severity_prefers_pathological_then_clinical():
    assert c.severity({"3.13": "1", "3.7": "4A"}) == (stage_rank("1"), "3.13")
    assert c.severity({"3.13": "999", "3.7": "4A"}) == (stage_rank("4A"), "3.7")
    assert c.severity({"3.13": "888"}) == (None, None)


# --- 註1 duplicates ----------------------------------------------------------
def test_single_record_is_eligible():
    r = run(rec("T1"))
    assert r.eligible == ["T1"] and r.excluded == {} and r.flags == {}


def test_duplicate_keeps_earliest_diagnosis():
    r = run(rec("T1", **{"2_5": "20240601", "3_13": "4A"}), rec("T2", **{"2_5": "20240315", "3_13": "1"}))
    assert r.eligible == ["T2"]
    assert r.excluded == {"T1": "DUPLICATE_OF:T2"}
    assert "T2" not in r.flags  # decided by the official rule, no tie flag


def test_same_day_keeps_more_severe_pathological_stage():
    r = run(rec("T1", **{"3_13": "2A", "3_7": "4C"}), rec("T2", **{"3_13": "3B", "3_7": "1"}))
    assert r.eligible == ["T2"]
    assert r.excluded == {"T1": "DUPLICATE_OF:T2"}
    assert c.FLAG_TIE_BROKEN_BY_STAGE in r.flags["T2"]


def test_same_day_pathological_unknown_falls_back_to_clinical():
    r = run(rec("T1", **{"3_13": "999", "3_7": "4A"}), rec("T2", **{"3_13": "3C", "3_7": "3C"}))
    assert r.eligible == ["T1"]
    assert r.excluded == {"T2": "DUPLICATE_OF:T1"}
    assert c.FLAG_STAGE_BASIS_CLINICAL in r.flags["T1"]


def test_same_day_unrankable_stage_loses_to_any_known_stage():
    r = run(rec("T1", **{"3_13": "999", "3_7": "999"}), rec("T2", **{"3_13": "0", "3_7": "0"}))
    assert r.eligible == ["T2"]
    assert c.FLAG_STAGE_UNRANKABLE in r.flags["T1"]


def test_same_day_same_stage_tie_broken_by_smallest_tumour_id():
    r = run(rec("T9"), rec("T10"), rec("T2"))
    # string order: "T10" < "T2" < "T9"
    assert r.eligible == ["T10"]
    assert r.excluded == {"T2": "DUPLICATE_OF:T10", "T9": "DUPLICATE_OF:T10"}
    assert c.FLAG_TIE_BROKEN_BY_TUMOUR_ID in r.flags["T10"]


def test_same_day_both_unknown_stage_tie_broken_by_tumour_id():
    r = run(rec("B", **{"3_13": "888", "3_7": "999"}), rec("A", **{"3_13": "999", "3_7": ""}))
    assert r.eligible == ["A"]
    assert c.FLAG_TIE_BROKEN_BY_TUMOUR_ID in r.flags["A"]


def test_synchronous_colon_and_rectum_are_one_category():
    colon = rec("COLON", **{"2_6": "C187", "3_13": "2A"})
    rectum = rec("RECT", **{"2_6": "C209", "3_13": "3B"})
    r = run(colon, rectum)
    assert r.eligible == ["RECT"]
    assert r.excluded == {"COLON": "DUPLICATE_OF:RECT"}


def test_two_colon_primaries_different_segments_are_duplicates():
    r = run(rec("CEC", **{"2_6": "C180", "2_5": "20240201"}), rec("SIG", **{"2_6": "C187", "2_5": "20240202"}))
    assert r.eligible == ["CEC"] and r.excluded == {"SIG": "DUPLICATE_OF:CEC"}


def test_different_hospitals_are_not_duplicates():
    r = run(rec("H1T", hospital="H1"), rec("H2T", hospital="H2"))
    assert r.eligible == ["H1T", "H2T"] and r.excluded == {}


def test_different_patients_are_not_duplicates():
    r = run(rec("P1", patient="A1"), rec("P2", patient="A2"))
    assert r.eligible == ["P1", "P2"]


def test_dedup_key_normalises_case_and_whitespace():
    r = run(rec("T1", patient="a123456789 "), rec("T2", patient="A123456789", **{"2_5": "20240401"}))
    assert r.excluded == {"T2": "DUPLICATE_OF:T1"}


def test_colorectal_and_other_cancer_same_patient_not_duplicates():
    r = run(rec("CRC"), rec("STOM", **{"2_6": "C169", "2_5": "20240101"}))
    assert r.eligible == ["CRC"] and r.excluded == {"STOM": c.NOT_COLORECTAL}


def test_representative_failing_class_does_not_promote_duplicate():
    early = rec("EARLY", **{"2_5": "20240201", "2_3": "3"})
    late = rec("LATE", **{"2_5": "20240501"})
    r = run(early, late)
    assert r.eligible == []
    assert r.excluded == {"EARLY": c.CLASS_NOT_1_OR_2, "LATE": "DUPLICATE_OF:EARLY"}


def test_invalid_date_record_cannot_win_dedup():
    r = run(rec("UNK", **{"2_5": "99999999"}), rec("OK", **{"2_5": "20240901"}))
    assert r.eligible == ["OK"] and r.excluded == {"UNK": c.INVALID_DIAGNOSIS_DATE}


def test_pre_2024_record_is_not_in_dedup_universe():
    r = run(rec("OLD", **{"2_5": "20231231"}), rec("NEW", **{"2_5": "20240102"}))
    assert r.eligible == ["NEW"] and r.excluded == {"OLD": c.DIAGNOSIS_BEFORE_COLLECTION_START}


def test_out_of_period_record_is_not_in_dedup_universe():
    r = run(rec("NEXT", **{"2_5": "20250105"}), rec("IN", **{"2_5": "20241230"}))
    assert r.eligible == ["IN"] and r.excluded == {"NEXT": c.OUTSIDE_MEASUREMENT_PERIOD}


def test_no_period_only_applies_2024_floor():
    r = assemble_cohort([rec("T", **{"2_5": "20260101"})])
    assert r.eligible == ["T"]


# --- special date values for 2.5 --------------------------------------------
@pytest.mark.parametrize("raw", ["00000000", "99999999", "20240299", "20249999", "20240231", "2024031", "", "2024-03-01"])
def test_invalid_diagnosis_dates(raw):
    r = run(rec("T", **{"2_5": raw}))
    assert r.excluded == {"T": c.INVALID_DIAGNOSIS_DATE}


def test_missing_diagnosis_date_field():
    record = rec("T")
    del record["fields"]["2.5"]
    assert run(record).excluded == {"T": c.INVALID_DIAGNOSIS_DATE}


# --- missing fields / keys ---------------------------------------------------
def test_missing_site():
    record = rec("T")
    del record["fields"]["2.6"]
    assert run(record).excluded == {"T": c.NOT_COLORECTAL}


@pytest.mark.parametrize("patient,hospital", [(None, "H1"), ("", "H1"), ("A1", None), ("A1", "  ")])
def test_missing_dedup_key(patient, hospital):
    r = run(rec("T", patient=patient, hospital=hospital))
    assert r.excluded == {"T": c.MISSING_DEDUP_KEY}


def test_missing_class_excluded():
    record = rec("T")
    del record["fields"]["2.3"]
    assert run(record).excluded == {"T": c.CLASS_NOT_1_OR_2}


def test_missing_stage_fields_single_record_still_eligible():
    record = rec("T")
    del record["fields"]["3.7"], record["fields"]["3.13"]
    assert run(record).eligible == ["T"]


def test_missing_vital_status_is_not_death():
    record = rec("T", **{"4_1": "00000000"})
    del record["fields"]["5.4"]
    assert run(record).eligible == ["T"]


def test_duplicate_tumour_id_rejected():
    with pytest.raises(ValueError):
        run(rec("T"), rec("T", patient="other"))


# --- class and cross-hospital ----------------------------------------------
@pytest.mark.parametrize("klass,ok", [("0", False), ("1", True), ("2", True), ("3", False), ("9", False)])
def test_class_filter(klass, ok):
    r = run(rec("T", **{"2_3": klass}))
    assert (r.eligible == ["T"]) is ok


def test_cross_hospital_treatment_excluded():
    r = run(rec("T", **{"2_3": "2", "2_3_1": "2", "2_3_2": "3"}))
    assert r.excluded == {"T": c.CROSS_HOSPITAL_TREATMENT}


@pytest.mark.parametrize("fields", [{"2_3": "1", "2_3_1": "2", "2_3_2": "3"}, {"2_3": "2", "2_3_1": "1", "2_3_2": "3"}, {"2_3": "2", "2_3_1": "2", "2_3_2": "1"}])
def test_cross_hospital_needs_all_three(fields):
    assert run(rec("T", **fields)).eligible == ["T"]


# --- died before treatment ---------------------------------------------------
DEAD = {"5_4": "0"}  # 長表 5.4: 0 = 死亡


def test_death_before_first_course_date_excluded_and_flagged():
    r = run(rec("T", **DEAD, **{"4_1": "20240320", "5_3": "20240315"}))
    assert r.excluded == {"T": c.DIED_BEFORE_TREATMENT}
    assert c.FLAG_DEATH_BEFORE_FIRST_COURSE_DATE in r.flags["T"]


def test_death_after_treatment_included():
    r = run(rec("T", **DEAD, **{"4_1": "20240320", "5_3": "20240501"}))
    assert r.eligible == ["T"]


def test_death_same_day_as_treatment_included_and_flagged():
    r = run(rec("T", **DEAD, **{"4_1": "20240320", "5_3": "20240320"}))
    assert r.eligible == ["T"]
    assert c.FLAG_SAME_DAY_DEATH_AND_TREATMENT in r.flags["T"]


def test_dead_without_first_course_excluded():
    r = run(rec("T", **DEAD, **{"4_1": "00000000", "5_3": "20240320", "2_3_2": "9"}))
    assert r.excluded == {"T": c.DIED_BEFORE_TREATMENT}
    assert c.FLAG_DIED_BASIS_NO_FIRST_COURSE in r.flags["T"]


def test_dead_without_first_course_and_unknown_death_date_still_excluded():
    r = run(rec("T", **DEAD, **{"4_1": "00000000", "5_3": "99999999", "2_3_2": "9"}))
    assert r.excluded == {"T": c.DIED_BEFORE_TREATMENT}


def test_dead_after_no_treatment_decision_not_excluded():
    # 2.3.2 = 4: first course was 不予治療／密切觀察／緩和 — a treatment decision.
    r = run(rec("T", **DEAD, **{"4_1": "00000000", "5_3": "20240901", "2_3_2": "4"}))
    assert r.eligible == ["T"]


def test_tx_status_0_excluded_even_if_alive_recorded():
    r = run(rec("T", **{"2_3_2": "0", "4_1": "00000000", "5_4": "1"}))
    assert r.excluded == {"T": c.DIED_BEFORE_TREATMENT}
    assert c.FLAG_DIED_BASIS_TX_STATUS_0 in r.flags["T"]


@pytest.mark.parametrize("first,death", [("99999999", "20240320"), ("20240320", "99999999"), ("20240320", "00000000"), ("", "20240320")])
def test_dead_with_unknown_order_not_excluded_but_flagged(first, death):
    r = run(rec("T", **DEAD, **{"4_1": first, "5_3": death}))
    assert r.eligible == ["T"]
    assert c.FLAG_DEATH_ORDER_UNKNOWN in r.flags["T"]


def test_alive_last_contact_before_treatment_is_not_death():
    # 5.3 is the last-contact date when 5.4 says alive.
    r = run(rec("T", **{"5_4": "1", "4_1": "20240320", "5_3": "20240305"}))
    assert r.eligible == ["T"]


def test_alive_without_treatment_is_not_death():
    r = run(rec("T", **{"5_4": "1", "4_1": "00000000"}))
    assert r.eligible == ["T"]


def test_unrecognised_vital_status_flagged_not_dead():
    r = run(rec("T", **{"5_4": "true", "4_1": "00000000"}))
    assert r.eligible == ["T"]
    assert c.FLAG_VITAL_STATUS_UNRECOGNISED in r.flags["T"]


def test_vital_status_default_is_long_form_code_table():
    assert c.DEFAULT_VITAL_STATUS_CODES == {"0": True, "1": False}  # 長表摘錄手冊 p. 314


def test_vital_status_code_table_supplied_by_caller():
    codes = {"0": True, "1": False}
    r = run(rec("D", **{"5_4": "0", "4_1": "00000000", "2_3_2": "9"}), rec("A", patient="B", **{"5_4": "1", "4_1": "00000000"}), vital_status_codes=codes)
    assert r.eligible == ["A"] and r.excluded == {"D": c.DIED_BEFORE_TREATMENT}


def test_died_before_treatment_function_direct():
    assert died_before_treatment({"5.4": "0", "4.1": "00000000"})[0] is True
    assert died_before_treatment({"5.4": "0", "4.1": "20240101", "5.3": "20240102"})[0] is False
    assert died_before_treatment({"5.4": "true", "4.1": "00000000"})[0] is False


def test_death_exclusion_on_representative_does_not_promote_duplicate():
    early = rec("EARLY", **DEAD, **{"2_5": "20240201", "4_1": "00000000", "2_3_2": "0"})
    late = rec("LATE", **{"2_5": "20240301"})
    r = run(early, late)
    assert r.eligible == []
    assert r.excluded == {"EARLY": c.DIED_BEFORE_TREATMENT, "LATE": "DUPLICATE_OF:EARLY"}


# --- 第五點 outside-hospital data --------------------------------------------
def test_outside_data_not_applied_without_mapping():
    assert run(rec("T")).eligible == ["T"]


def test_outside_data_rules():
    records = [rec(t, patient=t) for t in ("IN", "BOTH", "GOT", "MISS", "NONE")]
    status = {
        "IN": c.IN_HOSPITAL,
        "BOTH": c.BOTH_OUTSIDE,
        "GOT": c.NUMERATOR_OUTSIDE_OBTAINED,
        "MISS": c.NUMERATOR_OUTSIDE_NOT_OBTAINED,
    }
    r = run(*records, outside_data=status)
    assert r.eligible == ["GOT", "IN", "NONE"]
    assert r.excluded == {"BOTH": c.OUTSIDE_DATA_BOTH, "MISS": c.OUTSIDE_NUMERATOR_NOT_OBTAINED}
    assert c.FLAG_OUTSIDE_DATA_DEFAULTED in r.flags["NONE"]


def test_outside_data_unknown_status_rejected():
    with pytest.raises(ValueError):
        run(rec("T"), outside_data={"T": "maybe"})


# --- step precedence ---------------------------------------------------------
def test_one_reason_per_tumour_first_failing_step_wins():
    # Not colorectal AND invalid date AND class 3: reported as NOT_COLORECTAL.
    r = run(rec("T", **{"2_6": "C340", "2_5": "99999999", "2_3": "3"}))
    assert r.excluded == {"T": c.NOT_COLORECTAL}


def test_every_record_is_either_eligible_or_excluded():
    records = [
        rec("a"),
        rec("b", **{"2_5": "20240302"}),
        rec("c", patient="X", **{"2_3": "0"}),
        rec("d", patient="Y", **{"2_6": "C211"}),
        rec("e", patient="Z", hospital="H2", **DEAD, **{"4_1": "00000000", "2_3_2": "9"}),
    ]
    r = run(*records)
    assert set(r.eligible) | set(r.excluded) == {"a", "b", "c", "d", "e"}
    assert not set(r.eligible) & set(r.excluded)
    assert r.eligible == ["a"]
    assert r.excluded == {
        "b": "DUPLICATE_OF:a",
        "c": c.CLASS_NOT_1_OR_2,
        "d": c.NOT_COLORECTAL,
        "e": c.DIED_BEFORE_TREATMENT,
    }


def test_input_order_does_not_change_result():
    records = [rec("T3", **{"3_13": "3A"}), rec("T1"), rec("T2", **{"3_13": "3A"})]
    a = run(*records)
    b = run(*reversed(records))
    assert a == b and a.eligible == ["T2"]
