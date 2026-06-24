# Global Industry Rotation

面向投研中观配置的跨市场行业轮动模型，覆盖A股、港股与美股，输出超配/标配/低配行业清单、因子贡献分解、跨市场共振与样本外验证摘要。

## 快速开始

```bash
python -m industry_rotation.cli --as_of_date 2026-06-24 --market ALL --weight_profile default --output_dir reports
```

输出：
- `reports/global_industry_rotation_<date>.md`：主报告。
- `reports/global_industry_rotation_<date>.xlsx`：Excel行业打分表。
- `reports/scorecard_<date>.csv`：机器可读打分卡。

## 配置
默认参数位于 `src/industry_rotation/config/default_config.json`，包含因子权重、滚动窗口、拥挤度阈值、基准与组合约束。
