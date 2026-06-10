import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RhymePanel } from "@/components/editor/rhyme-panel";
import type { AnalysisResult } from "@/features/analysis/analysis-types";

const RESULT_WITH_RHYMES: AnalysisResult = {
  line: "I see the fire in your eyes",
  language: "en",
  totalSyllables: 8,
  tokens: [],
  targetWord: "eyes",
  rhymes: [
    { word: "skies", syllables: 1, type: "perfect" },
    { word: "rise", syllables: 1, type: "near" },
  ],
  innerRhymes: [],
  rhymeMode: "perfect",
  lowConfidence: false,
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
    expect(screen.getByText(/lost the connection/i)).toBeInTheDocument();
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

  it("shows a no-rhymes message when items list is empty but target exists", () => {
    render(<RhymePanel status="ready" result={RESULT_NO_RHYMES} />);
    expect(screen.getByText(/no perfect rhymes/i)).toBeInTheDocument();
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

  it("offers a Near-mode prompt in the perfect-mode empty state", () => {
    const result: AnalysisResult = { ...RESULT_NO_RHYMES, rhymeMode: "perfect" };
    const onRequestModeChange = vi.fn();
    render(
      <RhymePanel
        status="ready"
        result={result}
        rhymeMode="perfect"
        onRequestModeChange={onRequestModeChange}
      />,
    );
    const button = screen.getByRole("button", { name: /try near/i });
    button.click();
    expect(onRequestModeChange).toHaveBeenCalledWith("near");
  });

  it("does not offer a mode switch when already in near mode", () => {
    const result: AnalysisResult = { ...RESULT_NO_RHYMES, rhymeMode: "near" };
    render(
      <RhymePanel status="ready" result={result} rhymeMode="near" />,
    );
    expect(
      screen.queryByRole("button", { name: /try near/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByText(/nothing near/i)).toBeInTheDocument();
  });
});
