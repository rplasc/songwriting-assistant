import type { Editor } from "@tiptap/react";

/**
 * Read each TipTap paragraph as a line string (empty string for blank paragraphs).
 * Index 0 → line 1 (1-indexed externally). Matches jump-to-line's paragraph-counting contract.
 */
export function getEditorLines(editor: Editor): string[] {
  const lines: string[] = [];
  editor.state.doc.forEach((node) => {
    lines.push(node.textContent);
  });
  return lines;
}

/**
 * Canonical plain-text representation of editor content.
 * Each paragraph is one line; blank paragraphs produce empty lines.
 * Line N (1-indexed) = TipTap paragraph N. Use this instead of editor.getText().
 */
export function getEditorText(editor: Editor): string {
  return getEditorLines(editor).join("\n");
}
