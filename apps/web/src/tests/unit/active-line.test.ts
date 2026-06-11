import { describe, expect, it } from "vitest";
import {
  extractActiveLine,
  extractWordAt,
} from "@/features/analysis/active-line";

describe("extractActiveLine", () => {
  it("returns empty string for empty text", () => {
    expect(extractActiveLine("", 0)).toBe("");
  });

  it("returns the single line when there are no newlines", () => {
    expect(extractActiveLine("hello world", 5)).toBe("hello world");
  });

  it("returns the first line when caret is at start", () => {
    const text = "first line\nsecond line";
    expect(extractActiveLine(text, 0)).toBe("first line");
  });

  it("returns the second line when caret is in it", () => {
    const text = "first line\nsecond line";
    expect(extractActiveLine(text, 12)).toBe("second line");
  });

  it("returns the last line when caret is at end and text ends without newline", () => {
    const text = "line one\nline two";
    expect(extractActiveLine(text, text.length)).toBe("line two");
  });

  it("returns empty string for a blank line", () => {
    const text = "line one\n\nline three";
    expect(extractActiveLine(text, 9)).toBe("");
  });

  it("trims whitespace from the extracted line", () => {
    const text = "  padded line  ";
    expect(extractActiveLine(text, 7)).toBe("padded line");
  });

  it("clamps caret beyond text length to end of text", () => {
    const text = "short";
    expect(extractActiveLine(text, 999)).toBe("short");
  });

  it("handles caret at a newline boundary (sits on the newline character itself)", () => {
    const text = "line a\nline b";
    // caret = 6 is the position OF the newline — should return "line a"
    expect(extractActiveLine(text, 6)).toBe("line a");
  });
});

describe("extractWordAt", () => {
  it("returns null for empty text", () => {
    expect(extractWordAt("", 0)).toBeNull();
  });

  it("returns the word the caret is inside", () => {
    //        0123456789
    expect(extractWordAt("burn bright tonight", 6)).toBe("bright");
  });

  it("returns the word just typed (caret at its right edge)", () => {
    expect(extractWordAt("burn bright", 4)).toBe("burn");
  });

  it("returns the word when the caret is at its left edge", () => {
    expect(extractWordAt("burn bright", 5)).toBe("bright");
  });

  it("falls back to the word on the left when the caret floats in whitespace", () => {
    expect(extractWordAt("burn   bright", 6)).toBe("burn");
  });

  it("returns the upcoming word when nothing is to the left", () => {
    expect(extractWordAt("   bright", 1)).toBe("bright");
  });

  it("strips punctuation from the caret word", () => {
    // caret inside "fire," — the comma is not part of the word
    expect(extractWordAt("catch fire, tonight", 8)).toBe("fire");
  });

  it("keeps apostrophes and hyphens inside words", () => {
    expect(extractWordAt("it don't matter", 5)).toBe("don't");
    expect(extractWordAt("half-light falls", 4)).toBe("half-light");
  });

  it("handles accented words", () => {
    expect(extractWordAt("mi corazón late", 7)).toBe("corazón");
  });

  it("clamps a caret beyond the text", () => {
    expect(extractWordAt("hello", 99)).toBe("hello");
  });
});
