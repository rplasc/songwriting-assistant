import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnalysisFreshnessBadge } from "@/components/editor/analysis-freshness-badge";

describe("AnalysisFreshnessBadge", () => {
  it("renders fresh state in English", () => {
    render(<AnalysisFreshnessBadge status="fresh" language="en" />);
    expect(screen.getByText(/up to date/i)).toBeInTheDocument();
  });

  it("renders stale state in Spanish", () => {
    render(<AnalysisFreshnessBadge status="stale" language="es" />);
    expect(screen.getByText(/cambios sin revisar/i)).toBeInTheDocument();
  });

  it("renders unsupported messaging when capabilities are missing", () => {
    render(<AnalysisFreshnessBadge status="unsupported" language="en" />);
    expect(screen.getByText(/limited for this language/i)).toBeInTheDocument();
  });
});
