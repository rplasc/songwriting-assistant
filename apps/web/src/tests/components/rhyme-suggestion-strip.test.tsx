import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { RhymeSuggestionStrip } from "@/components/editor/rhyme-suggestion-strip";
import type { AnalysisResult } from "@/features/analysis/analysis-types";

function makeResult(overrides: Partial<AnalysisResult> = {}): AnalysisResult {
  return {
    line: "Your warmth I embrace.",
    language: "en",
    totalSyllables: 5,
    tokens: [],
    targetWord: "embrace",
    rhymes: [
      { word: "face", syllables: 1, type: "perfect" },
      { word: "grace", syllables: 1, type: "perfect" },
    ],
    innerRhymes: [],
    rhymeMode: "perfect",
    lowConfidence: false,
    latencyMs: 10,
    ...overrides,
  };
}

const noop = () => {};

function renderStrip(props: Partial<Parameters<typeof RhymeSuggestionStrip>[0]> = {}) {
  return render(
    <RhymeSuggestionStrip
      status="ready"
      result={makeResult()}
      rhymeMode="perfect"
      language="en"
      onRequestModeChange={noop}
      onInsertWord={noop}
      onOpenExplorer={noop}
      explorerOpen={false}
      {...props}
    />,
  );
}

describe("RhymeSuggestionStrip", () => {
  it("shows the target word, mode, and suggestion chips", () => {
    renderStrip();
    expect(screen.getByText("embrace")).toBeInTheDocument();
    expect(screen.getByText(/perfect/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /face/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /grace/ })).toBeInTheDocument();
  });

  it("inserts a word when its chip is clicked", async () => {
    const onInsertWord = vi.fn();
    renderStrip({ onInsertWord });
    await userEvent.click(screen.getByRole("button", { name: /^face/ }));
    expect(onInsertWord).toHaveBeenCalledWith("face");
  });

  it("nudges toward Near when perfect mode comes up empty", async () => {
    const onRequestModeChange = vi.fn();
    renderStrip({
      result: makeResult({ rhymes: [] }),
      onRequestModeChange,
    });
    expect(screen.getByText(/no perfect rhymes/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /try near/i }));
    expect(onRequestModeChange).toHaveBeenCalledWith("near");
  });

  it("asks for a finished word when there's no target", () => {
    renderStrip({ result: null });
    expect(screen.getByText(/finish a word to see rhymes/i)).toBeInTheDocument();
  });

  it("offers the explorer only while it's closed", () => {
    const { rerender } = renderStrip();
    expect(screen.getByRole("button", { name: /explore deeper/i })).toBeInTheDocument();
    rerender(
      <RhymeSuggestionStrip
        status="ready"
        result={makeResult()}
        rhymeMode="perfect"
        language="en"
        onRequestModeChange={noop}
        onInsertWord={noop}
        onOpenExplorer={noop}
        explorerOpen={true}
      />,
    );
    expect(screen.queryByRole("button", { name: /explore deeper/i })).toBeNull();
  });
});
