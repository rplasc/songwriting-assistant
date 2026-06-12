import { Extension } from "@tiptap/core";
import type { Editor } from "@tiptap/react";
import { Plugin, PluginKey } from "@tiptap/pm/state";
import { Decoration, DecorationSet } from "@tiptap/pm/view";
import type { InnerRhymeGroup } from "@/features/analysis/analysis-types";
import { describeLines, type LineDescriptor } from "./line-descriptors";

export const RHYME_GROUP_CLASS_COUNT = 8;

export interface InnerRhymePayload {
  groups: InnerRhymeGroup[];
  /** The analyzed draft content split on \n — occurrence offsets are only
   * valid against these lines, so each one is checked before decorating. */
  sourceLines: string[];
}

export interface RhymeUnderlineRange {
  from: number;
  to: number;
  className: string;
}

export const innerRhymeKey = new PluginKey<DecorationSet>("innerRhymes");

/**
 * Map analysis occurrences (1-based line index, char offsets into the
 * STRIPPED line text) to ProseMirror ranges. An occurrence is skipped when
 * its line has changed since analysis or its offsets no longer land on the
 * expected word — stale underlines are worse than missing ones.
 * Exported for unit tests.
 */
export function computeInnerRhymeRanges(
  lines: LineDescriptor[],
  payload: InnerRhymePayload,
): RhymeUnderlineRange[] {
  const byLine = new Map(lines.map((l) => [l.line, l]));
  const ranges: RhymeUnderlineRange[] = [];
  payload.groups.forEach((group, groupIndex) => {
    const className = `rhyme-g${groupIndex % RHYME_GROUP_CLASS_COUNT}`;
    for (const occ of group.occurrences) {
      const descriptor = byLine.get(occ.lineIndex);
      const source = payload.sourceLines[occ.lineIndex - 1];
      if (!descriptor || source === undefined) continue;
      if (descriptor.text.trim() !== source.trim()) continue;
      const lead = descriptor.text.length - descriptor.text.trimStart().length;
      const start = lead + occ.charStart;
      const end = lead + occ.charEnd;
      if (descriptor.text.slice(start, end) !== occ.text) continue;
      ranges.push({
        from: descriptor.pos + 1 + start,
        to: descriptor.pos + 1 + end,
        className,
      });
    }
  });
  return ranges;
}

/**
 * Edited ranges in post-transaction coordinates. Decorations overlapping any
 * of them are dropped: their underlying words may have changed, and the next
 * analysis will re-decorate. Exported for unit tests.
 */
export function collectDirtyRanges(mapping: {
  maps: readonly {
    forEach: (
      f: (
        oldStart: number,
        oldEnd: number,
        newStart: number,
        newEnd: number,
      ) => void,
    ) => void;
  }[];
}): [number, number][] {
  const dirty: [number, number][] = [];
  mapping.maps.forEach((stepMap) => {
    stepMap.forEach((_oldStart, _oldEnd, newStart, newEnd) => {
      dirty.push([newStart, newEnd]);
    });
  });
  return dirty;
}

export function overlapsDirty(
  range: { from: number; to: number },
  dirty: [number, number][],
): boolean {
  return dirty.some(([f, t]) => range.from <= t && range.to >= f);
}

/** Push fresh analysis results into the editor's underline decorations. */
export function setInnerRhymes(editor: Editor, payload: InnerRhymePayload): void {
  editor.view.dispatch(editor.state.tr.setMeta(innerRhymeKey, payload));
}

export const InnerRhymes = Extension.create({
  name: "innerRhymes",

  addProseMirrorPlugins() {
    return [
      new Plugin<DecorationSet>({
        key: innerRhymeKey,
        state: {
          init: () => DecorationSet.empty,
          apply(tr, prev, _oldState, newState) {
            const meta = tr.getMeta(innerRhymeKey) as
              | InnerRhymePayload
              | undefined;
            if (meta) {
              const ranges = computeInnerRhymeRanges(
                describeLines(newState.doc),
                meta,
              );
              return DecorationSet.create(
                newState.doc,
                ranges.map((r) =>
                  Decoration.inline(r.from, r.to, { class: r.className }),
                ),
              );
            }
            if (!tr.docChanged) return prev;
            const mapped = prev.map(tr.mapping, tr.doc);
            const dirty = collectDirtyRanges(tr.mapping);
            if (dirty.length === 0) return mapped;
            const survivors = mapped
              .find()
              .filter((d) => !overlapsDirty(d, dirty));
            return DecorationSet.create(tr.doc, survivors);
          },
        },
        props: {
          decorations(state) {
            return innerRhymeKey.getState(state);
          },
        },
      }),
    ];
  },
});
