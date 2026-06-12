import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { MarginRail } from "@/components/editor/margin-rail";
import type { AnalysisResult } from "@/features/analysis/analysis-types";
import type { DraftAnalysis } from "@/features/draft-analysis/draft-analysis-types";

const LINE_RESULT: AnalysisResult = {
  line: "Your warmth I embrace.",
  language: "en",
  totalSyllables: 5,
  tokens: [
    { text: "Your", syllables: 1 },
    { text: "warmth", syllables: 1 },
    { text: "I", syllables: 1 },
    { text: "embrace", syllables: 2 },
  ],
  targetWord: "embrace",
  rhymes: [],
  innerRhymes: [],
  rhymeMode: "perfect",
  lowConfidence: false,
  latencyMs: 10,
};

const ANALYSIS: DraftAnalysis = {
  draftId: "d1",
  revisionHash: "h1",
  language: "en",
  title: null,
  summary: {
    sectionCount: 3,
    lineCount: 11,
    totalSyllables: 74,
    notablePatterns: [],
  },
  sections: [
    {
      id: "sec_1",
      label: "verse",
      lineStart: 1,
      lineEnd: 5,
      lineCount: 4,
      rhymeScheme: "ABAB",
      rhymeSchemeConfidence: "full",
      syllablePattern: [5, 6, 5, 5],
      syllableVariance: 1.4,
      cadenceClass: "mixed",
      repetitionSignals: [],
    },
  ],
  insights: [
    {
      id: "ins_1",
      type: "weak_line",
      scope: "section",
      target: "sec_1",
      severity: "medium",
      message: "This line isn't pulling weight.",
      evidence: null,
      anchor: { scope: "section", sectionId: "sec_1", lineStart: 3, lineEnd: 3 },
      confidence: "medium",
      hookContext: false,
    },
  ],
  innerRhymes: [],
  capabilities: {
    rhymeScheme: "full",
    cadencePatterns: "full",
    stressHints: "partial",
    repetition: "full",
    mixedLanguage: "partial",
  },
  analyzedAt: "2026-06-10T12:00:00Z",
  latencyMs: 12,
  serverStatus: "fresh",
};

const noop = () => {};

function renderRail(props: Partial<Parameters<typeof MarginRail>[0]> = {}) {
  return render(
    <MarginRail
      open={true}
      onToggle={noop}
      language="en"
      lineStatus="ready"
      lineResult={LINE_RESULT}
      lineNotes={["Matches the Verse cadence (5)."]}
      status="fresh"
      analysis={ANALYSIS}
      error={null}
      onRefresh={noop}
      onJump={noop}
      onInsertSection={noop}
      compareStatus="idle"
      compareResult={null}
      compareError={null}
      baselineSet={false}
      baselineMatchesCurrent={false}
      onSetBaseline={noop}
      onClearBaseline={noop}
      onCompare={noop}
      {...props}
    />,
  );
}

describe("MarginRail", () => {
  it("exposes three tabs and opens on the Line tab", () => {
    renderRail();
    const tabs = screen.getAllByRole("tab");
    expect(tabs.map((t) => t.textContent)).toEqual([
      "Line",
      "Structure",
      "Insights",
    ]);
    expect(screen.getByRole("tab", { name: "Line" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    // Big numeral + token chips + note.
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText(/em.*brace.*2|embrace·2/)).toBeInTheDocument();
    expect(screen.getByText(/matches the verse cadence/i)).toBeInTheDocument();
  });

  it("jumps to the flagged line from the weak-line link", async () => {
    const onJump = vi.fn();
    renderRail({ onJump });
    await userEvent.click(
      screen.getByRole("button", { name: /find a line that's not pulling weight/i }),
    );
    expect(onJump).toHaveBeenCalledWith(3, 3);
  });

  it("shows structure details on the Structure tab", async () => {
    renderRail();
    await userEvent.click(screen.getByRole("tab", { name: "Structure" }));
    expect(screen.getByText(/at a glance/i)).toBeInTheDocument();
    // Scheme shows in the at-a-glance grid and again in the section list.
    expect(screen.getAllByText("ABAB").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /\+ section/i })).toBeInTheDocument();
  });

  it("lists insights on the Insights tab", async () => {
    renderRail();
    await userEvent.click(screen.getByRole("tab", { name: "Insights" }));
    expect(
      screen.getByText(/this line isn't pulling weight/i),
    ).toBeInTheDocument();
  });

  it("collapses to a thin strip with an expand affordance", async () => {
    const onToggle = vi.fn();
    renderRail({ open: false, onToggle });
    expect(screen.queryByRole("tablist")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: /show review/i }));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("invites the caret onto a line when there's no live result", () => {
    renderRail({ lineResult: null });
    expect(screen.getByText(/put the caret on a line/i)).toBeInTheDocument();
  });
});
