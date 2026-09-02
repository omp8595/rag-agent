import copy

from context_layer.evaluation.lineage_evaluator import evaluate_lineage


def test_real_package_has_full_lineage_coverage(assembler):
    package = assembler.get_context_package("HCP-001", "commercial_engagement", task="biomarker testing", principal="u", principal_roles=["brand_manager"])
    result = evaluate_lineage(package)
    assert result.lineage_coverage == 1.0
    assert result.orphan_facts == []
    assert result.total_facts == result.facts_with_lineage


def test_a_fact_missing_its_source_is_an_orphan(assembler):
    package = copy.deepcopy(assembler.get_context_package("HCP-001", "commercial_engagement", principal="u", principal_roles=["brand_manager"]))
    package["facts"].append({"claim": "no provenance", "source": "", "domain": "commercial", "confidence": 1.0, "bridge": None})

    result = evaluate_lineage(package)
    assert result.orphan_facts == ["no provenance"]
    assert result.lineage_coverage < 1.0


def test_an_empty_fact_list_has_trivial_full_coverage():
    result = evaluate_lineage({"facts": []})
    assert result.lineage_coverage == 1.0
    assert result.total_facts == 0
