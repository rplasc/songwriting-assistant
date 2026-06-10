import { Extension } from "@tiptap/core";
import type { Editor } from "@tiptap/react";
import type { Node as PMNode } from "@tiptap/pm/model";
import { Plugin, PluginKey } from "@tiptap/pm/state";
import { Decoration, DecorationSet } from "@tiptap/pm/view";
import { isSectionLabelLine } from "@/features/structure/section-label-lines";
import {
  describeLines,
  lineAtSelection,
  type LineDescriptor,
} from "./line-descriptors";

/** Trimmed line text → syllable count. Text-keyed so counts survive line
 * reordering and never land on the wrong line after edits. */
export type LineSyllableCounts = ReadonlyMap<string, number>;

interface LineMetricsState {
  counts: LineSyllableCounts;
  decorations: DecorationSet;
}

export const lineMetricsKey = new PluginKey<LineMetricsState>("lineMetrics");

/**
 * Node decorations only add attributes to the existing <p>, so the count is
 * rendered by CSS (::after) without inserting DOM into contenteditable.
 * Exported for unit tests.
 */
export function buildLineMetricsDecorations(
  doc: PMNode,
  lines: LineDescriptor[],
  counts: LineSyllableCounts,
  activeLine: number,
): DecorationSet {
  const decos: Decoration[] = [];
  for (const line of lines) {
    const trimmed = line.text.trim();
    if (trimmed.length === 0 || isSectionLabelLine(line.text)) continue;
    const count = counts.get(trimmed);
    const isActive = line.line === activeLine;
    if (count === undefined && !isActive) continue;
    const attrs: Record<string, string> = {};
    if (isActive) attrs.class = "line-active";
    if (count !== undefined) attrs["data-syllables"] = String(count);
    decos.push(Decoration.node(line.pos, line.pos + line.nodeSize, attrs));
  }
  return DecorationSet.create(doc, decos);
}

/** Push a fresh count map into the editor's decoration state. */
export function setLineSyllableCounts(
  editor: Editor,
  counts: LineSyllableCounts,
): void {
  editor.view.dispatch(editor.state.tr.setMeta(lineMetricsKey, { counts }));
}

export const LineMetrics = Extension.create({
  name: "lineMetrics",

  addProseMirrorPlugins() {
    return [
      new Plugin<LineMetricsState>({
        key: lineMetricsKey,
        state: {
          init: (_config, state) => ({
            counts: new Map(),
            decorations: buildLineMetricsDecorations(
              state.doc,
              describeLines(state.doc),
              new Map(),
              lineAtSelection(state),
            ),
          }),
          apply(tr, prev, _oldState, newState) {
            const meta = tr.getMeta(lineMetricsKey) as
              | { counts: LineSyllableCounts }
              | undefined;
            if (!meta && !tr.docChanged && !tr.selectionSet) return prev;
            const counts = meta?.counts ?? prev.counts;
            return {
              counts,
              decorations: buildLineMetricsDecorations(
                newState.doc,
                describeLines(newState.doc),
                counts,
                lineAtSelection(newState),
              ),
            };
          },
        },
        props: {
          decorations(state) {
            return lineMetricsKey.getState(state)?.decorations;
          },
        },
      }),
    ];
  },
});
