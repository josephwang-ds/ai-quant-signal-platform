# 部署闭环 Runbook + 修文档 Cursor 指令

线上闭环 = **Supabase(DB) → Render(FastAPI) → Vercel(Next.js) → DeepSeek(Copilot)**，
浏览器里能跑通：`创建研究 → 执行 → 验证 → 评估 → 人工决策 → Copilot`。

> 现状：`docs/reviews/DEPLOYED-E2E-VERIFICATION.md` 记录本套曾于 2026-07-15 部署跑通
> （Render 后端 + Vercel `signals.josephjwang.com` + CORS 全绿）。所以这不是从零搭，
> 而是**照 runbook 复现 / 重新验证**，并顺手补掉 3 个会坑下一个部署者的缺口。

---

## ⚠️ 三个真实缺口（会让闭环断掉）

1. **README 数据库引导漏了迁移**（最致命）
   `README.md` 第 207 行只让你 apply `backend/db/schema.sql`。但研究链路的表
   （strategies / research / experiment_runs / validation_runs / evaluations / decisions /
   lifecycle_events）全在 `backend/db/migrations/0002–0006` 里。只跑 schema.sql →
   线上只有回测表 → **所有 `/api/v1/research/*` 返回 503，整条闭环断**。
   → 正确顺序在 `backend/db/migrations/README.md` 里（本 runbook 第 1 步照抄）。

2. **迁移 README 引用了不存在的脚本**
   `backend/db/migrations/README.md` 的 "Restart verification" 说用
   `verify_durable_research_spine.py --phase before/after`。该脚本不存在，参数也不存在。
   真实脚本是 `backend/scripts/verify_deployed_research_api.py`，参数为
   `--base-url --symbol --start-date [--end-date --timeout --verbose]`。

3. **Render 免费档会休眠**
   冷启动首个请求可能 30–60s 甚至超时。验证前先手动 `curl /health` 唤醒，再跑后续。

（第 1、2 条用文末的 Cursor prompt 修掉；第 3 条是运维习惯。）

---

## 手动 Runbook（你在各控制台照做）

### 第 1 步 · Supabase：按顺序执行 SQL（关键）
Supabase 项目 → SQL Editor → 依次粘贴执行下列文件全文，**顺序不能乱**：

1. `backend/db/schema.sql`                               （回测基线表）
2. `backend/db/migrations/0002_durable_research_spine.sql`
3. `backend/db/migrations/0003_seed_canonical_research.sql`
4. `backend/db/migrations/0004_idempotency_keys.sql`
5. `backend/db/migrations/0005_seed_safe_noop.sql`
6. `backend/db/migrations/0006_human_decision.sql`

验证（在 SQL Editor 跑）：
```sql
-- 7 张表都在
select table_name from information_schema.tables
where table_name in
('strategies','research','experiment_runs','validation_runs','evaluations','decisions','lifecycle_events');
-- 种子研究在
select id, status from research where id = 'ma-crossover-spy';
```

### 第 2 步 · Render：后端环境变量
Render 服务（Blueprint 来自 `render.yaml`）→ Environment。`render.yaml` 里标了
`sync: false` 的必须在面板手填，**永不提交到仓库**：

| 变量 | 值 |
|---|---|
| `ALLOWED_ORIGINS` | 你的 Vercel 前端确切来源，逗号分隔，**不带路径、不带通配符**。例：`https://signals.josephjwang.com` |
| `SUPABASE_DB_URL` | Supabase **Transaction Pooler** 连接串（不是 direct）；仅后端 |
| `LLM_API_KEY` | DeepSeek 密钥；仅后端 |
| `LLM_PROVIDER` | `deepseek`（render.yaml 已带默认，可不填） |
| `LLM_BASE_URL` | `https://api.deepseek.com`（已带默认） |
| `COPILOT_MODEL` | `deepseek-v4-flash`（已带默认，且是当前有效模型） |

改完 **Manual Deploy / 触发一次重部署**（新增的 sync:false 变量对已存在服务不会自动生效）。

### 第 3 步 · Vercel：前端环境变量
Vercel 项目 → Settings → Environment Variables：

| 变量 | 值 |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | 你的 Render 后端来源，例 `https://ai-quant-signal-platform.onrender.com`（绝对 http/https，尾斜杠可选） |

⚠️ `NEXT_PUBLIC_*` 是**编译进浏览器包**的，改完必须**重新 Deploy** 才生效。

### 第 4 步 · 验证闭环（把 API_BASE 换成你的 Render 域名）
```bash
API=https://ai-quant-signal-platform.onrender.com

# 1) 先唤醒 + 进程存活
curl -s "$API/health"                    # 期望 {"status":"ok",...}

# 2) 数据库连上没
curl -s "$API/api/database/status"       # 期望 configured:true, connected:true

# 3) 数据源
curl -s "$API/api/data-sources/status"

# 4) 真实执行链路（后端脚本；在 backend/ 下）
cd backend && PYTHONPATH=. python scripts/verify_deployed_research_api.py \
  --base-url "$API" --symbol SPY --start-date 2022-01-01 --verbose
```
`/api/database/status` 返回 `configured:true, connected:false` → 503，说明
`SUPABASE_DB_URL` 没配或连不上（多半是用了 direct 连接串而非 pooler）。

### 第 5 步 · 浏览器端到端
打开 Vercel 前端 → 选中 `ma-crossover-spy` → 按顺序点：
**Run Experiment → Run Validation → Request Evaluation → Request Human Decision → Open Research Copilot**。
每一步的数字都应来自后端；Copilot 能基于证据作答即闭环打通。

---

## Cursor 指令 A —（低风险）修 README 数据库引导，补上迁移

```
编辑 README.md 的 "### Database bootstrap and verification" 小节（约第 205–207 行）。
现在它只写了 "Apply backend/db/schema.sql ... then verify"，漏掉了研究链路必需的迁移，
会导致新部署的 /api/v1/research/* 全部 503。

把这一段改成：明确要求按顺序在 Supabase SQL Editor 执行：
  1. backend/db/schema.sql
  2. backend/db/migrations/0002_durable_research_spine.sql
  3. backend/db/migrations/0003_seed_canonical_research.sql
  4. backend/db/migrations/0004_idempotency_keys.sql
  5. backend/db/migrations/0005_seed_safe_noop.sql
  6. backend/db/migrations/0006_human_decision.sql
并加一句：完整顺序与验证见 backend/db/migrations/README.md。
保留原有的 curl $API_BASE_URL/health 和 /api/database/status 验证示例。
只改这一小节，不要动 README 其它部分。
```

## Cursor 指令 B —（低风险）修迁移 README 里不存在的验证脚本

```
编辑 backend/db/migrations/README.md 的 "Restart verification" 小节。
它当前引用 backend/scripts/verify_durable_research_spine.py 和 --phase before/--phase after，
这个脚本和这些参数都不存在。

改成引用真实脚本 backend/scripts/verify_deployed_research_api.py，其真实参数为：
  --base-url <后端origin>  --symbol <代码>  --start-date <YYYY-MM-DD>
  可选：--end-date  --timeout(默认60)  --verbose
给出一个可照抄的例子：
  cd backend && PYTHONPATH=. python scripts/verify_deployed_research_api.py \
    --base-url "$API_BASE_URL" --symbol SPY --start-date 2022-01-01 --verbose
说明它验证的是部署后 research execution API 是否返回真实计算结果；
删除任何关于 --phase before/after 的描述。只改这一小节。
```

> 两条都是纯文档修正，跑不跑测试都行；改完 `git diff` 看一眼即可提交。
