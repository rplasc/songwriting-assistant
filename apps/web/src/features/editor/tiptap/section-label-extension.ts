import { Extension } from "@tiptap/core";
import type { Node as PMNode } from "@tiptap/pm/model";
import { Plugin, PluginKey } from "@tiptap/pm/state";
import { Decoration, DecorationSet } from "@tiptap/pm/view";
import { isSectionLabelLine } from "@/features/structure/section-label-lines";
import { describeLines, type LineDescriptor } from "./line-descriptors";

export const sectionLabelKey = new PluginKey<DecorationSet>("sectionLabels");

/**
 * Purely presentational: a `[Chorus]` paragraph keeps its plain text (the
 * backend parses it into a section) but renders as a small-caps margin label.
 * Brackets stay in the document and visible-but-dimmed, so the caret can
 * always reach them. Exported for unit tests.
 */
export function buildSectionLabelDecorations(
  doc: PMNode,
  lines: LineDescriptor[],
): DecorationSet {
  const decos: Decoration[] = [];
  for (const line of lines) {
    if (!isSectionLabelLine(line.text)) continue;
    decos.push(
      Decoration.node(line.pos, line.pos + line.nodeSize, {
        class: "line-section-label",
      }),
    );
    const textStart = line.pos + 1;
    const open = line.text.indexOf("[");
    const close = line.text.lastIndexOf("]");
    if (open >= 0) {
      decos.push(
        Decoration.inline(textStart + open, textStart + open + 1, {
          class: "bracket-dim",
        }),
      );
    }
    if (close > open) {
      decos.push(
        Decoration.inline(textStart + close, textStart + close + 1, {
          class: "bracket-dim",
        }),
      );
    }
  }
  return DecorationSet.create(doc, decos);
}

export const SectionLabels = Extension.create({
  name: "sectionLabels",

  addProseMirrorPlugins() {
    return [
      new Plugin<DecorationSet>({
        key: sectionLabelKey,
        state: {
          init: (_config, state) =>
            buildSectionLabelDecorations(state.doc, describeLines(state.doc)),
          apply(tr, prev, _oldState, newState) {
            if (!tr.docChanged) return prev;
            return buildSectionLabelDecorations(
              newState.doc,
              describeLines(newState.doc),
            );
          },
        },
        props: {
          decorations(state) {
            return sectionLabelKey.getState(state);
          },
        },
      }),
    ];
  },
});
