from __future__ import annotations

from pathlib import Path
import pandas as pd


def write_markdown_report(path: Path, as_of_date: str, macro_state: str, scored: pd.DataFrame, resonance: pd.DataFrame, validation: pd.DataFrame) -> None:
    lines = [
        f"# 全球行业轮动模型主报告（{as_of_date}）",
        "",
        "## 模型结构图",
        "数据接入 → 三周期宏观状态 → 四因子层标准化 → 市场内综合打分 → 约束后行业权重 → 跨市场语义映射与共振识别 → 报告/Excel 输出。",
        "",
        f"## 当期宏观状态判定：`{macro_state}`",
        "",
        "## 三市场 Top-3 / Bottom-3",
    ]
    for market, group in scored.groupby("market"):
        lines += [f"### {market}", "**Top-3**", group.nsmallest(3, "score_rank")[["industry", "signal", "total_score", "target_weight"]].to_markdown(index=False), "", "**Bottom-3**", group.nlargest(3, "score_rank")[["industry", "signal", "total_score", "target_weight"]].to_markdown(index=False), ""]
    lines += ["## 跨市场共振表", resonance.to_markdown(index=False), "", "## 样本外验证摘要", validation.to_markdown(index=False), "", "## 合规提示", "A股/港股不做空个股；行业级低配通过ETF减配实现。港股/美股如涉及行业ETF空头，以 `shorting_feasible` 字段标记可行性。"]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_excel(path: Path, scored: pd.DataFrame, resonance: pd.DataFrame, validation: pd.DataFrame) -> None:
    with pd.ExcelWriter(path) as writer:
        scored.to_excel(writer, sheet_name="industry_scorecard", index=False)
        resonance.to_excel(writer, sheet_name="cross_market_resonance", index=False)
        validation.to_excel(writer, sheet_name="validation", index=False)
