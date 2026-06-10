import type { Editor } from "@tiptap/react";

/**
 * Insert a `[Label]` paragraph after the caret's current line and put the
 * caret on a fresh line below it, ready for lyrics. Typing the brackets by
 * hand works just as well — this is the click path.
 */
export function insertSectionLabel(editor: Editor, label: string): void {
  const { $head } = editor.state.selection;
  const afterCurrentLine = $head.after(1);
  editor
    .chain()
    .focus()
    .insertContentAt(afterCurrentLine, [
      { type: "paragraph", content: [{ type: "text", text: `[${label}]` }] },
      { type: "paragraph" },
    ])
    .run();
}
