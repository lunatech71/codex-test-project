from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

FACTOR_COLUMNS = ["macro", "fundamental", "flow", "technical_valuation"]


def zscore_by_market(frame: pd.DataFrame, columns: list[str] = FACTOR_COLUMNS) -> pd.DataFrame:
    out = frame.copy()
    for col in columns:
        out[f"{col}_z"] = out.groupby("market")[col].transform(lambda s: stats.zscore(s, nan_policy="omit"))
        out[f"{col}_z"] = out[f"{col}_z"].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return out


def score_industries(frame: pd.DataFrame, config: dict, weight_profile: str = "default") -> pd.DataFrame:
    scored = zscore_by_market(frame)
    weights = config["weight_profiles"][weight_profile]
    crowding = config["model"]["crowding"]
    scored["crowding_penalty"] = 0.0
    crowded = scored["turnover_percentile"] > crowding["turnover_percentile_threshold"]
    crowded |= scored["volatility_spike_z"] > crowding["volatility_spike_z_threshold"]
    crowded |= scored["leader_valuation_premium"] > crowding["leader_valuation_premium_threshold"]
    scored.loc[crowded, "crowding_penalty"] = -0.35
    total = []
    for _, row in scored.iterrows():
        w = weights[row["market"]]
        factor_score = sum(row[f"{factor}_z"] * w[factor] for factor in FACTOR_COLUMNS)
        total.append(factor_score + row["crowding_penalty"])
    scored["total_score"] = total
    scored["score_rank"] = scored.groupby("market")["total_score"].rank(ascending=False, method="first")
    q_hi = config["model"]["signal_thresholds"]["overweight_quantile"]
    q_lo = config["model"]["signal_thresholds"]["underweight_quantile"]
    scored["signal"] = "标配"
    for market, idx in scored.groupby("market").groups.items():
        s = scored.loc[idx, "total_score"]
        scored.loc[idx, "signal"] = np.where(s >= s.quantile(q_hi), "超配", np.where(s <= s.quantile(q_lo), "低配", "标配"))
    sigma = config["model"]["signal_thresholds"]["strong_signal_sigma"]
    scored["strong_signal_alert"] = scored[[f"{c}_z" for c in FACTOR_COLUMNS]].abs().gt(sigma).any(axis=1)
    return scored.sort_values(["market", "score_rank"])


def apply_weight_constraints(scored: pd.DataFrame, benchmark_weights: pd.DataFrame, config: dict) -> pd.DataFrame:
    out = scored.merge(benchmark_weights, on=["market", "industry"], how="left")
    cons = config["model"]["constraints"]
    out["target_deviation"] = np.select(
        [out["signal"].eq("超配"), out["signal"].eq("低配")],
        [cons["max_overweight_deviation"], cons["max_underweight_deviation"]],
        default=0.0,
    )
    out["target_weight"] = (out["benchmark_weight"] + out["target_deviation"]).clip(lower=0)
    out["target_weight"] = out.groupby("market")["target_weight"].transform(lambda s: s / s.sum())
    return out


def identify_resonance(scored: pd.DataFrame) -> pd.DataFrame:
    pivot = scored.pivot_table(index="semantic_industry", columns="market", values="signal", aggfunc="first")
    rows = []
    for semantic, row in pivot.iterrows():
        signals = row.dropna().to_dict()
        overweight = sum(v == "超配" for v in signals.values())
        underweight = sum(v == "低配" for v in signals.values())
        if overweight == 3 or (overweight >= 2 and underweight == 0):
            confidence = "高置信度"
        elif overweight == 2:
            confidence = "二市场共振观察"
        elif overweight == 1:
            confidence = "单市场信号"
        else:
            confidence = "无超配共振"
        rows.append({"semantic_industry": semantic, "overweight_markets": overweight, "underweight_markets": underweight, "confidence": confidence, **signals})
    return pd.DataFrame(rows).sort_values(["confidence", "overweight_markets"], ascending=[True, False])
