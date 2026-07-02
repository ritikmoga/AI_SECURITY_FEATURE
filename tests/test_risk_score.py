from src.scoring.risk_score import RiskScorer


def test_risk_score_levels():
    scorer = RiskScorer()
    assert scorer.level_for_score(0) == "Safe"
    assert scorer.level_for_score(30) == "Suspicious"
    assert scorer.level_for_score(60) == "High Risk"
    assert scorer.level_for_score(90) == "Dangerous"


def test_report_contains_scan_id():
    report = RiskScorer().build_report("url", "https://example.com", [])
    assert report["scan_id"]
    assert report["risk_level"] == "Safe"
