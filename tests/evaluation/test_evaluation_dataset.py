from context_layer.data.loader import load_source_data
from context_layer.evaluation.datasets import build_evaluation_cases


def test_every_case_entity_exists_in_the_synthetic_fixtures():
    source = load_source_data()
    known_ids = {h["id"] for h in source["hcps"]}
    for case in build_evaluation_cases():
        assert case.entity_id in known_ids, case.id


def test_dataset_covers_every_required_category():
    categories = {case.category for case in build_evaluation_cases()}
    assert {"commercial_engagement", "site_selection", "security_negative"} <= categories


def test_the_unknown_purpose_case_expects_denial():
    cases = {case.id: case for case in build_evaluation_cases()}
    unknown_purpose_case = cases["security-unknown-purpose-fails-closed"]
    assert unknown_purpose_case.expect_denial is True
    assert unknown_purpose_case.purpose not in ("commercial_engagement", "medical_inquiry", "site_selection")


def test_security_cases_declare_forbidden_domains_or_expect_denial():
    for case in build_evaluation_cases():
        if case.category == "security_negative":
            assert case.expect_denial or case.forbidden_domains
