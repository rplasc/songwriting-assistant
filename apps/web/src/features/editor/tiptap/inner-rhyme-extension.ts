import { Extension } from "@tiptap/core";
import type { Editor } from "@tiptap/react";
import { Plugin, PluginKey } from "@tiptap/pm/state";
import { Decoration, DecorationSet } from "@tiptap/pm/view";
import type { InnerRhymeGroup } from "@/features/analysis/analysis-types";
import { describeLines, type LineDescriptor } from "./line-descriptors";

export const RHYME_GROUP_CLASS_COUNT = 12;

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
 * Map a rhyme group's phonetic key to one of the RHYME_GROUP_CLASS_COUNT color
 * slots. Hashing the key (rather than the group's position) keeps a given sound
 * the same color regardless of how many groups precede it or how the document is
 * edited — the same sound always reads as the same color. With more distinct
 * co-visible sounds than slots, two sounds can share a color; that's an accepted
 * ceiling, matching a fixed palette. FNV-1a over the key chars, folded into the
 * slot count. Exported for unit tests.
 */
export function rhymeColorSlot(rhymeKey: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < rhymeKey.length; i++) {
    h ^= rhymeKey.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0) % RHYME_GROUP_CLASS_COUNT;
}

/**
 * Assign each distinct rhyme key a color slot, avoiding collisions among the
 * keys visible together. Each key's preferred slot is its hash
 * (rhymeColorSlot); on collision the key probes forward to the next free
 * slot. Keys are processed in sorted order, so the assignment is a pure
 * function of the key SET — reordering groups or words never changes a
 * color, and an edit only shifts keys that were colliding. With more keys
 * than slots, later keys fall back to their preferred slot (a collision —
 * the accepted ceiling of a fixed palette). Exported for unit tests.
 */
export function assignColorSlots(keys: Iterable<string>): Map<string, number> {
  const unique = Array.from(new Set(keys)).sort();
  const slots = new Map<string, number>();
  const used = new Set<number>();
  for (const key of unique) {
    let slot = rhymeColorSlot(key);
    if (used.size < RHYME_GROUP_CLASS_COUNT) {
      while (used.has(slot)) slot = (slot + 1) % RHYME_GROUP_CLASS_COUNT;
    }
    used.add(slot);
    slots.set(key, slot);
  }
  return slots;
}

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
  const slotByKey = assignColorSlots(payload.groups.map((g) => g.rhymeKey));
  const ranges: RhymeUnderlineRange[] = [];
  payload.groups.forEach((group) => {
    // Near/cadence groups render de-emphasized (fainter marker, dashed
    // underline) so the perfect end-rhyme scheme visually dominates.
    const nearModifier = group.rhymeType === "near" ? " rhyme-near" : "";
    const className = `rhyme-g${slotByKey.get(group.rhymeKey)}${nearModifier}`;
    // Adjacent words of the same group merge into one continuous block, so a
    // compound phrase ("countin' this") reads as a single unit, not two
    // stacked pills.
    let prev: { range: RhymeUnderlineRange; descriptor: LineDescriptor } | null =
      null;
    for (const occ of group.occurrences) {
      const descriptor = byLine.get(occ.lineIndex);
      const source = payload.sourceLines[occ.lineIndex - 1];
      if (!descriptor || source === undefined) continue;
      if (descriptor.text.trim() !== source.trim()) continue;
      const lead = descriptor.text.length - descriptor.text.trimStart().length;
      const start = lead + occ.charStart;
      const end = lead + occ.charEnd;
      if (descriptor.text.slice(start, end) !== occ.text) continue;
      const from = descriptor.pos + 1 + start;
      const to = descriptor.pos + 1 + end;
      if (prev && prev.descriptor === descriptor && from >= prev.range.to) {
        const gapStart = prev.range.to - (descriptor.pos + 1);
        const gap = descriptor.text.slice(gapStart, start);
        if (gap.length <= 2 && /^[^\p{L}\p{N}]*$/u.test(gap)) {
          prev.range.to = to;
          continue;
        }
      }
      const range: RhymeUnderlineRange = { from, to, className };
      ranges.push(range);
      prev = { range, descriptor };
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
