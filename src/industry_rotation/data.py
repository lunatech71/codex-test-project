from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

MARKET_INDUSTRIES = {
    "CN": ["能源", "材料", "工业", "可选消费", "必需消费", "医药", "金融", "房地产", "信息技术", "通信服务"],
    "HK": ["能源业", "原材料业", "工业", "非必需性消费", "必需性消费", "医疗保健业", "金融业", "地产建筑业", "资讯科技业", "电讯业", "公用事业"],
    "US": ["Energy", "Materials", "Industrials", "Consumer Discretionary", "Consumer Staples", "Health Care", "Financials", "Real Estate", "Information Technology", "Communication Services", "Utilities"],
}

@dataclass(frozen=True)
class ModelInput:
    factor_frame: pd.DataFrame
    returns: pd.DataFrame
    benchmark_weights: pd.DataFrame
    macro_state: str


def generate_demo_input(as_of_date: str, seed: int = 42) -> ModelInput:
    """Generate deterministic public-schema demo data for offline reproducibility.

    Production adapters can replace this with OpenBB/FRED/OECD/index-provider pulls
    while preserving the same normalized columns.
    """
    rng = np.random.default_rng(seed)
    as_of = pd.Timestamp(as_of_date)
    rows = []
    ret_rows = []
    weight_rows = []
    dates = pd.date_range(as_of - pd.DateOffset(years=5), as_of, freq="ME")
    states = ["growth_up_inflation_up", "growth_up_inflation_down", "growth_down_inflation_up", "growth_down_inflation_down"]
    macro_state = states[as_of.month % 4]
    for market, industries in MARKET_INDUSTRIES.items():
        raw_w = rng.dirichlet(np.ones(len(industries)))
        for industry, base_w in zip(industries, raw_w):
            macro = rng.normal(0, 1)
            fundamental = rng.normal(0, 1)
            flow = rng.normal(0, 1)
            technical = rng.normal(0, 1)
            turnover_pct = float(rng.uniform(0, 1))
            rows.append({
                "as_of_date": as_of, "market": market, "industry": industry,
                "macro": macro, "fundamental": fundamental, "flow": flow,
                "technical_valuation": technical, "turnover_percentile": turnover_pct,
                "volatility_spike_z": rng.normal(0, 1), "leader_valuation_premium": rng.uniform(0, 1),
                "pb_roe_percentile_10y": rng.uniform(0, 1), "shorting_feasible": market in {"HK", "US"},
            })
            weight_rows.append({"market": market, "industry": industry, "benchmark_weight": base_w})
            level = 100.0
            for d in dates:
                level *= 1 + rng.normal(0.006 + 0.002 * macro, 0.055)
                ret_rows.append({"date": d, "market": market, "industry": industry, "return": level / 100 - 1})
    return ModelInput(pd.DataFrame(rows), pd.DataFrame(ret_rows), pd.DataFrame(weight_rows), macro_state)


def load_industry_mapping() -> pd.DataFrame:
    return pd.read_csv(Path(__file__).resolve().parent / "data" / "industry_mapping_v1.csv")
