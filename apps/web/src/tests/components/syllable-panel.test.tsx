import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SyllablePanel } from "@/components/editor/syllable-panel";
import type { AnalysisResult } from "@/features/analysis/analysis-types";

const RESULT: AnalysisResult = {
  line: "I see the fire in your eyes",
  totalSyllables: 8,
  tokens: [
    { text: "I", syllables: 1 },
    { text: "see", syllables: 1 },
    { text: "fire", syllables: 2 },
  ],
  targetWord: "eyes",
  rhymes: [],
  latencyMs: 30,
};

describe("SyllablePanel", () => {
  it("shows the empty-state prompt in idle with no result", () => {
    render(<SyllablePanel status="idle" result={null} />);
    expect(
      screen.getByText(/start writing to see syllable counts/i),
    ).toBeInTheDocument();
  });

  it("shows the error empty state when status is error and result is null", () => {
    render(<SyllablePanel status="error" result={null} />);
    expect(
      screen.getByText(/reach the analysis service/i),
    ).toBeInTheDocument();
  });

  it("shows the total syllable count when a result is present", () => {
    render(<SyllablePanel status="ready" result={RESULT} />);
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("renders each token with its syllable count", () => {
    render(<SyllablePanel status="ready" result={RESULT} />);
    expect(screen.getByText("I")).toBeInTheDocument();
    expect(screen.getByText("fire")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("shows the counting indicator when status is loading", () => {
    render(<SyllablePanel status="loading" result={null} />);
    expect(screen.getByText(/counting/i)).toBeInTheDocument();
  });

  it("hides the counting indicator when not loading", () => {
    render(<SyllablePanel status="ready" result={RESULT} />);
    expect(screen.queryByText(/counting/i)).not.toBeInTheDocument();
  });

  it("keeps the previous result visible (dimmed) while loading", () => {
    render(<SyllablePanel status="loading" result={RESULT} />);
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("uses singular 'syllable' when count is 1", () => {
    const singleResult = { ...RESULT, totalSyllables: 1 };
    render(<SyllablePanel status="ready" result={singleResult} />);
    expect(screen.getByText("syllable")).toBeInTheDocument();
  });
});
