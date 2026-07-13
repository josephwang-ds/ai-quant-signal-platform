/**
 * Notebook 轻量 Markdown 呈现（无额外依赖）。
 * 支持：段落、## 标题、**粗体**、- 列表、`code`。
 */

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inlineFormat(text: string): string {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

/**
 * 将受限 Markdown 子集渲染为 HTML 字符串（供 dangerouslySetInnerHTML 使用）。
 */
export function renderNotebookMarkdown(body: string): string {
  const lines = body.split("\n");
  const parts: string[] = [];
  let listOpen = false;

  function closeList() {
    if (listOpen) {
      parts.push("</ul>");
      listOpen = false;
    }
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();

    if (line.trim() === "") {
      closeList();
      continue;
    }

    if (line.startsWith("## ")) {
      closeList();
      parts.push(`<h4 class="notebook-markdown__h">${inlineFormat(line.slice(3))}</h4>`);
      continue;
    }

    if (line.startsWith("- ")) {
      if (!listOpen) {
        parts.push('<ul class="notebook-markdown__list">');
        listOpen = true;
      }
      parts.push(`<li>${inlineFormat(line.slice(2))}</li>`);
      continue;
    }

    closeList();
    parts.push(`<p class="notebook-markdown__p">${inlineFormat(line)}</p>`);
  }

  closeList();
  return parts.join("");
}
