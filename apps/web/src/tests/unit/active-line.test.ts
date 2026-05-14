import { describe, expect, it } from "vitest";
import { extractActiveLine } from "@/features/analysis/active-line";

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
