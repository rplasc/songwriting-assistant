import type { Node as PMNode } from "@tiptap/pm/model";
import type { EditorState } from "@tiptap/pm/state";

/**
 * One top-level paragraph viewed as a lyric line. `line` is 1-based and
 * matches the analysis services' line numbering (see editor-lines.ts).
 * `pos` is the ProseMirror position before the paragraph node; its text
 * content starts at `pos + 1`.
 */
export interface LineDescriptor {
  line: number;
  pos: number;
  nodeSize: number;
  text: string;
}

export function describeLines(doc: PMNode): LineDescriptor[] {
  const out: LineDescriptor[] = [];
  let line = 0;
  doc.forEach((node, offset) => {
    line += 1;
    out.push({ line, pos: offset, nodeSize: node.nodeSize, text: node.textContent });
  });
  return out;
}

/** 1-based line number of the paragraph holding the selection head. */
export function lineAtSelection(state: EditorState): number {
  return state.selection.$head.index(0) + 1;
}
