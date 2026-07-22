# 招聘视角执行清单 · P0/P1 + 冷启动解决

按"招聘方看到你的顺序"排。P0 不做，后面都白搭。

---

## 🔴 冷启动 / demo 挂掉 —— 已给解决方案（先做）

**根因**：Render 免费档闲置 15 分钟休眠，冷启动 30–60s；且 Supabase 免费档约 7 天无活动会暂停 → research 路由 503。招聘方点开正好遇上 = 致命第一印象。

**已交付**：`.github/workflows/keep-warm.yml`（本次新建）——每 10 分钟 ping
`/api/database/status`，一箭双雕唤醒 Render + 让 Supabase 不被暂停。

**你要做的三步：**
1. 提交这个 workflow 到 GitHub；到仓库 **Settings → Secrets and variables → Actions →
   Variables** 新建 `BACKEND_URL = https://<你的服务>.onrender.com`（不设则用默认值）。
   到 Actions 页手动 Run 一次确认能跑通。
2. 如果 Supabase 已被暂停：登录 Supabase 控制台 → 项目 **Restore / 恢复**（几十秒）。
3. **更稳的叠加（推荐）**：再注册 UptimeRobot（免费，5 分钟间隔）监控同一个
   `/api/database/status` URL——GitHub 定时任务是尽力而为、可能延迟，UptimeRobot 更准时。
4. **面试季**：临时开 Render Starter **$7/月**（常驻不休眠、彻底消除冷启动），面试完降回免费。

> 一句话：workflow + Supabase 恢复 + （可选）UptimeRobot = 免费把 demo 稳住；面试季再花 $7 保险。

---

## P0 · 这周（决定 30 秒第一印象 + 拆判断力红旗）

| # | 动作 | 用哪份 prompt |
|---|---|---|
| P0-1 | 保活 + 恢复 Supabase（见上） | `.github/workflows/keep-warm.yml`（已建） |
| P0-2 | 拍平导航、露出旗舰模块、换品牌、响应式 | `CURSOR_NAV_UI_OVERHAUL_PROMPTS.md` → NAV-1/2/3 |
| P0-3 | 删 8 个空壳路由 | `CURSOR_RISK_REVIEW_PROMPTS.md` → R-0 |
| P0-4 | 删 / 明确标注 `apps/api/`（消除两套后端） | `PROJECT_REVIEW.md` 第1节 + 下方 Prompt H-1 |

## P1 · 补深度与门面（招聘经理看深度，HR 扫门面）

| # | 动作 | 用哪份 prompt |
|---|---|---|
| P1-1 | 接活风控引擎 → 真 Risk Review | `CURSOR_RISK_REVIEW_PROMPTS.md` → R-1/R-2/R-3 |
| P1-2 | 真 ML：规则 vs XGBoost/LightGBM，防泄漏 | `CURSOR_COMPARE_MODELS_PROMPTS.md` → CM-1…5 |
| P1-3 | 模型对比可视化 | `CURSOR_UI_OPTIMIZE_PROMPTS.md` → UI-0/UI-1 |
| P1-4 | 页面术语去学术化 + 首页故事 | `V2_PHASE1_RENAME_PROMPTS.md` → P1-B/P1-C |
| P1-5 | README-for-recruiters + 截图/演示 | 下方 Prompt H-2（新） |

## P2 · 打磨
一致性(UI-2)、Dashboard+拆巨型组件(UI-3)、诚实加一个 LSTM（离线训练）。

---

## Prompt H-1 —（低风险）消除"两套后端"

```
仓库里有两套后端：backend/（9718 行，真部署、全功能）与 apps/api/（615 行，只做了
CreateResearch 一个用例、内存仓库、未部署）。对招聘方，apps/api/ 现在是"未完成的重构"，
是判断力负分。二选一执行（默认选 A）：

A. 删除 apps/api/ 整个目录；把其中体现的 clean-architecture / vertical-slice 意图，
   浓缩成一段设计说明放到 docs/ARCHITECTURE.md 里（作为"目标架构"的文字愿景，而非半成品代码）。
   同步删除根 README / CI 里对 apps/api 的引用与其独立测试步骤。

B. 若想保留：在 apps/api/README.md 和根 README 顶部用一句话明确标注
   "架构探索样本，不参与运行、不在部署路径中"，并从 CI 必跑步骤里移出，避免让人误以为是主干。

完成后确保根 README 的"Getting started / CI"描述与实际一致；前端后端主测试全绿。
```

## Prompt H-2 —（HR 门面）README 顶部 + 截图/演示

```
目标：让非技术 recruiter 扫 README 前半屏就懂"这是什么、用了什么、去哪看"。

编辑 README.md（配合 V2_PHASE1_RENAME 的 P1-D 定位改写，一起做）：
1. 顶部依次：产品名(AI Investment Intelligence Platform) → 一句话价值 →
   一行徽章(技术栈：Next.js / FastAPI / PostgreSQL / scikit-learn·XGBoost·LightGBM /
   DeepSeek LLM) → "Live Demo" 链接 + "Demo video/GIF" 链接。
2. 紧接着放 2–4 张截图（Dashboard、Compare Models 对比图、Risk Review、Investment Memo）。
   在 README 引用 docs/screenshots/ 下的图片；若图片暂缺，先放占位并在
   docs/screenshots/README.md 写明每张应截什么画面（拍图动作由人来做）。
3. 一段"What it does"用 5 条人话 bullet（发现机会 / AI 解读信息 / 对比模型 /
   历史验证 / 可解释备忘录），每条一句，去学术黑话。
4. 保留底部合规声明（仅供研究·非投资建议）——这是成熟度加分项。
5. 关键词自然融入正文，便于 HR 关键词匹配：机器学习、模型评估、防数据泄漏、回测、
   推荐排序、LLM 集成、可解释性、A/B 对比、FastAPI、Next.js、CI。

不改任何技术小节的事实（命令、端口、部署步骤保持准确）。
```

---

## 记住这条（对两类招聘方都成立）
**聚焦、能跑、有深度的一个项目 > 摊得很大的半成品。**
先救活 demo（免费保活）→ 露模块+换品牌 → 删杂物 → 补真 ML → README 门面。
这不是按工作量排，是按"招聘方看到你的先后"排。
