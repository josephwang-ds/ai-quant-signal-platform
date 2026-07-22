# Cursor 指令 · 旗舰模块「Compare Models」（真 ML + 防泄漏回测）

目标：规则策略（MA / 动量 / 组合 / 买入持有）与真 ML 模型（逻辑回归 / 随机森林 /
XGBoost / LightGBM）在**同一个样本外(OOS)窗口、同一套交易成本与指标**下同台对比，
并给出可解释性（特征重要性 + 方向准确率）。这是打 DS / AI Engineer 的核心技术叙事。

## 不可动摇的三条纪律（务必让 Cursor 遵守）
1. **防未来函数**：ML 只输出一个 `signal` 列（"预测下一日上涨=1"），走现有
   `app.backtest.engine.apply_position_and_returns`（内部 `position = signal.shift(1)`，
   即 t 日算信号、t+1 日才建仓）和 `app.backtest.metrics.calculate_backtest_metrics`。
   **绝不新写一套回测/成本逻辑**——复用等于保证与规则策略苹果对苹果。
2. **时序切分，禁止随机洗牌**：按 `split_date` 时间切分；训练只用样本内、评估只用样本外；
   scaler/模型只在训练集 fit，测试集只 transform。**禁止 KFold/shuffle/在全量上 fit**。
3. **标签用未来、特征只用过去**：标签 `y_t = 1 if close_{t+1} > close_t else 0`（仅训练用）；
   特征全部来自 `add_technical_indicators` 产出的历史列。切分处做 **1 日 embargo**
   （丢掉训练集最后一行，因其标签 close_{t+1} 落进测试期，会造成边界泄漏）。

按顺序执行；完成标准：后端 `PYTHONPATH=. pytest -q`、前端 `npx tsc --noEmit && npm test && npm run build` 全绿。

---

## Prompt CM-1 —（后端·依赖与特征）

```
1) backend/requirements.txt 追加（注意 Render 免费档内存/构建限制，见下方备注）：
   numpy>=1.26
   scikit-learn>=1.4
   xgboost>=2.0
   lightgbm>=4.3

2) 新建 backend/app/models/features.py：
   from app.features.technical_indicators import add_technical_indicators
   定义 FEATURE_COLUMNS = ["return_20d","return_60d","ma20","ma60","volatility_20d",
                          "volume_change","rsi_14"]
   （只用这些历史派生列；ma20/ma60 建议转成相对价格，如 close/ma20-1，避免量纲问题——
    新增 ma20_gap、ma60_gap 两列替代原始 ma 绝对值。）
   函数 build_feature_frame(price_df) -> (X: DataFrame, y: Series, aligned_df: DataFrame):
     - df = add_technical_indicators(price_df.copy())
     - 标签: df["y_next_up"] = (df["close"].shift(-1) > df["close"]).astype(int)
     - 丢掉暖机期与末行（shift(-1) 造成的 NaN）：df = df.dropna(subset=FEATURE_COLUMNS+["y_next_up"])
     - 返回 X=df[FEATURE_COLUMNS], y=df["y_next_up"], aligned_df=df（含 date/close/daily_return）
   **断言 y 不在 X 里、FEATURE_COLUMNS 不含任何 *_next_* / 未来列。**

3) 新建 backend/app/models/model_registry.py：
   返回一个 name->构造器 的字典（每次调用新建实例，禁止全局复用已 fit 的模型）：
     "logistic":       LogisticRegression(max_iter=1000)
     "random_forest":  RandomForestClassifier(n_estimators=300, max_depth=4, random_state=42)
     "xgboost":        XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                                     subsample=0.8, eval_metric="logloss", random_state=42)
     "lightgbm":       LGBMClassifier(n_estimators=300, max_depth=3, learning_rate=0.05,
                                     subsample=0.8, random_state=42)
   逻辑回归前接 StandardScaler（用 sklearn Pipeline）；树模型可不缩放。
   提供 feature_importance(model, feature_names) -> dict：树模型用 feature_importances_，
   逻辑回归用 |coef_| 归一化。
```
> **Render 部署备注（重要）**：xgboost/lightgbm 的 wheel 较大，免费档构建慢、可能触内存上限。
> 如果部署吃紧，给 Cursor 备选：先只上 `logistic + random_forest + HistGradientBoostingClassifier`
> （后者是 sklearn 自带、无额外依赖、同样是梯度提升），本地再开 xgboost/lightgbm。二选一即可。

---

## Prompt CM-2 —（后端·防泄漏对比引擎）

```
新建 backend/app/models/model_comparison.py，函数
run_model_comparison(price_df, *, split_date, transaction_cost, short_window, long_window,
                     momentum_window, models=None) -> dict:

步骤（严格按序）：
1. X, y, aligned = build_feature_frame(price_df)。
2. 时序切分：train_mask = aligned["date"] < split_date；test_mask = aligned["date"] >= split_date。
   若任一侧样本过少（如 <60 行）抛 ValueError（路由转 400，提示调整 split_date）。
3. embargo：从训练集**去掉最后 1 行**（其标签落入测试期）。
4. 对每个模型：在 (X_train, y_train) 上 fit；对 X_test 预测 proba/label →
   signal_test（1=预测涨）。构造 test 窗口的 df：
     model_df = aligned.loc[test_mask, ["date","close","daily_return"]].copy()
     model_df["model_signal"] = signal_test 对齐到相同 index
   调 apply_position_and_returns(model_df, signal_col="model_signal",
     transaction_cost=..., buy_reason="Model predicts next-day up",
     sell_reason="Model predicts next-day down")，再 calculate_backtest_metrics。
   记录 feature_importance 和 **方向准确率**（sklearn accuracy_score，明确标注这是
   "directional accuracy，非收益承诺"）。
5. 规则基准同窗口对比：对 ma_crossover / momentum / combined / buy_and_hold，
   **在同一个 test 窗口**上算 OOS 指标——做法：对全量 price_df 跑各自 run_*_backtest
   （保证暖机），再把结果 df 切到 test 窗口后用 calculate_backtest_metrics 重算，
   使所有策略评估区间一致。买入持有用 calculate_buy_and_hold_metrics。
6. 汇总：复用 app.backtest.compare 里 _build_summary 的思路，产出
   best_total_return / best_sharpe / lowest_drawdown / fewest_trades（label 命中）。
7. 返回 {
     "split_date", "n_train", "n_test", "test_start", "test_end",
     "results": [ {label, kind:"rule"|"ml", strategy, metrics,
                   directional_accuracy?, feature_importance?} ... ],
     "summary": {...},
     "interpretation": [ 规则型解释串：ML 未必赢；样本外一致区间才可比；
                         方向准确率 ≠ 收益；成本与换手要一起看 ]
   }

**不要**在这个文件里重写任何收益/回撤计算——只调 engine + metrics。
```

---

## Prompt CM-3 —（后端·路由 + 测试，含泄漏守卫）

```
1) 新建 backend/app/api/routes/model_comparison.py：
   APIRouter(prefix="/api/v1/models", tags=["compare-models"])
   POST "/compare"，请求体含 ticker, start_date, end_date?, split_date, transaction_cost,
   short_window, long_window, momentum_window, data_source, models?(可选子集)。
   逻辑：load_price_data → run_model_comparison → 返回。错误处理照抄 main.py 的 run_backtest
   （ValueError→404/400，其它→500）。在 main.py include_router 注册。

2) 新建 backend/tests/test_model_comparison.py（离线，monkeypatch load_price_data 用合成价格；
   参照现有离线路由测试写法）。必须覆盖这些**防泄漏守卫**（面试加分点）：
   - test_split_is_chronological_and_no_overlap：train 的最大 date < test 的最小 date，
     且训练集因 embargo 少了末行。
   - test_features_have_no_future_columns：断言 FEATURE_COLUMNS 与返回结果里都不含
     以 y_/next_/future_ 命名或等于 close.shift(-1) 的列。
   - test_all_strategies_share_same_oos_window：results 里每条 metrics 对应的评估区间
     （test_start/test_end）一致。
   - test_no_lookahead_smoke：构造一段"未来不可预测"的随机游走价格，断言各 ML 模型的
     directional_accuracy 落在合理区间（约 0.4–0.6），不会出现 >0.9 这种泄漏征兆。
   - test_model_output_shape：results 含 rule 与 ml 两类、每条有 metrics 的关键 key
     （total_return/sharpe_ratio/max_drawdown/number_of_trades）。

完成标准：cd backend && PYTHONPATH=. pytest -q 全绿。
```

---

## Prompt CM-4 —（前端·Compare Models 页面）

```
在 frontend 新增/改造 Compare Models 页面，调用 POST /api/v1/models/compare，
取数与渲染风格对齐 components/features/comparison/StrategyComparisonPage.tsx。

1) frontend/lib/api.ts 新增 runModelComparison(params): Promise<ModelComparisonResponse>
   （仿 runStrategyComparison，用 buildApiUrl("api/v1/models/compare")，body 含 split_date）。
   定义 ModelComparisonResponse 类型（results: {label,kind,strategy,metrics,
   directional_accuracy?,feature_importance?}[]、summary、interpretation、test_start/test_end）。

2) 新增页面（可挂在现有 comparison 路由下新增一个 "Models" 子视图，或新建
   frontend/app/compare-models/page.tsx + components/features/comparison/ModelComparisonPage.tsx）：
   - 表单：ticker / start_date / split_date / 成本 / 窗口 / 可勾选模型子集。
   - 结果表：每行一个策略/模型，列 = 总收益 / Sharpe / 最大回撤 / 换手(number_of_trades) /
     成本 / 方向准确率(仅 ML)。用 summary 高亮每列最优（best_* 命中的 label 加标记）。
   - 顶部一行"评估区间"标注 test_start–test_end + 一句 "所有策略在同一样本外窗口对比"。
   - 每个 ML 模型下方一个特征重要性小条形图（feature_importance）。
   - interpretation 串以"读法提示"呈现（ML 未必赢、准确率≠收益等）。
   - loading/error 用 lib/apiRequest 的 getApiDisplayMessage。

3) i18n.ts 加中英文文案（模块名 "Compare Models / 模型对比"、列名、特征名、读法提示）。
4) 导航：workspaceNav.ts 的 tools 组把 Compare 指向新的 Compare Models（或并列新增一项）。

完成标准：npx tsc --noEmit && npm test && npm run build 全绿；
本地 npm run dev 打开页面，填参数能看到规则策略 vs ML 模型在同一 OOS 窗口的真实对比 + 特征重要性。
```

---

## Prompt CM-5 —（可选·收尾与叙事）

```
1) 本地 curl 自测：
   curl -s -X POST http://127.0.0.1:8000/api/v1/models/compare -H 'content-type: application/json' \
     -d '{"ticker":"SPY","start_date":"2018-01-01","split_date":"2023-01-01","transaction_cost":0.001,
          "short_window":20,"long_window":60,"momentum_window":20}'
2) README 模块列表把 Compare Models 标为"已实现：规则策略与 XGBoost/LightGBM 等 ML 模型在
   同一样本外窗口、防泄漏地对比 Return/Sharpe/Drawdown/Turnover/Cost，含特征重要性与方向准确率。"
3) （可选）把对比结果接进 Investment Memo：让 Copilot 基于这份 results 生成一段解释
   （谁更好、为什么、风险在哪），严守"LLM 解释、不预测"。
```

---

## 这个模块的面试价值（你可以照着讲）
- **模型选择与评估**：多模型同台，用**样本外**指标而非训练集表现比较。
- **时间序列防泄漏**：时序切分 + embargo + 只在训练集 fit + 标签/特征时序对齐——
  并且有**单测守卫**（含"随机游走上准确率不应异常高"的泄漏烟雾测试）。这是最能体现严谨的点。
- **可解释性**：特征重要性 + 方向准确率 + 规则型读法提示（+ 可选 LLM 解释）。
- **工程一致性**：ML 与规则复用同一回测/成本/指标管线，对比才可信。
- **诚实**：方向准确率明确标注"非收益承诺"；ML 未必赢，也如实展示。
