from industry_rotation.config import load_config
from industry_rotation.data import generate_demo_input, load_industry_mapping
from industry_rotation.model import apply_weight_constraints, identify_resonance, score_industries


def test_scoring_outputs_signals_and_constraints():
    cfg = load_config()
    data = generate_demo_input("2026-06-24")
    scored = score_industries(data.factor_frame, cfg)
    constrained = apply_weight_constraints(scored, data.benchmark_weights, cfg)
    assert {"超配", "标配", "低配"}.issubset(set(constrained["signal"]))
    assert constrained.groupby("market")["target_weight"].sum().round(6).eq(1.0).all()


def test_resonance_uses_semantic_mapping():
    cfg = load_config()
    data = generate_demo_input("2026-06-24")
    scored = apply_weight_constraints(score_industries(data.factor_frame, cfg), data.benchmark_weights, cfg)
    mapping = load_industry_mapping()
    long_map = mapping.melt(id_vars=["semantic_industry", "notes"], value_vars=["cn_industry", "hk_industry", "us_industry"], value_name="industry").dropna(subset=["industry"])
    scored = scored.merge(long_map[["semantic_industry", "industry"]], on="industry", how="left")
    resonance = identify_resonance(scored)
    assert "confidence" in resonance.columns
    assert resonance["semantic_industry"].notna().any()
