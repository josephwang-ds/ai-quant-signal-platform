# AI Quant Research Workspace — Style Guide

> **Status:** Product design standard · **Last reviewed:** 2026-07-13

The interface should feel like a calm, precise research instrument. It prioritizes evidence, lifecycle, and review over spectacle, trading urgency, or generic dashboard density.

## UI principles

1. **Workspace before pages.** Preserve Strategy and Research context across tasks.
2. **Evidence before narrative.** Put metrics, provenance, and confidence before AI interpretation.
3. **State before action.** Show lifecycle status, blocking conditions, ownership, and next valid action.
4. **Progressive depth.** Begin with decision-relevant summaries and allow inspection of method and source.
5. **Calm risk communication.** Avoid casino, brokerage, and alarmist visual language.
6. **Accessible by construction.** Use semantic structure, keyboard support, focus states, and redundant status cues.
7. **Bilingual resilience.** Layouts must tolerate English and Simplified Chinese without truncating meaning.

## Workspace-first design

A workspace view should answer:

- Which Strategy or Research program am I in?
- What lifecycle state is authoritative?
- Who owns the next action?
- What evidence supports or blocks progress?
- How confident is the data?
- What changed, and what decision follows?

Use persistent context, task-oriented sections, and linked artifacts. Avoid isolated metric galleries or navigation organized only by implementation features.

## Typography

The current type system is canonical:

- **IBM Plex Sans** for interface text.
- **IBM Plex Mono** for numbers, identifiers, parameters, timestamps, and compact research metadata.
- System CJK fallbacks: PingFang SC, Hiragino Sans GB, and Microsoft YaHei.

Use tabular numerals for aligned quantitative values. Headings should be concise and sentence case. Prefer weight and spacing over excessive size. Do not use monospace as decoration.

| Role | Guidance |
|---|---|
| Workspace title | clear identity, restrained scale, one per context |
| Section title | describes a research task or evidence group |
| Body | readable at `1rem`, approximately `1.6` line height |
| Supporting text | no smaller than the established `0.875rem` token for meaningful content |
| Quantitative value | monospace, tabular, unit shown or inferable from column heading |

## Color philosophy

The palette uses warm neutral surfaces with restrained teal emphasis. Orange communicates caution or adverse direction. Color is semantic, never ornamental or the sole carrier of meaning.

| Token | Current value | Use |
|---|---:|---|
| Page | `#f5f5f0` | primary canvas |
| Card | `#ffffff` | evidence and task surfaces |
| Primary text | `#1a1a1a` | titles and core content |
| Secondary text | `#3d3d3d` | supporting explanation |
| Muted text | `#6b6b6b` | metadata; maintain contrast |
| Accent / positive | `#0d6e6e` | primary action, selected state, positive status |
| Caution / negative | `#b45309` | warnings, adverse direction, blocking attention |

Do not introduce finance-default red/green semantics without labels. Risk levels require a textual level and reason. Generated chart series must remain distinguishable in grayscale and common color-vision deficiencies.

## Spacing and layout

Use a 4px base rhythm, expressed through the existing CSS tokens and rem values. Favor breathing room between research sections and tighter spacing inside related evidence groups.

- Page gutters: at least 16px on compact screens; increase with viewport.
- Card padding: 16–24px depending on density.
- Control height: consistent within a toolbar.
- Section gap: use the existing `--space-section` token.
- Content width: respect `--container`; data-heavy views may use available width intentionally.
- Alignment: numeric columns right-align; labels and narrative left-align.

Responsive layouts must preserve reading and action order. Horizontal scrolling is acceptable for genuinely tabular evidence when columns cannot be meaningfully stacked.

## Naming and copy

- Use domain language: Strategy, Research, Experiment, Validation, Evidence, Review, Decision, Monitoring.
- Name actions as verbs: “Run validation,” “Request review,” “Reopen research.”
- Avoid vague labels such as “Process,” “Submit,” or “AI result.”
- Distinguish “Not run,” “Running,” “Failed,” “Blocked,” and “No data.”
- State why an action is unavailable and what evidence or authority is required.
- Label generated content “AI interpretation” and identify its evidence scope.
- Avoid claims such as “safe,” “guaranteed,” or “best strategy.”

## Icons

Use one consistent icon family when introduced. Icons support labels; they do not replace unfamiliar concepts. Match stroke weight and optical size, provide accessible names for icon-only controls, and avoid decorative finance imagery such as rockets, money bags, or flashing market arrows.

Recommended semantic uses:

- lifecycle/status: paired icon + text;
- provenance: source/link symbol;
- review: document/check symbol;
- warning: restrained alert symbol with reason;
- overflow actions: standard ellipsis with accessible label.

## Cards

Cards group one coherent research object or evidence set. They are not default wrappers for every element.

A card should have, when relevant:

1. identity and lifecycle state;
2. purpose or hypothesis;
3. owner and updated time;
4. key evidence with units and confidence;
5. blocking condition or next action; and
6. a clear path to inspect details.

Use borders and subtle elevation from existing tokens. Avoid nested card stacks, oversized shadows, decorative gradients, and hover motion that shifts surrounding layout.

## Data presentation

- Display units, period, benchmark, and observation window.
- Separate actual, benchmark, estimate, and scenario values.
- Show missing or stale data explicitly.
- Include source and confidence near decision-relevant metrics.
- Use appropriate precision; more decimals do not imply more certainty.
- Preserve raw evidence access behind summaries.
- Charts require titles, axes, units, legends, and a written takeaway that does not overstate causality.

## States and feedback

Every asynchronous surface must define loading, empty, stale, error, partial, and success behavior. Avoid blank containers and indefinite spinners. Destructive or lifecycle-changing actions require explicit consequences and, when appropriate, confirmation.

## Accessibility baseline

- Meet WCAG AA contrast for text and controls.
- Provide visible keyboard focus and logical tab order.
- Use native elements before custom interaction patterns.
- Associate form labels, descriptions, and errors programmatically.
- Do not encode meaning through color, position, or hover alone.
- Respect reduced-motion preferences.
- Test zoom, narrow layouts, long English text, and Chinese text.

## Design review checklist

- [ ] Strategy/Research context and authoritative lifecycle state are visible.
- [ ] Evidence, source, confidence, and AI interpretation are distinguishable.
- [ ] The primary action is valid for the current state and actor.
- [ ] Loading, empty, stale, failed, blocked, and success states are defined.
- [ ] Typography, color, spacing, icons, and cards reuse established patterns.
- [ ] Keyboard, focus, contrast, responsive, and bilingual behavior were checked.
- [ ] The experience resembles a research workspace, not a trading terminal.
