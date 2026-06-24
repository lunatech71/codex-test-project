from __future__ import annotations

import argparse
from pathlib import Path

from .backtest import rolling_validation
from .config import load_config
from .data import generate_demo_input, load_industry_mapping
from .model import apply_weight_constraints, identify_resonance, score_industries
from .report import write_excel, write_markdown_report


def run(as_of_date: str, market: str, weight_profile: str, output_dir: Path) -> None:
    config = load_config()
    model_input = generate_demo_input(as_of_date)
    factors = model_input.factor_frame
    if market != "ALL":
        factors = factors[factors["market"].eq(market)]
    scored = score_industries(factors, config, weight_profile)
    scored = apply_weight_constraints(scored, model_input.benchmark_weights, config)
    mapping = load_industry_mapping()
    long_map = mapping.melt(id_vars=["semantic_industry", "notes"], value_vars=["cn_industry", "hk_industry", "us_industry"], value_name="industry").dropna(subset=["industry"])
    scored = scored.merge(long_map[["semantic_industry", "industry"]], on="industry", how="left")
    resonance = identify_resonance(scored) if market == "ALL" else scored[["market", "industry", "signal", "semantic_industry"]]
    validation = rolling_validation(model_input.returns, scored)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_markdown_report(output_dir / f"global_industry_rotation_{as_of_date}.md", as_of_date, model_input.macro_state, scored, resonance, validation)
    write_excel(output_dir / f"global_industry_rotation_{as_of_date}.xlsx", scored, resonance if hasattr(resonance, 'to_excel') else scored, validation)
    scored.to_csv(output_dir / f"scorecard_{as_of_date}.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run global cross-market industry rotation model")
    parser.add_argument("--as_of_date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--market", default="ALL", choices=["ALL", "CN", "HK", "US"])
    parser.add_argument("--weight_profile", default="default")
    parser.add_argument("--output_dir", default="reports")
    args = parser.parse_args()
    run(args.as_of_date, args.market, args.weight_profile, Path(args.output_dir))

if __name__ == "__main__":
    main()
