import { describe, expect, it } from "vitest";
import { Schema, type Node as PMNode } from "@tiptap/pm/model";
import { buildLineMetricsDecorations } from "@/features/editor/tiptap/line-metrics-extension";
import { buildSectionLabelDecorations } from "@/features/editor/tiptap/section-label-extension";
import {
  collectDirtyRanges,
  computeInnerRhymeRanges,
  overlapsDirty,
  rhymeColorSlot,
  RHYME_GROUP_CLASS_COUNT,
} from "@/features/editor/tiptap/inner-rhyme-extension";
import {
  describeLines,
  type LineDescriptor,
} from "@/features/editor/tiptap/line-descriptors";

const schema = new Schema({
  nodes: {
    doc: { content: "paragraph+" },
    paragraph: { content: "text*" },
    text: {},
  },
});

function makeDoc(lines: string[]): PMNode {
  return schema.node(
    "doc",
    null,
    lines.map((text) =>
      text.length > 0
        ? schema.node("paragraph", null, [schema.text(text)])
        : schema.node("paragraph"),
    ),
  );
}

describe("describeLines", () => {
  it("walks paragraphs with 1-based lines and absolute positions", () => {
    const doc = makeDoc(["abc", "", "de"]);
    const lines = describeLines(doc);
    expect(lines).toEqual([
      { line: 1, pos: 0, nodeSize: 5, text: "abc" },
      { line: 2, pos: 5, nodeSize: 2, text: "" },
      { line: 3, pos: 7, nodeSize: 4, text: "de" },
    ]);
  });
});

describe("buildLineMetricsDecorations", () => {
  it("adds counts to known lines and skips blanks and labels", () => {
    const doc = makeDoc(["[Verse]", "Counting down the days,", ""]);
    const lines = describeLines(doc);
    const counts = new Map([["Counting down the days,", 5]]);
    const set = buildLineMetricsDecorations(doc, lines, counts, 99);
    const found = set.find();
    expect(found).toHaveLength(1);
    expect(found[0].from).toBe(lines[1].pos);
    expect(found[0].spec).toBeDefined();
  });

  it("marks the active line even without a cached count", () => {
    const doc = makeDoc(["fresh words"]);
    const lines = describeLines(doc);
    const set = buildLineMetricsDecorations(doc, lines, new Map(), 1);
    expect(set.find()).toHaveLength(1);
  });

  it("does not mark a section label as active", () => {
    const doc = makeDoc(["[Chorus]"]);
    const lines = describeLines(doc);
    const set = buildLineMetricsDecorations(doc, lines, new Map(), 1);
    expect(set.find()).toHaveLength(0);
  });
});

describe("buildSectionLabelDecorations", () => {
  it("decorates label lines and dims both brackets", () => {
    const doc = makeDoc(["[Chorus]", "lyric line"]);
    const lines = describeLines(doc);
    const set = buildSectionLabelDecorations(doc, lines);
    const found = set.find();
    // 1 node decoration + 2 bracket inline decorations
    expect(found).toHaveLength(3);
    const inline = found.filter((d) => d.from !== lines[0].pos);
    // "[" at text offset 0 → pos 1..2; "]" at offset 7 → pos 8..9
    expect(inline.map((d) => [d.from, d.to])).toEqual(
      expect.arrayContaining([
        [1, 2],
        [8, 9],
      ]),
    );
  });

  it("ignores lyric lines", () => {
    const doc = makeDoc(["no labels here"]);
    const set = buildSectionLabelDecorations(doc, describeLines(doc));
    expect(set.find()).toHaveLength(0);
  });
});

function descriptorsFor(lines: string[]): LineDescriptor[] {
  return describeLines(makeDoc(lines));
}

describe("computeInnerRhymeRanges", () => {
  const group = (occurrences: {
    lineIndex: number;
    charStart: number;
    charEnd: number;
    text: string;
  }[]) => ({
    id: "g1",
    rhymeType: "perfect" as const,
    confidence: "high" as const,
    rhymeKey: "EY",
    occurrences: occurrences.map((o, i) => ({
      ...o,
      wordIndex: i,
      normalized: o.text.toLowerCase(),
    })),
  });

  it("maps stripped-text offsets to document positions", () => {
    const source = ["Counting down the days,"];
    const ranges = computeInnerRhymeRanges(descriptorsFor(source), {
      groups: [group([{ lineIndex: 1, charStart: 18, charEnd: 22, text: "days" }])],
      sourceLines: source,
    });
    // paragraph text starts at pos 1
    expect(ranges).toEqual([
      { from: 19, to: 23, className: `rhyme-g${rhymeColorSlot("EY")}` },
    ]);
  });

  it("re-adds leading whitespace present in the editor line", () => {
    const editorLines = ["  Counting down the days,"];
    const ranges = computeInnerRhymeRanges(descriptorsFor(editorLines), {
      groups: [group([{ lineIndex: 1, charStart: 18, charEnd: 22, text: "days" }])],
      sourceLines: ["Counting down the days,"],
    });
    expect(ranges).toEqual([
      { from: 21, to: 25, className: `rhyme-g${rhymeColorSlot("EY")}` },
    ]);
  });

  it("skips occurrences whose line changed since analysis", () => {
    const ranges = computeInnerRhymeRanges(descriptorsFor(["edited line now"]), {
      groups: [group([{ lineIndex: 1, charStart: 0, charEnd: 6, text: "stable" }])],
      sourceLines: ["stable line here"],
    });
    expect(ranges).toEqual([]);
  });

  it("skips occurrences whose offsets no longer match the word", () => {
    const source = ["same length lineX"];
    const ranges = computeInnerRhymeRanges(descriptorsFor(source), {
      groups: [group([{ lineIndex: 1, charStart: 0, charEnd: 4, text: "diff" }])],
      sourceLines: source,
    });
    expect(ranges).toEqual([]);
  });

  it("assigns a class from the rhyme key, stable across group order", () => {
    const source = ["aa bb"];
    const occ = (word: string, i: number) => ({
      id: `g${i}`,
      rhymeType: "perfect" as const,
      confidence: "high" as const,
      rhymeKey: `KEY_${word}`,
      occurrences: [
        {
          lineIndex: 1,
          wordIndex: i,
          charStart: i * 3,
          charEnd: i * 3 + 2,
          text: word,
          normalized: word,
        },
      ],
    });
    const forward = computeInnerRhymeRanges(descriptorsFor(source), {
      groups: [occ("aa", 0), occ("bb", 1)],
      sourceLines: source,
    });
    // Same key -> same class regardless of position in the group list.
    expect(forward[0].className).toBe(`rhyme-g${rhymeColorSlot("KEY_aa")}`);
    expect(forward[1].className).toBe(`rhyme-g${rhymeColorSlot("KEY_bb")}`);
    // Reordering the words on the line must not change either word's color.
    const swappedSource = ["bb aa"];
    const swapped = computeInnerRhymeRanges(descriptorsFor(swappedSource), {
      groups: [occ("bb", 0), occ("aa", 1)],
      sourceLines: swappedSource,
    });
    expect(swapped[0].className).toBe(`rhyme-g${rhymeColorSlot("KEY_bb")}`);
    expect(swapped[1].className).toBe(`rhyme-g${rhymeColorSlot("KEY_aa")}`);
  });
});

describe("rhymeColorSlot", () => {
  it("is deterministic and within the palette range", () => {
    for (const key of ["EY", "AO1_R", "IY1_T", "AH0_L", "", "UW1"]) {
      const slot = rhymeColorSlot(key);
      expect(slot).toBe(rhymeColorSlot(key));
      expect(slot).toBeGreaterThanOrEqual(0);
      expect(slot).toBeLessThan(RHYME_GROUP_CLASS_COUNT);
      expect(Number.isInteger(slot)).toBe(true);
    }
  });
});

describe("dirty-range pruning", () => {
  it("collects post-step ranges from a mapping", () => {
    const fakeMapping = {
      maps: [
        {
          forEach(f: (a: number, b: number, c: number, d: number) => void) {
            f(4, 6, 4, 9);
          },
        },
      ],
    };
    expect(collectDirtyRanges(fakeMapping)).toEqual([[4, 9]]);
  });

  it("drops decorations overlapping dirty ranges and keeps the rest", () => {
    const dirty: [number, number][] = [[10, 14]];
    expect(overlapsDirty({ from: 12, to: 13 }, dirty)).toBe(true);
    expect(overlapsDirty({ from: 8, to: 11 }, dirty)).toBe(true);
    expect(overlapsDirty({ from: 1, to: 5 }, dirty)).toBe(false);
    expect(overlapsDirty({ from: 15, to: 20 }, dirty)).toBe(false);
  });
});
