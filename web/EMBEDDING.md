# Embedding the showcase

`showcase.html` is one self-contained file — inline CSS, inline SVG, no fonts,
scripts or images fetched from anywhere. It renders identically offline, inside an
iframe, and inside a sandbox, which is what makes it portable.

## Streamlit

```python
import streamlit as st
from pathlib import Path

html = Path("web/showcase.html").read_text()

# Streamlit's theme does not reach into the iframe, so pass it in explicitly.
if st.get_option("theme.base") == "dark":
    html = html.replace('<html lang="en">', '<html lang="en" data-theme="dark">')

st.components.v1.html(html, height=7200, scrolling=True)
```

`height` has to be set by hand: an iframe does not grow to fit its content, and
too small a value silently crops the page rather than scrolling it. 7200 fits the
full page at desktop width; on narrow screens it reflows taller, so
`scrolling=True` matters.

## A personal site

Serve the file and link to it, or embed it:

```html
<iframe src="/projects/filing-triage/showcase.html?theme=dark"
        style="width:100%;height:100vh;border:0" title="Filing Triage"></iframe>
```

`?theme=dark` or `?theme=light` forces the palette; omit it to follow the
visitor's system setting.

To drop the content straight into an existing page instead, take everything
between `<main class="wrap">` and `</main>`, and the `<style>` block with it —
the CSS is namespaced loosely enough to travel, but check it against your own
base styles, since it sets `body` and heading rules.

## What is inside

| | |
|---|---|
| Charts | inline SVG, hover titles, direct value labels |
| Palette | validated for colour-vision deficiency in both light and dark |
| Themes | `prefers-color-scheme`, overridable by `data-theme` or `?theme=` |
| Width | reflows to 390px with no horizontal scroll |
| Requests | none |
