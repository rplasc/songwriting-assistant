import { describe, expect, it } from "vitest";
import { detectStanzas } from "@/features/structure/stanza-detector";

describe("detectStanzas", () => {
  it("returns no ranges for empty content", () => {
    expect(detectStanzas("")).toEqual([]);
    expect(detectStanzas("   \n  \n")).toEqual([]);
  });

  it("treats the whole content as one stanza when there are no blank lines", () => {
    const text = "line one\nline two\nline three";
    expect(detectStanzas(text)).toEqual([{ lineStart: 1, lineEnd: 3 }]);
  });

  it("splits on blank line separators with 1-indexed inclusive ranges", () => {
    const text = "verse a\nverse b\n\nchorus a\nchorus b\nchorus c";
    expect(detectStanzas(text)).toEqual([
      { lineStart: 1, lineEnd: 2 },
      { lineStart: 4, lineEnd: 6 },
    ]);
  });

  it("collapses multi-blank separators without producing empty stanzas", () => {
    const text = "a\n\n\n\nb";
    expect(detectStanzas(text)).toEqual([
      { lineStart: 1, lineEnd: 1 },
      { lineStart: 5, lineEnd: 5 },
    ]);
  });

  it("ignores leading and trailing blank lines", () => {
    const text = "\n\nverse\n\n";
    expect(detectStanzas(text)).toEqual([{ lineStart: 3, lineEnd: 3 }]);
  });
});
