from context_layer.graph.store import Fact
from context_layer.evaluation.graph_evaluator import evaluate_graph
from context_layer.policy.engine import PolicyEngine
from context_layer.policy.models import PolicyRequest


def test_real_commercial_scope_traversal_is_compliant(assembler):
    scope = PolicyEngine().evaluate(
        PolicyRequest(principal="u", principal_roles=["brand_manager"], purpose="commercial_engagement", entity_id="HCP-001")
    )
    result = evaluate_graph(assembler.store, "HCP-001", scope)
    assert result.graph_compliant
    assert result.unauthorized_bridges == []


def test_flags_a_bridge_id_not_in_the_whitelist(assembler, monkeypatch):
    """Proves the check discriminates: a traversal result carrying a
    made-up bridge id must be flagged, not trusted."""
    scope = PolicyEngine().evaluate(
        PolicyRequest(principal="u", principal_roles=["brand_manager"], purpose="commercial_engagement", entity_id="HCP-001")
    )
    fake_facts = [
        Fact(src="HCP-001", dst="PUB-999", edge_type="AUTHORED", domain="medical", attrs={}, bridged_via="not.a.real.bridge")
    ]
    monkeypatch.setattr(assembler.store, "bounded_traversal", lambda *a, **k: fake_facts)

    result = evaluate_graph(assembler.store, "HCP-001", scope)
    assert not result.graph_compliant
    assert result.unauthorized_bridges


def test_flags_a_bridge_used_outside_the_granted_scope(assembler, monkeypatch):
    scope = PolicyEngine().evaluate(
        PolicyRequest(principal="u", principal_roles=["clinical_ops"], purpose="site_selection", entity_id="HCP-001")
    )
    # site_selection grants zero bridges — even a genuinely whitelisted
    # bridge id must be rejected if this scope never granted it.
    fake_facts = [
        Fact(src="HCP-001", dst="PUB-999", edge_type="AUTHORED", domain="medical", attrs={}, bridged_via="medical.publications->commercial")
    ]
    monkeypatch.setattr(assembler.store, "bounded_traversal", lambda *a, **k: fake_facts)

    result = evaluate_graph(assembler.store, "HCP-001", scope)
    assert not result.graph_compliant
