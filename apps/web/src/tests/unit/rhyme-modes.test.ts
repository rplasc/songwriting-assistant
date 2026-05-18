import { beforeEach, describe, expect, it } from "vitest";
import {
  DEFAULT_RHYME_MODE,
  RHYME_MODE_OPTIONS,
  RHYME_MODE_STORAGE_KEY,
  readStoredRhymeMode,
  writeStoredRhymeMode,
} from "@/features/analysis/rhyme-modes";

describe("rhyme-modes", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("exposes Perfect and Near options with descriptions", () => {
    expect(RHYME_MODE_OPTIONS.map((o) => o.value)).toEqual(["perfect", "near"]);
    for (const option of RHYME_MODE_OPTIONS) {
      expect(option.label.length).toBeGreaterThan(0);
      expect(option.description.length).toBeGreaterThan(0);
    }
  });

  it("defaults to perfect", () => {
    expect(DEFAULT_RHYME_MODE).toBe("perfect");
    expect(readStoredRhymeMode()).toBe("perfect");
  });

  it("round-trips a stored mode through localStorage", () => {
    writeStoredRhymeMode("near");
    expect(window.localStorage.getItem(RHYME_MODE_STORAGE_KEY)).toBe("near");
    expect(readStoredRhymeMode()).toBe("near");
  });

  it("falls back to the default for garbage values", () => {
    window.localStorage.setItem(RHYME_MODE_STORAGE_KEY, "wild");
    expect(readStoredRhymeMode()).toBe("perfect");
  });
});
