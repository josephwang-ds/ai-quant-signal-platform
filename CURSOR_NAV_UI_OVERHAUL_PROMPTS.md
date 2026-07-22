# Cursor 指令 · 导航与外壳彻底重构（把主内容"挖出来"）

## 现状诊断（根因）
`frontend/components/layout/SideNav.tsx` 里：
- 第一组只显示"研究库 / 当前研究"两项。
- **所有功能模块**（Strategy Lab、Compare、Robustness、Paper Trading、Market Watch、Data、
  Saved Runs）被包在一个**默认折叠的 `<details>` "更多工具"（navGroupSecondary）** 里。
→ 用户打开首屏根本看不到你能打的模块。品牌还停留在 "AI Quant Research"。

## 目标
拍平导航：旗舰模块**全部一级可见、无需展开**；重命名品牌与标签；侧栏做出层次与响应式。

完成标准：`npx tsc --noEmit && npm test && npm run build` 全绿。

---

## Prompt NAV-1 —（核心）重写 SideNav：拍平 + 分区 + 露出旗舰

```
重写 frontend/components/layout/SideNav.tsx 与 frontend/lib/workspaceNav.ts，
让所有核心模块一级可见，去掉把功能藏进 <details> "更多工具" 的做法。

新的侧栏信息架构（分区标题 + 一级链接，全部默认展开）：

  概览 / Overview
    · Dashboard              → "/"（或 /overview，取现有首页路由）
  研究 / Research
    · Investment Ideas       → 研究库（原 navResearchWorkspace，href "/"，若与 Dashboard 冲突则
                                Dashboard 用 /overview、Investment Ideas 用 "/"）
    · Current Study          → 当前研究（现有 currentResearchHref）
  分析与建模 / Analyze & Model
    · AI Watchlist           → /market-watch
    · Strategy Studio        → /strategy-lab
    · Compare Models ⭐       → /comparison（或 /compare-models，若已建新路由）
    · Performance Review     → /robustness 里若含 OOS/验证则并入；否则指向验证工具
    · Risk Review            → /risk-gate-review
    · Paper Trading          → /paper-trading
  资料 / Archive（这一组可保留可折叠 <details>，因为是次要）
    · Data                   → /data-center
    · Saved Runs             → /experiments

实现要求：
- 把上面除 Archive 外的所有分组都渲染成**始终展开**的分区（普通 div + 分区小标题），
  不要再用默认折叠的 <details> 包住核心模块。
- Archive 组可以继续用 <details>（默认折叠 OK），因为它确实是次要资料。
- 每个链接沿用现有 isWorkspaceNavItemActive 判定 active 高亮。
- workspaceNav.ts 里重构 WORKSPACE_NAV_GROUPS 为上面的分区结构（新增 overview / research /
  analyze 分组；把 market-watch/strategy-lab/comparison/risk-gate-review/paper-trading 放进 analyze；
  data-center/experiments 放 archive）。为缺失的 labelKey 在 i18n 增加 key。

i18n（en + zh 都加/改）：
  navGroupOverview="Overview/概览"  navGroupResearch="Research/研究"
  navGroupAnalyze="Analyze & Model/分析与建模"  navGroupArchive="Archive/资料"
  navDashboard="Dashboard/仪表盘"  navResearchWorkspace→"Investment Ideas/投资想法"
  navCurrentResearch→"Current Study/当前研究"  navMarketWatch→"AI Watchlist/AI 关注列表"
  navStrategyLab→"Strategy Studio/策略工作室"  navComparison→"Compare Models/模型对比"
  navRiskReview="Risk Review/风险评估"  navPaperTrading→"Paper Trading/模拟盘"
  navDataCenter→"Data/数据"  navExperiments→"Saved Runs/已存运行"
  删除或停用 navGroupSecondary（"更多工具"/"More tools"）。

npx tsc --noEmit && npm test && npm run build 全绿。
```

---

## Prompt NAV-2 —（品牌）把 "AI Quant Research" 换成新定位

```
在 frontend/lib/i18n.ts 改品牌显示串（en+zh，仅改值不改 key）：
  appTitle:      "AI Quant Research Workspace" → "AI Investment Intelligence Platform"
                 （zh: "AI 量化研究" → "AI 投资智能平台"）
  appTitleShort: "AI Quant Research" → "Investment Intelligence"（zh: "AI 投资智能"）
这些串被 components/layout/AppShell.tsx 与 PageHero.tsx 使用，会自动更新侧栏顶部与首页大标题。
全仓再搜一遍用户可见的 "Quant" / "量化研究" 残留，按新定位改（注释/变量名不动）。
npx tsc --noEmit && npm test 全绿。
```

---

## Prompt NAV-3 —（外壳视觉强化 + 响应式）

```
强化 frontend/components/layout/ 的外壳观感与响应式，不改业务逻辑：

1) 侧栏分区层次：分区小标题用更弱的字重/字号与字距（uppercase、letter-spacing、
   text-slate-400 一类），链接项加 hover / active 背景与左侧高亮条，图标可选（lucide-react）。
   当前页链接 active 态要明显。
2) 顶部品牌区：AppShell 顶部显示品牌名 + 版本，做成可点击回 Dashboard。
3) 响应式：窄屏（<768px）侧栏收成汉堡抽屉（TopNav 里放开关），点击遮罩关闭；
   桌面维持固定侧栏。用纯 CSS/状态即可，别引新库。
4) 语言切换与 DemoBanner 保留；DemoBanner（"作品集演示 · 仅供研究 · 非投资建议…"）
   移到底部或顶部条,样式收敛为一行细提示，别占大块。
5) 整体留白/圆角/分隔线统一，去掉突兀的灰块。

npx tsc --noEmit && npm test && npm run build 全绿；本地 npm run dev 桌面与窄屏各看一遍。
```

---

## 顺带：这次要不要连"研究学习"术语一起清掉
你截图里"研究/研究库/当前研究"这类学术词还在。NAV-1 已把侧栏标签换成投资产品用语；
更深一层的页面内文案（研究问题/假设/验证/评估…）在
`V2_PHASE1_RENAME_PROMPTS.md` 的 P1-B 里，建议本轮一并执行，风格才统一。

## 验收（照着点一遍）
- 打开首屏：侧栏直接看到 Dashboard / Investment Ideas / AI Watchlist / Strategy Studio /
  Compare Models / Risk Review / Paper Trading，**不用展开任何"更多工具"**。
- 品牌显示 "AI Investment Intelligence"，不再是 "AI Quant Research"。
- 窄屏下侧栏变抽屉，不挤压内容。

## 别过度
- 不引入重型 UI 框架/主题库；沿用现有 CSS 与 lucide-react。
- 一次只重构"外壳与导航"，功能页逻辑不动，靠现有测试兜底。
