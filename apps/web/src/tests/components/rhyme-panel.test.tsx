import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RhymePanel } from "@/components/editor/rhyme-panel";
import type { AnalysisResult } from "@/features/analysis/analysis-types";

const RESULT_WITH_RHYMES: AnalysisResult = {
  line: "I see the fire in your eyes",
  totalSyllables: 8,
  tokens: [],
  targetWord: "eyes",
  rhymes: [
    { word: "skies", syllables: 1, type: "perfect" },
    { word: "rise", syllables: 1, type: "near" },
  ],
  latencyMs: 20,
};

const RESULT_NO_RHYMES: AnalysisResult = {
  ...RESULT_WITH_RHYMES,
  rhymes: [],
};

const RESULT_NO_TARGET: AnalysisResult = {
  ...RESULT_WITH_RHYMES,
  targetWord: null,
  rhymes: [],
};

describe("RhymePanel", () => {
  it("shows the empty-state prompt when idle with no result", () => {
    render(<RhymePanel status="idle" result={null} />);
    expect(screen.getByText(/finish a word to see rhymes/i)).toBeInTheDocument();
  });

  it("shows empty-state prompt when result has no target word", () => {
    render(<RhymePanel status="ready" result={RESULT_NO_TARGET} />);
    expect(screen.getByText(/finish a word to see rhymes/i)).toBeInTheDocument();
  });

  it("shows error empty state when status is error and result is null", () => {
    render(<RhymePanel status="error" result={null} />);
    expect(
      screen.getByText(/reach the analysis service/i),
    ).toBeInTheDocument();
  });

  it("shows the target word label when a result has one", () => {
    render(<RhymePanel status="ready" result={RESULT_WITH_RHYMES} />);
    // The "for <target>" label uses the list aria-label
    expect(
      screen.getByRole("list", { name: /rhyme suggestions for eyes/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("eyes")).toBeInTheDocument();
  });

  it("renders each rhyme suggestion", () => {
    render(<RhymePanel status="ready" result={RESULT_WITH_RHYMES} />);
    expect(screen.getByText("skies")).toBeInTheDocument();
    expect(screen.getByText("rise")).toBeInTheDocument();
  });

  it("shows 'no rhymes found' when items list is empty but target exists", () => {
    render(<RhymePanel status="ready" result={RESULT_NO_RHYMES} />);
    expect(
      screen.getByText(/no rhymes found for this word/i),
    ).toBeInTheDocument();
  });

  it("shows the finding indicator when loading", () => {
    render(<RhymePanel status="loading" result={null} />);
    expect(screen.getByText(/finding/i)).toBeInTheDocument();
  });

  it("keeps previous rhymes visible (dimmed) while loading a new result", () => {
    render(<RhymePanel status="loading" result={RESULT_WITH_RHYMES} />);
    expect(screen.getByText("skies")).toBeInTheDocument();
  });

  it("shows degree indicators for each rhyme via aria-label", () => {
    render(<RhymePanel status="ready" result={RESULT_WITH_RHYMES} />);
    // The degree symbols are rendered with title/aria-label for the type
    expect(screen.getByLabelText("perfect")).toBeInTheDocument();
    expect(screen.getByLabelText("near")).toBeInTheDocument();
  });
});
