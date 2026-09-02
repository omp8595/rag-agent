"""Synthetic data generator for the Context Layer prototype.

Produces the Week-1 deliverable from the design doc, section 9:
50 HCPs, 10 institutions, 30 content items, 100 interactions,
40 publications, 5 studies (plus the site/investigator and MSL
interaction records the domain subgraphs need). Deterministic
(fixed seed) so the demo in scripts/demo.py is reproducible.

This data is synthetic and does not represent real people,
institutions, or studies.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

SEED = 42
OUT_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "synthetic"

SPECIALTIES = [
    ("Oncology", "SNOMED:394592004"),
    ("Cardiology", "SNOMED:394579002"),
    ("Endocrinology", "SNOMED:394583002"),
    ("Neurology", "SNOMED:394591006"),
    ("Rheumatology", "SNOMED:394810000"),
]

THERAPEUTIC_AREAS = ["Oncology", "Cardiometabolic", "Immunology", "Neuroscience"]

TOPICS = [
    ("HER2-low breast cancer", "MeSH:D000071243"),
    ("Biomarker testing", "MeSH:D014408"),
    ("Heart failure with preserved ejection fraction", "MeSH:D064894"),
    ("Type 2 diabetes management", "MeSH:D003924"),
    ("Rheumatoid arthritis biologics", "MeSH:D001172"),
    ("Multiple sclerosis relapse prevention", "MeSH:D009103"),
]

FIRST_NAMES = [
    "Aisha", "Raj", "Maria", "Wei", "Chen", "Fatima", "John", "Priya",
    "Carlos", "Emma", "Kenji", "Sofia", "Amir", "Olivia", "Deepa", "Lucas",
    "Nadia", "Hiro", "Elena", "Sam",
]
LAST_NAMES = [
    "Smith", "Iyer", "Garcia", "Zhang", "Wang", "Khan", "Brown", "Rao",
    "Lopez", "Johnson", "Tanaka", "Rossi", "Hussain", "Davies", "Nair",
    "Martin", "Ali", "Sato", "Popescu", "Lee",
]

INSTITUTION_NAMES = [
    "Tata Memorial Hospital", "Mayo Clinic", "Charite Berlin",
    "St. Vincent's Medical Center", "Toronto General Hospital",
    "Royal Marsden", "Cleveland Clinic", "Fudan University Hospital",
    "Karolinska University Hospital", "Peter MacCallum Cancer Centre",
]

CONTENT_TITLES = [
    "Biomarker Testing in Practice: A Clinician's Guide",
    "HFpEF Diagnosis and Management Update",
    "Second-Line Options in HER2-low Breast Cancer",
    "Biologic Selection in Refractory RA",
    "New Data in Relapsing MS: Congress Highlights",
    "T2D: Individualizing Therapy Intensification",
]

CHANNELS = ["email", "rep_visit", "webinar", "conference_booth", "portal_download"]

JOURNALS = ["NEJM", "Lancet Oncology", "JAMA", "Circulation", "Annals of Rheumatic Diseases"]


def _rng() -> random.Random:
    return random.Random(SEED)


def generate_institutions(rng: random.Random) -> list[dict]:
    institutions = []
    for i, name in enumerate(INSTITUTION_NAMES, start=1):
        institutions.append(
            {
                "id": f"INST-{i:03d}",
                "mdm_account_id": f"MDM-ACCT-{i:04d}",
                "name": name,
                "type": rng.choice(["academic_medical_center", "community_hospital", "cancer_center"]),
                "country": rng.choice(["US", "IN", "DE", "CA", "UK", "AU", "SE", "IT"]),
            }
        )
    return institutions


def generate_hcps(rng: random.Random, institutions: list[dict], n: int = 50) -> list[dict]:
    hcps = []
    for i in range(1, n + 1):
        specialty, snomed = rng.choice(SPECIALTIES)
        inst = rng.choice(institutions)
        hcps.append(
            {
                "id": f"HCP-{i:03d}",
                "npi": f"{1000000000 + i}",
                "orcid": f"0000-000{rng.randint(1,9)}-{rng.randint(1000,9999)}-{rng.randint(1000,9999)}",
                "display": f"Dr. {rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                "specialty": {"value": specialty, "code": snomed},
                "therapeutic_area": rng.choice(THERAPEUTIC_AREAS),
                "institution_id": inst["id"],
                "territory": rng.choice(["NE-1", "NE-2", "SE-1", "MW-1", "W-1"]),
                "personal_email": f"hcp{i}@example-personal.test",
            }
        )
    return hcps


def generate_content(rng: random.Random, n: int = 30) -> list[dict]:
    items = []
    for i in range(1, n + 1):
        title = f"{rng.choice(CONTENT_TITLES)} ({i})"
        topic, mesh = rng.choice(TOPICS)
        items.append(
            {
                "id": f"CNT-{i:03d}",
                "title": title,
                "topic": topic,
                "mesh_code": mesh,
                "therapeutic_area": rng.choice(THERAPEUTIC_AREAS),
                "approval_status": rng.choices(["approved", "pending", "expired"], weights=[80, 15, 5])[0],
                "audience": rng.choice(["HCP", "patient", "internal"]),
                "body_text": (
                    f"Clinical summary covering {topic.lower()} for practicing physicians, "
                    f"including recent trial data and practical dosing guidance."
                ),
            }
        )
    return items


def generate_interactions(rng: random.Random, hcps: list[dict], content: list[dict], n: int = 100) -> list[dict]:
    interactions = []
    approved_content = [c for c in content if c["approval_status"] == "approved"]
    for i in range(1, n + 1):
        hcp = rng.choice(hcps)
        item = rng.choice(approved_content)
        interactions.append(
            {
                "id": f"INT-{i:04d}",
                "hcp_id": hcp["id"],
                "content_id": item["id"],
                "channel": rng.choice(CHANNELS),
                "date": f"2026-{rng.randint(1,8):02d}-{rng.randint(1,28):02d}",
            }
        )
    return interactions


def generate_publications(rng: random.Random, hcps: list[dict], n: int = 40) -> list[dict]:
    pubs = []
    for i in range(1, n + 1):
        topic, mesh = rng.choice(TOPICS)
        authors = rng.sample(hcps, k=rng.randint(1, 3))
        pubs.append(
            {
                "id": f"PUB-{i:03d}",
                "title": f"{topic}: a multicenter analysis ({2024 + i % 3})",
                "author_hcp_ids": [a["id"] for a in authors],
                "topic": topic,
                "mesh_code": mesh,
                "journal": rng.choice(JOURNALS),
                "date": f"{2024 + i % 3}-{rng.randint(1,12):02d}-01",
                "abstract": (
                    f"This multicenter study evaluates {topic.lower()} outcomes, "
                    f"reporting endpoints relevant to clinical decision-making."
                ),
            }
        )
    return pubs


def generate_studies(rng: random.Random, n: int = 5) -> list[dict]:
    studies = []
    for i in range(1, n + 1):
        studies.append(
            {
                "id": f"STUDY-{i:03d}",
                "protocol_id": f"PROTO-{2026}-{i:03d}",
                "phase": rng.choice(["Phase 2", "Phase 3"]),
                "status": rng.choice(["recruiting", "active_not_recruiting", "completed"]),
                "therapeutic_area": rng.choice(THERAPEUTIC_AREAS),
            }
        )
    return studies


def generate_investigator_sites(
    rng: random.Random, hcps: list[dict], institutions: list[dict], studies: list[dict], n: int = 12
) -> list[dict]:
    records = []
    for i in range(1, n + 1):
        hcp = rng.choice(hcps)
        study = rng.choice(studies)
        records.append(
            {
                "id": f"PI-{i:03d}",
                "hcp_id": hcp["id"],
                "study_id": study["id"],
                "site_institution_id": hcp["institution_id"],
                "role": "PRINCIPAL_INVESTIGATOR_OF",
                "enrollment_rate": round(rng.uniform(0.3, 1.5), 2),
                "feasibility_score": round(rng.uniform(0.4, 0.98), 2),
                "active": study["status"] in ("recruiting", "active_not_recruiting"),
            }
        )
    return records


def generate_msl_interactions(rng: random.Random, hcps: list[dict], n: int = 25) -> list[dict]:
    """Medical-only, never bridged to Commercial (design doc section 1 & 3)."""
    records = []
    for i in range(1, n + 1):
        hcp = rng.choice(hcps)
        topic, _ = rng.choice(TOPICS)
        records.append(
            {
                "id": f"MSL-{i:03d}",
                "hcp_id": hcp["id"],
                "msl_id": f"MSLEMP-{rng.randint(1,15):03d}",
                "topic": topic,
                "date": f"2026-{rng.randint(1,8):02d}-{rng.randint(1,28):02d}",
                "notes": "Medical inquiry response; scientific exchange only.",
            }
        )
    return records


def generate_all() -> dict[str, list[dict]]:
    rng = _rng()
    institutions = generate_institutions(rng)
    hcps = generate_hcps(rng, institutions)
    content = generate_content(rng)
    interactions = generate_interactions(rng, hcps, content)
    publications = generate_publications(rng, hcps)
    studies = generate_studies(rng)
    investigator_sites = generate_investigator_sites(rng, hcps, institutions, studies)
    msl_interactions = generate_msl_interactions(rng, hcps)
    return {
        "institutions": institutions,
        "hcps": hcps,
        "content": content,
        "interactions": interactions,
        "publications": publications,
        "studies": studies,
        "investigator_sites": investigator_sites,
        "msl_interactions": msl_interactions,
    }


def write_all(out_dir: Path = OUT_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = generate_all()
    for name, records in data.items():
        (out_dir / f"{name}.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    write_all()
    print(f"Wrote synthetic fixtures to {OUT_DIR}")
