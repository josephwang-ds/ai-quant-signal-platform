# Research Library (PR-027)

## Purpose

The Research Library is the **workspace homepage** for research projects.

It is **not**:

- a file explorer
- a KPI / stock dashboard
- a place to invent research projects, activity logs, or percentages

## Inputs

- Existing research from `ResearchRepository` (demo catalog + local user research)
- Timeline events from the catalog when present for the continue target

No backend list API is added in this slice.

## Sections

1. **Continue Research** — most recent by `updatedAt`, or empty state
2. **Research Projects** — real cards only (title, strategy, stage, status)
3. **Research Lifecycle** — product spine; highlight completed stages for the continue target
4. **Recent Activity** — reuse timeline when available; otherwise “No recent activity.”
5. **Quick Actions** — navigation links (and New Research opens the existing local create modal)

## Empty state

“No research yet. Create or import a research project to begin.”

Load Demo remains an import path for the canonical Trend Following Study — not a fabricated second project.

## Surfaces

- `/` (AppShell Research Library entry)
- Nav label: Research Library

## Authenticity

No KPI cards, donut charts, fake percentages, or dummy projects.
