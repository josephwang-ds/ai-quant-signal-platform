# 上线前 Checklist（feat/v2-hiring-refresh → main）

按顺序过。目的：把这一大批(导航/品牌/Risk Review/Compare Models/14+ 模型/PCA/调优/CNN·LSTM·RL 离线/AI Insights/首页精简)安全合并上线，且**默认 demo 路径又快又绿**。

---

## ☐ 1. 生成离线 artifact（CNN / RL）
现在 `backend/app/models/artifacts/` 只有 `lstm_SPY.json`，CNN/RL 勾了没数据。
在 `backend/`（已装 dev 依赖：torch 等）跑：
```bash
cd backend && source .venv/bin/activate
PYTHONPATH=. python3 scripts/train_cnn.py --ticker SPY --split-date 2022-01-01
# 若有 RL 训练脚本：
PYTHONPATH=. python3 scripts/train_rl.py  --ticker SPY --split-date 2022-01-01
ls app/models/artifacts/   # 应看到 cnn_SPY.json (+ rl_SPY.json)
```
> artifact 的 `.json` 要提交（运行时读它）；`.pt/.zip` 权重可选提交（复现用）。

## ☐ 2. 默认只勾"快模型" + 调高重端点超时（治残留的"每次 fail"）
- **前端默认选择**：`components/features/comparison/ModelComparisonPage.tsx` 里模型多选的
  初始 state，默认只勾 **logistic + random_forest + xgboost**（快）。
  SVM(rbf)、ARIMA、CNN/LSTM/RL、以及"全勾"留给用户手动，避免免费档一次训一堆超时。
- **超时**：给 `/api/v1/models/compare` 单独用更长超时（如 120s）。
  看 `lib/apiRequest.ts`（`API_REQUEST_TIMEOUT_MS`）或 `lib/api.ts` 里 `runModelComparison` 的
  超时设置，把这个重端点调到 120s；`/health`、`/status` 保持 5s。
- （可选）后端启动时预热一次 xgboost/lightgbm import，避免首调付导入成本。

## ☐ 3. 本地全量验证（三个都要绿）
```bash
# 后端
cd backend && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt   # 确保 statsmodels 等都在
PYTHONPATH=. pytest -q                                     # ARIMA 测试需 statsmodels

# 前端
cd ../frontend
npx tsc --noEmit && npm test -- --run && npm run build
```
全绿再进下一步；有红贴出来先修。

## ☐ 4. 提交 + 合并到 main + 盯 Render 重建
```bash
rm -f .git/index.lock         # 僵尸锁若在
git add -A                    # 若 notes/ 已 gitignore，这里安全（不会带进工作笔记）
git commit -m "feat: modeling suite (features/PCA/tuning/offline DL·RL) + AI Insights + risk/landing fixes"
git push
# 到 GitHub 开/更新 PR，等 CI 绿 → Merge 到 main
```
merge 后 **Render 自动重建后端**（这次要装 numpy/sklearn/xgboost/lightgbm/statsmodels，构建更慢更大）：
- 到 Render 面板盯这次 deploy 的 build 日志。**成功** = 收工；**失败(OOM/超时)** = 贴日志给我，
  用 HistGradientBoosting 等减重方案。
- Vercel 自动重建前端；生产 `signals.josephjwang.com` 更新后 **硬刷新 Cmd+Shift+R**。

## ☐ 5. Render 环境变量
- `FINNHUB_API_KEY`（sync:false）：填了走 Finnhub 新闻；**不填则自动回退 yfinance**（零成本、无情感，也能跑）。
- 确认 `LLM_API_KEY / SUPABASE_DB_URL / ALLOWED_ORIGINS` 都在（AI Insights 的总结用 LLM）。

---

## ☐ 6. 上线后冒烟（把 API 换成你的 Render 域名）
```bash
API=https://ai-quant-signal-platform.onrender.com
curl -s "$API/health"
curl -s "$API/api/database/status"                 # connected:true
# Compare Models（默认快模型子集）
curl -s -X POST "$API/api/v1/models/compare" -H 'content-type: application/json' \
  -d '{"ticker":"SPY","start_date":"2018-01-01","split_date":"2023-01-01","transaction_cost":0.001,
       "short_window":20,"long_window":60,"momentum_window":20,"models":["logistic","random_forest","xgboost"]}'
# Risk Review
curl -s -X POST "$API/api/v1/risk/review" -H 'content-type: application/json' \
  -d '{"ticker":"SPY","start_date":"2022-01-01","strategy":"ma_crossover","short_window":20,"long_window":60,"transaction_cost":0.001}'
# AI Insights
curl -s -X POST "$API/api/v1/insights/news-sentiment" -H 'content-type: application/json' -d '{"ticker":"AAPL"}'
```
浏览器再走一遍：Compare Models(默认子集秒出) → Risk Review(档位随股票变、不再永远 L5) → AI Insights(5 档 + 总结)。

---

## 完成后
- demo 稳定在线 + 默认路径快 = 可以往招聘方发链接了（面试季记得开 keep-warm，或 $7 Starter）。
- 这份 checklist 是工作笔记，建议放本地 `notes/`（已 gitignore），别提交进 repo。
