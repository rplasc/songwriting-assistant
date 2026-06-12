import { describe, expect, it } from "vitest";
import { mapSyllablePatternToLines } from "@/features/analysis/map-syllable-pattern";

describe("mapSyllablePatternToLines", () => {
  it("assigns counts to countable lines in order", () => {
    const sourceLines = ["[Verse]", "Counting down the days,", "", "Tangled in my dreams,"];
    const entries = mapSyllablePatternToLines(
      [{ lineStart: 1, lineEnd: 4, syllablePattern: [5, 5] }],
      sourceLines,
    );
    expect(entries).toEqual([
      { line: 2, text: "Counting down the days,", count: 5 },
      { line: 4, text: "Tangled in my dreams,", count: 5 },
    ]);
  });

  it("skips blank lines and label lines without consuming pattern slots", () => {
    const sourceLines = ["one syllable line", "", "[Chorus]", "another line"];
    const entries = mapSyllablePatternToLines(
      [{ lineStart: 1, lineEnd: 4, syllablePattern: [4, 3] }],
      sourceLines,
    );
    expect(entries.map((e) => e.line)).toEqual([1, 4]);
    expect(entries.map((e) => e.count)).toEqual([4, 3]);
  });

  it("drops a section whose pattern is shorter than its countable lines", () => {
    const entries = mapSyllablePatternToLines(
      [{ lineStart: 1, lineEnd: 3, syllablePattern: [4] }],
      ["line a", "line b", "line c"],
    );
    expect(entries).toEqual([]);
  });

  it("drops a section whose pattern is longer than its countable lines", () => {
    const entries = mapSyllablePatternToLines(
      [{ lineStart: 1, lineEnd: 1, syllablePattern: [4, 6] }],
      ["only line"],
    );
    expect(entries).toEqual([]);
  });

  it("drops a section whose range runs past the content", () => {
    const entries = mapSyllablePatternToLines(
      [{ lineStart: 1, lineEnd: 5, syllablePattern: [4, 6] }],
      ["only line"],
    );
    expect(entries).toEqual([]);
  });

  it("keeps healthy sections when a sibling section mismatches", () => {
    const entries = mapSyllablePatternToLines(
      [
        { lineStart: 1, lineEnd: 1, syllablePattern: [7] },
        { lineStart: 2, lineEnd: 2, syllablePattern: [1, 2] },
      ],
      ["healthy line", "raced line"],
    );
    expect(entries).toEqual([{ line: 1, text: "healthy line", count: 7 }]);
  });

  it("trims text used as the cache key", () => {
    const entries = mapSyllablePatternToLines(
      [{ lineStart: 1, lineEnd: 1, syllablePattern: [3] }],
      ["  indented line  "],
    );
    expect(entries[0].text).toBe("indented line");
  });
});
