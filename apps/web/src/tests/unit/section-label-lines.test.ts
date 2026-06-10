import { describe, expect, it } from "vitest";
import {
  isCountableLine,
  isSectionLabelLine,
  sectionLabelOf,
} from "@/features/structure/section-label-lines";

describe("sectionLabelOf", () => {
  it("extracts simple labels", () => {
    expect(sectionLabelOf("[Chorus]")).toBe("Chorus");
    expect(sectionLabelOf("[verse]")).toBe("verse");
  });

  it("tolerates surrounding and inner whitespace", () => {
    expect(sectionLabelOf("  [ Pre-Chorus ]  ")).toBe("Pre-Chorus");
  });

  it("accepts Spanish and custom labels", () => {
    expect(sectionLabelOf("[Coro]")).toBe("Coro");
    expect(sectionLabelOf("[Puente]")).toBe("Puente");
    expect(sectionLabelOf("[Drop 2]")).toBe("Drop 2");
  });

  it("rejects lines with text outside the brackets", () => {
    expect(sectionLabelOf("hey [name] of mine")).toBeNull();
    expect(sectionLabelOf("[Chorus] again")).toBeNull();
  });

  it("rejects letterless bracket lines", () => {
    expect(sectionLabelOf("[2]")).toBeNull();
    expect(sectionLabelOf("[...]")).toBeNull();
  });

  it("rejects nested or empty brackets", () => {
    expect(sectionLabelOf("[[Chorus]]")).toBeNull();
    expect(sectionLabelOf("[]")).toBeNull();
  });
});

describe("isSectionLabelLine", () => {
  it("matches label lines only", () => {
    expect(isSectionLabelLine("[Bridge]")).toBe(true);
    expect(isSectionLabelLine("just lyrics")).toBe(false);
    expect(isSectionLabelLine("")).toBe(false);
  });
});

describe("isCountableLine", () => {
  it("counts lyric lines but not blanks or labels", () => {
    expect(isCountableLine("Counting down the days,")).toBe(true);
    expect(isCountableLine("")).toBe(false);
    expect(isCountableLine("   ")).toBe(false);
    expect(isCountableLine("[Chorus]")).toBe(false);
  });
});
