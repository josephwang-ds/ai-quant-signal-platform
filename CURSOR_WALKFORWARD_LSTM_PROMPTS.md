# Cursor 指令 · Walk-forward 评估 + LSTM（离线层）

在**现有 Compare Models**基础上扩展，不破坏现在的单切分路径。
现有关键部件（复用，别重写）：
- `backend/app/models/features.py`：`build_feature_frame(price_df) -> (X, y, aligned)`、`FEATURE_COLUMNS`、
  `_assert_no_future_feature_columns`、标签 `y_next_up`。
- `backend/app/models/model_comparison.py`：`run_model_comparison(..., split_date, ...)`、
  `_predict_signal`、`_slice_to_test_window`、`_metrics_for_test_segment`、`_build_equity_curve_rows`、
  `_rebase_segment_for_metrics`（来自 `app.backtest.oos`）、`apply_position_and_returns`。
- `backend/app/models/model_registry.py`：logistic / random_forest / xgboost / lightgbm。
- 路由 `backend/app/api/routes/model_comparison.py`（POST /api/v1/models/compare）。
- 前端 `frontend/app/compare-models/`、`ModelComparisonPage.tsx`、`ModelComparisonCharts.tsx`、
  `lib/api.ts` 的 `runModelComparison`。

**三条防泄漏纪律照旧**：时序切分不洗牌；每折只在该折训练集 fit（scaler/模型都是）；
标签用未来、特征只用过去，每个折边界做 1 日 embargo。

完成标准：后端 `PYTHONPATH=. pytest -q`、前端 `npx tsc --noEmit && npm test -- --run && npm run build` 全绿。

---

## Prompt WF-1 —（后端）加 walk-forward 滚动样本外评估

```
在 backend/app/models/model_comparison.py 新增函数 run_walk_forward_comparison，
不改动现有 run_model_comparison。目的：把"单个 split_date 一刀切"升级为"多折滚动 OOS"，
更能体现时间序列 ML 的严谨。

签名：
run_walk_forward_comparison(price_df, *, n_folds=4, transaction_cost, short_window,
    long_window, momentum_window, models=None, scheme="expanding") -> dict

实现（严格按序，尽量复用现有部件）：
1. X, y, aligned = build_feature_frame(price_df)；dates = 已有的日期序列。
2. 按时间把样本外区间等分成 n_folds 折。scheme:
   - "expanding"(默认，锚定扩窗)：第 k 折训练=区间起点..该折测试前一日；测试=该折那段。
   - "rolling"(可选滑窗)：训练窗口固定长度向前滚动。
   先实现 expanding，rolling 作为参数分支。
3. 每折：
   - 训练/测试按日期切；embargo：丢掉训练集最后 1 行（其标签落入测试期），复用现有做法。
   - 训练样本或测试样本 < MIN_SPLIT_ROWS 的折跳过并记录，不报错。
   - 对每个模型：在该折训练集 fit → 用 _predict_signal 在该折测试集得 signal。
4. 拼接：把每个模型在各折测试段的 signal **按时间顺序拼成一条连续的 OOS 信号序列**，
   然后走一次 apply_position_and_returns + calculate_backtest_metrics（复用
   _metrics_for_test_segment / _rebase_segment_for_metrics）得到**该模型的聚合 walk-forward 指标**
   与净值曲线（复用 _build_equity_curve_rows）。
5. 规则基线（ma_crossover / momentum / combined / buy_and_hold）在**同一拼接 OOS 区间**上算指标，
   与现有单切分里对规则基线的处理保持一致。
6. 额外产出每折的简要指标（每折每模型的 directional_accuracy 与 sharpe），用于前端画"逐折稳定性"。
7. 返回结构与 run_model_comparison **尽量同构**，另加：
   {
     "mode": "walk_forward", "n_folds": <实际用到的折数>, "scheme": scheme,
     "folds": [ {"index":k,"train_start","train_end","test_start","test_end",
                 "per_model":[{"label","directional_accuracy","sharpe_ratio"}...]} ... ],
     "results": [...同现有结构：label/kind/metrics/equity...但为聚合 OOS...],
     "summary", "interpretation"(补一条：多折滚动比单切分更能反映稳健性),
     "oos_start","oos_end"
   }

路由：在 backend/app/api/routes/model_comparison.py 的 POST /api/v1/models/compare 请求体
加可选字段 n_folds(int|None) 与 scheme。**n_folds 为空 → 走现有单切分 run_model_comparison；
n_folds 给了 → 走 run_walk_forward_comparison。** 不新增端点，保持前端兼容。

测试 backend/tests/test_model_comparison.py 增补：
- test_walk_forward_folds_are_chronological：每折 train_end < test_start，折与折按时间不重叠（含 embargo）。
- test_walk_forward_no_leakage_smoke：随机游走价格上各模型聚合 directional_accuracy ∈ ~0.4–0.6。
- test_walk_forward_aggregates_over_full_oos：results 的评估区间 = 各折测试段拼接的 [oos_start, oos_end]。
- test_single_split_still_works：不传 n_folds 时行为不变（回归保护）。

PYTHONPATH=. pytest -q 全绿。
```

## Prompt WF-2 —（前端）Compare Models 支持 walk-forward 视图

```
前端在 Compare Models 页支持 walk-forward，与现有单切分并存：
1. lib/api.ts 的 runModelComparison 参数加可选 n_folds、scheme；类型加 folds、mode、oos_start/oos_end。
2. ModelComparisonPage.tsx 顶部加一个切换："单切分(split_date) / 滚动多折(walk-forward)"。
   选 walk-forward 时用 n_folds 输入(默认 4)，不传 split_date。
3. 结果区：
   - 聚合 OOS 的净值叠加图/散点/排名条形复用现有 ModelComparisonCharts（数据换成聚合结果）。
   - 新增一张"逐折稳定性"小图：x=折序号，y=各模型该折 sharpe（或 directional_accuracy），
     用 CHART_COMPARE_LINES 多序列。让"某模型是不是每折都稳"一目了然。
   - 顶部标注 oos_start–oos_end 与 "N 折滚动样本外"。
4. i18n 加中英文文案（walk-forward / 单切分 / 折 / 逐折稳定性 等）。

npx tsc --noEmit && npm test -- --run && npm run build 全绿。
```

---

## Prompt LSTM-1 —（离线训练脚本 + 产出 artifact，不进 Render 运行时）

```
加一个 LSTM，但**离线训练、把结果作为 artifact 提交**，线上不装 torch（保 Render 轻）。

1) backend/requirements-dev.txt（注意：加到 dev，不加到 requirements.txt / 不进 Render 运行时）：
   torch>=2.2

2) 新建 backend/scripts/train_lstm.py（本地/CI 手动运行）：
   - 参数：--ticker SPY --start-date --split-date --seq-len 20 --epochs --out <artifact 路径>
   - 用 app.data_providers 加载价格；用 features.build_feature_frame 得到 X/y/aligned
     （**只用 FEATURE_COLUMNS，防泄漏纪律与其它模型一致**）。
   - 构造序列样本：每个样本 = 过去 seq_len 天的 FEATURE_COLUMNS（标准化，scaler 只在训练段 fit），
     标签 = 该序列末日的 y_next_up。
   - 时序切分：split_date 前为训练、后为测试；从训练段末尾再切一小段按时间顺序的验证集做 early stopping
     （**绝不碰测试段**）；embargo 丢掉跨界样本。
   - 模型：小型 LSTM（1–2 层、hidden 16–32）+ 线性头 + sigmoid。CPU 训练即可。
   - 在测试段预测 → signal → 走 apply_position_and_returns + calculate_backtest_metrics
     得到 OOS 指标与净值曲线（与其它模型同一管线）。
   - 产出 artifact JSON 存到 backend/app/models/artifacts/lstm_<ticker>.json，内容：
     { "label":"LSTM","kind":"ml","strategy":"lstm","trained_at":<ISO>,
       "ticker","start_date","split_date","seq_len",
       "metrics":{...同其它模型的 metrics key...},
       "directional_accuracy":<float>,
       "equity_curve":[{"date","LSTM":<cum>}...],
       "note":"Offline-trained; results as of trained_at. Reproduce via scripts/train_lstm.py" }
   - 同时把训练好的权重存 backend/app/models/artifacts/lstm_<ticker>.pt（供复现，可选提交）。

3) 说明：README/脚本头部写清楚"LSTM 为离线训练，结果以 artifact 形式随仓库提交，
   线上不做 torch 推理；复现命令见下"。

本地能跑通 python scripts/train_lstm.py ... 生成 artifact 即可（这步不进 CI 必跑）。
```

## Prompt LSTM-2 —（把 LSTM artifact 接进 Compare Models，前端加"离线"标）

```
让 Compare Models 结果里带上 LSTM 这一行，数据来自 LSTM-1 生成的 artifact，**线上不导入 torch**。

后端 backend/app/models/model_comparison.py：
- 新增可选步骤：若存在 backend/app/models/artifacts/lstm_<ticker>.json 且其
  (start_date/split_date 或 walk-forward 的 oos 区间) 与本次请求兼容，则把该 artifact 的
  label/metrics/directional_accuracy/equity_curve 作为一条 result 追加进 results，
  并打 "source":"offline_artifact"、"trained_at" 字段。**不兼容就跳过、不报错、也不编造。**
- 只读 JSON，不 import torch。请求体加可选 include_lstm(bool, 默认 true)。

前端 ModelComparisonPage.tsx / ModelComparisonCharts.tsx：
- LSTM 这一行/这条曲线加一个小徽章 "Offline-trained · <trained_at>"，
  hover 提示"离线训练，结果随仓库提交，可用 scripts/train_lstm.py 复现"。
- 其余展示与其它模型一致（进净值叠加图、散点、排名）。
- i18n 加中英文（离线训练 / 可复现 等）。

诚实要点（务必保留）：LSTM 行明确标注"离线、截至某时间"，不要伪装成实时训练；
directional_accuracy 仍标注"非收益承诺"。

后端 pytest / 前端 tsc+test+build 全绿。
```

---

## 面试怎么讲（加完之后）
- **walk-forward**："我没有只用一次样本外切分，而是滚动多折评估，并画了逐折稳定性——
  看的是模型在不同时间段是否稳定，而不是单段运气。每折只在其训练集内 fit、边界做 embargo 防泄漏。"
- **LSTM（诚实叙事）**："我加了 LSTM 做对比。在这种日频小样本上它并没有稳定跑赢 GBM——
  我把它离线训练、结果随仓库可复现地提交，线上不背 torch 依赖。这说明我懂什么时候该上深度学习、
  什么时候不该，以及怎么把重模型和轻部署分开。"

## 别过度
- walk-forward 折数别太多（4–6 折足够），否则每折样本太少、噪声大。
- LSTM 保持小模型；不要为了"看起来深"堆层数,小样本只会更过拟合。
