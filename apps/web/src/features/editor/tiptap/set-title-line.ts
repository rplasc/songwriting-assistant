import type { Editor } from "@tiptap/react";
import { isCountableLine } from "@/features/structure/section-label-lines";

/**
 * The title is derived from the first lyric line (see derive-title.ts), so
 * editing it rewrites that line in place. If there's no lyric line yet
 * (empty draft, or only section labels), a new first line is inserted —
 * unless the new title is itself empty, in which case there's nothing to do.
 */
export function setTitleLine(editor: Editor, title: string): void {
  const text = title.trim();
  let targetPos = -1;
  let targetSize = 0;
  editor.state.doc.forEach((node, offset) => {
    if (targetPos === -1 && isCountableLine(node.textContent)) {
      targetPos = offset;
      targetSize = node.nodeSize;
    }
  });

  const chain = editor.chain().focus();
  if (targetPos !== -1) {
    chain.setTextSelection({ from: targetPos + 1, to: targetPos + targetSize - 1 });
    if (text) chain.insertContent(text);
    else chain.deleteSelection();
  } else if (text) {
    chain.insertContentAt(0, [
      { type: "paragraph", content: [{ type: "text", text }] },
    ]);
  } else {
    return;
  }
  chain.run();
}
