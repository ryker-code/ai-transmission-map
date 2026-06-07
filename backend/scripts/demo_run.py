#!/usr/bin/env python3
"""
Quick demo: runs a thesis, prints bottleneck scores, and generates a memo excerpt.
Usage: python -m backend.scripts.demo_run
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


async def main():
    print("=== AI Transmission Map — Demo Run ===\n")

    # 1. Bottleneck scores
    print("1. Bottleneck Scores (top 5)")
    from backend.agents.scorer import compute_bottleneck_scores
    scores = compute_bottleneck_scores()
    for s in scores[:5]:
        print(f"   {s.rank:2d}. {s.entity_name:<35} score={s.score:.1f}  regime={s.regime_tag}")

    print()

    # 2. Regime detection
    print("2. Current Market Regime")
    from backend.tools.regime_detector import detect_regime
    regime = detect_regime()
    print(f"   Regime: {regime['regime']}  confidence={regime['confidence']:.2f}")
    print(f"   Description: {regime['description']}")

    print()

    # 3. Entity resolver
    print("3. Entity Resolver Lookups")
    from backend.agents.resolver import get_resolver
    resolver = get_resolver()
    test_names = ["NVIDIA", "GEV", "Constellation", "Vertiv"]
    for name in test_names:
        result = resolver.resolve(name)
        if result:
            print(f"   '{name}' → {result['canonical_name']} ({result['entity_type']})")
        else:
            print(f"   '{name}' → not found")

    print()

    # 4. House view summary
    print("4. House View Overrides")
    from backend.db.house_view_store import all_entries
    entries = all_entries()
    if entries:
        for eid, d in list(entries.items())[:3]:
            print(f"   {eid}: conviction={d.get('conviction')} weight={d.get('weight_override')}")
    else:
        print("   No active overrides (default parity weights)")

    print()

    # 5. Bloomberg parser demo
    print("5. Bloomberg URL Parser")
    from backend.tools.bloomberg_parser import BloombergParser
    test_url = "https://www.bloomberg.com/news/articles/2024-01-15/nvidia-power-demand-ai-data-centers"
    parser = BloombergParser()
    meta = parser.parse_url(test_url)
    print(f"   URL: {test_url[:60]}...")
    print(f"   Tags: {meta['topic_tags']}")
    print(f"   Date: {meta['estimated_date']}")

    print()
    print("=== Demo complete. Backend healthy. ===")


if __name__ == "__main__":
    asyncio.run(main())
