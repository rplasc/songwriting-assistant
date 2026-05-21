import type { Editor } from "@tiptap/react";

/**
 * Scroll and place the cursor at the start of the Nth line (1-indexed),
 * where each paragraph counts as one line — matching the gateway's
 * line numbering and the stanza detector.
 */
export function jumpToLine(editor: Editor, line: number): void {
  if (!editor || line < 1) return;
  let count = 0;
  let targetPos: number | null = null;
  editor.state.doc.forEach((node, offset) => {
    count += 1;
    if (count === line && targetPos === null) {
      // +1 to land inside the paragraph, after its opening token.
      targetPos = offset + 1;
    }
  });
  if (targetPos === null) return;
  editor
    .chain()
    .focus()
    .setTextSelection(targetPos)
    .scrollIntoView()
    .run();
}
