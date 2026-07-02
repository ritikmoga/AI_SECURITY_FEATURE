"""CLI helper for ScamShield AI Security Feature."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from src.config import AppConfig
from src.detection.malware_detector import MalwareDetector
from src.detection.url_checker import URLChecker
from src.scoring.risk_score import RiskScorer

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="ScamShield AI defensive scanning CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Scan a single URL safely")
    group.add_argument("--message", help="Scan a text message safely")
    group.add_argument("--file", help="Scan a local file safely without executing it")
    args = parser.parse_args()

    config = AppConfig.from_env()
    scorer = RiskScorer()

    if args.url:
        checker = URLChecker(config)
        findings = checker.analyze_url(args.url)
        report = scorer.build_report("url", args.url, findings)
    elif args.message:
        checker = URLChecker(config)
        detector = MalwareDetector(config)
        message = {"subject": "", "body": args.message, "attachments": []}
        findings = checker.check(message) + detector.detect_message(message)
        report = scorer.build_report("message", "message", findings)
    else:
        detector = MalwareDetector(config)
        path = Path(args.file)
        findings, meta = detector.analyze_file(path, original_filename=path.name)
        report = scorer.build_report("file", path.name, findings, metadata=meta)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
