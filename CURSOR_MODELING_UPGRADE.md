# Cursor 指令 · 建模升级 v2（特征可见 / PCA·特征选择 / 模型可选 / 高级模型）

按反馈修订：**一切做成用户可勾选的选项，不硬加**（沿用现有 `MODEL_OPTIONS` 复选框模式）；
**前端要能看到用了哪些特征、经过什么预处理**；诚实区分模型适用范围。

复用：`backend/app/models/{features.py, model_registry.py, model_comparison.py}`、
路由 `app/api/routes/model_comparison.py`、前端 `ModelComparisonPage.tsx`（含 `MODEL_OPTIONS`）。
**防泄漏三纪律照旧**：时序切分不洗牌；预处理/模型只在训练集 fit；特征只用过去、标签用未来 + embargo。
完成标准：后端 `PYTHONPATH=. pytest -q`、前端 `npx tsc --noEmit && npm test -- --run && npm run build` 全绿。

---

## M-1 —（特征）扩到 ~15–20 个 + 前端可见

```
A. backend/app/models/features.py 扩展 FEATURE_COLUMNS（全部历史滚动、防泄漏，保持
   _assert_no_future_feature_columns 通过）：多周期动量(return_5d/10d/120d)、
   均线间隙(ma5_gap/ma10_gap 及 short/long 比)、波动率(volatility_60d、vol_ratio_20_60)、
   多周期 RSI(rsi_7/rsi_21)、MACD(ema12-ema26 及 signal)、布林带位置((close-ma20)/(2*std20))、
   量能(volume_change_5d、OBV 归一化)、距 52 周高低(close/rolling_max_252-1、close/rolling_min_252-1)。
   注释写明：日频单标的样本有限，特征 15–20 个即可，别几百个（过拟合）。

B. **让前端看到用了哪些特征**：在 run_model_comparison / walk-forward 的返回体加
   "feature_set": { "columns": FEATURE_COLUMNS, "count": len }，路由透传。
   前端 ModelComparisonPage 加一个"Features used / 使用的特征"折叠面板，列出每个特征名
   （中英文说明可用 i18n 短描述），让评审一眼看到模型吃了哪些输入。

测试：断言 feature_set.columns 非空、无 y_/next_/future_ 列、count 与列表一致。pytest 全绿。
```

## M-2 —（预处理）PCA / 特征选择，做成可选且**在 UI 可见**

```
加一个可选预处理阶段，放在 scaler 之后、模型之前，**只在训练集 fit**，并把过程暴露给前端。

后端：
1) 请求体加 preprocessing: "none" | "pca" | "select_kbest" | "l1_select"（默认 "none"），
   以及可选 pca_components:int / select_k:int。
2) 在建模管线里按选项插入：
   - "pca": sklearn PCA(n_components=pca_components) —— 记录 explained_variance_ratio_（累计）。
   - "select_kbest": SelectKBest(f_classif, k=select_k) —— 记录被选中的特征名与分数。
   - "l1_select": SelectFromModel(LogisticRegression(penalty="l1", solver="liblinear")) —— 记录保留特征。
   全部只 fit 训练集，测试集只 transform（防泄漏）。
3) 返回体加 "preprocessing": {
     "method": <所选>,
     "pca": {"n_components", "explained_variance_ratio":[...], "cumulative":<float>} | null,
     "selection": {"selected_features":[...], "dropped_features":[...]} | null }

前端：ModelComparisonPage 加"Preprocessing / 预处理"控件（下拉：无 / PCA / SelectKBest / L1 选择）+
展示结果面板：
   - PCA → 一张碎石图/累计方差条，标注"前 N 个主成分解释 X% 方差"。
   - 选择类 → 高亮"保留的特征 / 丢弃的特征"。
让"降维/选特征这一步"在界面上看得见。

测试：三种预处理各能跑通、PCA 返回方差比、选择类返回被选特征、评估仍只在 OOS。pytest 全绿。
```

## M-3 —（模型）扩成可勾选注册表，**不硬加**；诚实分类

```
把模型做成和现有 MODEL_OPTIONS 一样的可勾选清单，默认勾选合理子集，其余可选。
**关键：不同模型属于不同范式，要如实归类，别硬塞进方向分类。**

A. 方向分类器（预测次日涨/跌 → signal，直接进 Compare Models）：
   backend/app/models/model_registry.py 增加构造器并注册：
   - "logistic_l2"（现有 logistic）
   - "logistic_l1"（penalty="l1", solver="liblinear"）—— 对应 Lasso 式稀疏
   - "logistic_en"（penalty="elasticnet", solver="saga", l1_ratio=0.5）—— ElasticNet 式
   - "ridge_clf"（RidgeClassifier）—— Ridge 式
   - "svm"（SVC(kernel="rbf", probability=True) 套 StandardScaler 管线）
   - 现有 random_forest / xgboost / lightgbm 保留
   注意：SVC(rbf) 无 coef_/feature_importances_ → 把 feature_importance() 改成
   **取不到时返回 {} 而不是抛异常**（前端该模型就不画特征重要性，合理）。

B. 收益回归器（预测次日收益 → 取符号 → signal；用你说的 Ridge/Lasso/ElasticNet 本尊）：
   - "ridge_reg"(Ridge)、"lasso_reg"(Lasso)、"elasticnet_reg"(ElasticNet)
   预测 next-day return，>0 记 1、否则 0，再走同一回测管线。
   （这直接用到 Ridge/Lasso/ElasticNet 回归，和分类器形成对比，叙事更丰富。）

C. 单变量时序（ARIMA）：
   - "arima"：statsmodels ARIMA 对收益序列滚动预测下一日收益 → 取符号 → signal。
     注意它**不吃 M-1 的特征**（纯时序），返回里标注 uses_features=false，诚实呈现。
   requirements 加 statsmodels（较轻，可进 requirements.txt）。

D. **GARCH 不进方向对比** —— 它是**波动率**模型，不是方向模型。正确做法：
   在 Risk Review 里用 GARCH 预测的条件波动率喂"波动率档"（正好补上我们之前发现的
   volatility 恒为 1 的死档）。在本文件不加进 Compare Models；如需要，单独一条 Risk Review 指令。

E. 前端：ModelComparisonPage 的 MODEL_OPTIONS 扩成上面的可勾选项（分组：
   "线性/正则" | "树/提升" | "间隔(SVM)" | "回归取符号" | "时序(ARIMA)"），
   每项加 i18n label。后端 models 参数已支持子集，勾选即生效。

测试：每个新模型能单独跑通、component/metrics 正常；SVM 无重要性时返回 {} 不报错；
回归取符号路径产出 signal 正确。pytest 全绿。
```

## M-4 —（高级模型，可选开关）CNN / LSTM，离线训练接入

```
CNN、LSTM 作为**可勾选的离线模型**（不进 Render 运行时、不装 torch）：
- requirements-dev.txt 加 torch>=2.2（仅 dev）。
- scripts/train_cnn.py 与 scripts/train_lstm.py：用 build_feature_frame 构造 [seq_len×n_features]
  序列样本，防泄漏切分 + 训练段内验证 early stopping + embargo，测试段预测 → signal →
  同一回测管线 → 产出 artifact JSON 到 app/models/artifacts/{cnn,lstm}_<ticker>.json
  （label/kind/strategy/trained_at/metrics/directional_accuracy/equity_curve/note）。
- model_comparison 泛化 artifact 加载：扫描 artifacts/ 下所有兼容 JSON，各追加一行，
  source="offline_artifact"+trained_at；**只读 JSON 不 import torch**。
- 前端把 CNN/LSTM 也列进 MODEL_OPTIONS（分组"深度学习·离线"），勾选=是否纳入对比；
  该行加"Offline-trained·日期"徽章，hover 提示可用脚本复现。
```

## M-5 —（可选）超参调优：时序 CV
```
加可选 tune:bool；tune=True 时对所选模型用 TimeSeriesSplit（禁止 KFold/洗牌）在**训练集内**
RandomizedSearchCV（网格小、偏正则），refit 后照常在 OOS 评估；返回 best_params 供前端展示。
interpretation 里诚实标注："金融数据调优易过拟合验证集，结论以样本外为准。"
```

## M-6 —（展示页）模型方法论 + "哪个模型好"的结论
```
在 ModelComparisonPage 结果区加两块，让评审看懂"怎么比的"和"结论是什么"：

1) "方法论 / Methodology" 折叠说明（i18n 静态文案 + 小图示）：
   - 一段人话讲清：防泄漏时序切分、样本外评估、所有模型走同一回测/成本管线、
     directional accuracy ≠ 收益。
   - 每个模型家族一句定位：线性/正则(logistic/ridge/lasso/EN)、树/提升(RF/XGB/LGBM)、
     间隔(SVM)、收益回归取符号、单变量时序(ARIMA)、深度学习(CNN/LSTM·离线)。

2) "结论 / Which model is best"（数据化，一句话 + 依据）：
   - 读 summary 与各模型 OOS 指标，给出"样本外最佳 Sharpe=X（模型名）；最高收益/最低回撤分别是谁；
     但换手与成本如何"，并诚实提示"未必在其它区间也最好——见 walk-forward 逐折稳定性"。
   - 可选：把这份 results 交给 Copilot(DeepSeek) 生成一段解释，严守"解释不预测、不承诺收益"。
tsc+test+build 全绿。
```

## M-7 —（新闻→情感特征）favourable / not / 5 档，复用 DeepSeek
```
用 LLM 对新闻做情感，最简单 favourable / neutral / not_favourable，或 1–5 档。
**诚实前提（务必遵守）**：把情感当**历史回测特征**需要 point-in-time 新闻（预测日收盘前已发布、带时间戳），
否则是未来函数。没有历史带时间戳新闻时，只做"当前定性面板"，不喂进历史回测、不声称防泄漏。

先做 A（低风险、马上有价值）：
A. "AI Insights · 新闻情感"面板（当前时点、定性、不进回测）：
   - 后端新增 /api/v1/insights/news-sentiment：输入 ticker（+可让用户粘贴新闻），
     取最近若干条标题/摘要，调 DeepSeek 输出：
       { overall: "favourable"|"neutral"|"not_favourable", score_1_5:int,
         items:[{headline, stance, reason, citation}] }
     沿用 Copilot 的系统策略：基于所给文本解释、给理由与引用，**不预测价格、不承诺收益**。
   - 前端一张卡：5 档着色(1 很不利 … 5 很有利) + 每条要点。标注"AI 解读，非投资建议"。
（进阶）B. 真当回测特征：需历史带时间戳新闻数据集，把每日情感分对齐到"该日收盘前已知"，
   作为新特征列并入 M-1，严格 point-in-time。没有此数据就**只做 A**，并如实说明原因。
后端 pytest / 前端 tsc+test+build 全绿。
```

---

## 附录 · RL（单独实验件，不进方向对比）
```
stable-baselines3 + gymnasium（dev-only）；自定义 gym 环境：单标的、离散动作(空/持/满)、
reward=次日收益-成本、状态=特征窗口；训练段学策略、测试段仅评估、含成本、禁未来信息；
产出 artifact 作为一行，明确标注"RL·离线·实验性·非收益承诺"。
面试话术：RL 业界主用于最优执行/做市，方向 alpha 上生产少、易过拟合——你做的是受约束、
可复现、如实标注局限的实验。
```

## 诚实红线（务必保留）
- 特征 15–20 个即可；PCA/选择只在训练集 fit。
- 模型分范式如实归类：GARCH 是波动率不是方向；ARIMA 不吃特征要标注。
- DL/RL 全部离线训练、提交 artifact，Render 只服务结果。
- 一切以**样本外**表现为准；directional accuracy 标注"非收益承诺"。
```
