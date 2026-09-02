def test_synthetic_data_counts_match_design_doc(source_data):
    assert len(source_data["hcps"]) == 50
    assert len(source_data["institutions"]) == 10
    assert len(source_data["content"]) == 30
    assert len(source_data["interactions"]) == 100
    assert len(source_data["publications"]) == 40
    assert len(source_data["studies"]) == 5
