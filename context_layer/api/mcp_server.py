"""Context API — design doc section 6: an MCP server, so any agent runtime
can consume it (design principle #5). Standard MCP tools + resources over
the same ContextAssembler the demo script and tests use directly.

Run with: python -m context_layer.api.mcp_server
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from context_layer.api.app import build_assembler

mcp = FastMCP("life-sciences-context-layer")
_assembler = build_assembler()


@mcp.tool()
def get_context_package(
    entity_id: str, purpose: str, task: str = "", principal: str = "agent", principal_roles: list[str] | None = None
) -> dict:
    """Primary entry point: assemble a policy-scoped Context Package for
    `entity_id` under `purpose`. `task` is free text used only to rank
    recommended content — it never widens access."""
    return _assembler.get_context_package(
        entity_id, purpose, task, principal=principal, principal_roles=principal_roles or []
    )


@mcp.tool()
def find_entities(query: str, entity_type: str, purpose: str) -> list[dict]:
    """Search for entities of `entity_type` (e.g. "Person", "Institution")
    whose display name matches `query`."""
    return _assembler.find_entities(query, entity_type, purpose)


@mcp.tool()
def explain_relationship(entity_a: str, entity_b: str, purpose: str) -> dict:
    """Return the path between two entities within the subgraph(s) and
    bridges permitted for `purpose`, or None if no such path exists."""
    return _assembler.explain_relationship(entity_a, entity_b, purpose)


@mcp.tool()
def find_content(topic: str = "", audience: str = "HCP", approval_status: str = "approved") -> list[dict]:
    """Search approved content by topic/audience. Purpose-agnostic: content
    metadata itself isn't policy-restricted, only which content gets
    recommended within a Context Package is scoped by purpose."""
    return _assembler.find_content(topic, audience, approval_status)


# Resources expose Identity Spine reads only — no purpose parameter,
# because spine data (reference entities, standard-coded attributes) is
# what design doc principle #2 treats as carrying no policy risk. Anything
# domain-scoped (interactions, publications, study assignments) is only
# reachable through the purpose-bound tools above.


@mcp.resource("context://hcp/{hcp_id}")
def hcp_resource(hcp_id: str) -> dict:
    node = _assembler.store.node(hcp_id)
    if node is None or node.get("node_type") != "Person":
        return {"error": f"no HCP {hcp_id}"}
    return {"id": hcp_id, "display": node["display"], "specialty": node.get("specialty")}


@mcp.resource("context://institution/{institution_id}")
def institution_resource(institution_id: str) -> dict:
    node = _assembler.store.node(institution_id)
    if node is None or node.get("node_type") != "Institution":
        return {"error": f"no institution {institution_id}"}
    return {"id": institution_id, "name": node["name"], "mdm_account_id": node.get("mdm_account_id")}


@mcp.resource("context://content/{content_id}")
def content_resource(content_id: str) -> dict:
    node = _assembler.store.node(content_id)
    if node is None or node.get("node_type") != "Content":
        return {"error": f"no content {content_id}"}
    return {
        "id": content_id,
        "title": node["title"],
        "approval_status": node["approval_status"],
        "audience": node["audience"],
    }


if __name__ == "__main__":
    mcp.run()
