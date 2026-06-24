from __future__ import annotations

import pandas as pd


def rolling_validation(returns: pd.DataFrame, top_industries: pd.DataFrame) -> pd.DataFrame:
    """Compute simple out-of-sample metrics for selected Top-3 industries.

    The function expects normalized monthly industry return levels/returns and reports
    hit ratio, average excess return, and maximum drawdown versus equal-weight industry benchmark.
    """
    rows = []
    for market, selected in top_industries.groupby("market"):
        chosen = set(selected.nsmallest(3, "score_rank")["industry"])
        r = returns[returns["market"].eq(market)].copy()
        monthly = r.pivot_table(index="date", columns="industry", values="return").pct_change().dropna(how="all")
        portfolio = monthly[list(chosen)].mean(axis=1)
        benchmark = monthly.mean(axis=1)
        excess = (portfolio - benchmark).dropna()
        wealth = (1 + excess).cumprod()
        drawdown = wealth / wealth.cummax() - 1
        rows.append({
            "market": market,
            "top3_hit_ratio": float((excess > 0).mean()),
            "avg_excess_return": float(excess.mean()),
            "max_drawdown": float(drawdown.min()),
            "months": int(excess.shape[0]),
        })
    return pd.DataFrame(rows)
