# 执行总纲 · AI Investment Intelligence Platform 改造

把仓库根目录这几份 Cursor 指令按下面顺序推。每条完成标准都写在各自文件里
（后端 `PYTHONPATH=. pytest -q`；前端 `npx tsc --noEmit && npm test && npm run build` 全绿）。
原则：**只在 `backend/` 上做后端；改动只改显示名不改 URL（除删空壳）；重模型离线训练。**

---

## 阶段 0 · 清理地基（先做，低风险）
| 步骤 | 文件 / 动作 | 目的 |
|---|---|---|
| 0-1 | `CURSOR_RISK_REVIEW_PROMPTS.md` → **R-0** | 删 8 个空壳路由 |
| 0-2 | 删除 / 明确标注 `apps/api/`（见 `PROJECT_REVIEW.md` 第1节） | 消除"两套后端"困惑 |

## 阶段 1 · 外壳与故事（视觉冲击最大，优先）
| 步骤 | 文件 | 目的 |
|---|---|---|
| 1-1 | `CURSOR_NAV_UI_OVERHAUL_PROMPTS.md` → **NAV-1/2/3** | 拍平导航、露出旗舰模块、换品牌、响应式 |
| 1-2 | `V2_PHASE1_RENAME_PROMPTS.md` → **P1-B / P1-C / P1-D** | 页面术语去学术化、首页故事、README 定位 |
> 注：`CURSOR_SIMPLIFY_PROMPTS.md` 与 P1-A 已被 NAV-1 覆盖，可跳过。

## 阶段 2 · 两个旗舰模块（技术深度）
| 步骤 | 文件 | 目的 |
|---|---|---|
| 2-1 | `CURSOR_RISK_REVIEW_PROMPTS.md` → **R-1/R-2/R-3** | 把已有风控引擎接成真 Risk Review（前后端+测试）|
| 2-2 | `CURSOR_COMPARE_MODELS_PROMPTS.md` → **CM-1…CM-5** | 规则 vs XGBoost/LightGBM，防泄漏、同 OOS 窗口对比 |
| 2-3 | `CURSOR_UI_OPTIMIZE_PROMPTS.md` → **UI-0 / UI-1** | 模型对比可视化（净值叠加/风险收益散点/排名/特征重要性）|

## 阶段 3 · 全站打磨
| 步骤 | 文件 | 目的 |
|---|---|---|
| 3-1 | `CURSOR_UI_OPTIMIZE_PROMPTS.md` → **UI-2** | 数字格式/涨跌配色/三态/响应式表格统一 |
| 3-2 | `CURSOR_UI_OPTIMIZE_PROMPTS.md` → **UI-3** | 首页 Dashboard 收口 + 拆 6 万字节巨型组件 |

## 阶段 4 · 部署闭环
| 步骤 | 文件 | 目的 |
|---|---|---|
| 4-1 | `DEPLOY_CLOSED_LOOP.md` → 手动 runbook | Supabase 迁移顺序 / Render 环境变量 / Vercel / CORS / 验证 |
| 4-2 | `DEPLOY_CLOSED_LOOP.md` → 指令 A/B | 修 README 漏迁移、修不存在的验证脚本引用 |

## 可选 · 进阶模型（面试王牌，非必需）
- **LSTM（深度学习）**：加进 Compare Models 框架，**离线训练**、如实展示"未必赢"。
- **RL（强化学习）**：单独 Phase 3 模块，范围收窄（单标的、离散动作、含成本、OOS）。
- 两者都**离线训练、提交结果**，线上不装 torch（保 Render 轻）。
- （这两条 Cursor 指令我可以再单独出，未包含在上面文件里。）

---

## 部署与成本策略（Render 现状：免费档闲置 15 分钟休眠、冷启动 30–60s、512MB）
1. **先免费优化**：加免费保活 ping（UptimeRobot / cron-job.org / GitHub Actions，每 10–14 分钟打 `/health`）；后端保持轻；**重模型离线训练、提交结果**。
2. **只在面试季**临时开 **Render Starter $7/月**（常驻不休眠、消除冷启动首屏），面试完降回免费。
3. **不建议只为省钱换主机**；现有 Render+Supabase+Vercel 已跑通且有文档。想换主机只在"想学 Cloud Run / 想用 HF Spaces 做 ML 门面"时才划算。

## 一句话优先级
**先阶段 0+1（清理+外壳，几小时见效、冲击最大）→ 再阶段 2（旗舰模块，技术深度）→ 阶段 3 打磨 → 阶段 4 部署。** 面试季再花 $7 消冷启动。
