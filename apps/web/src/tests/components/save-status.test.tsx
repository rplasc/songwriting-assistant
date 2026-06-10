import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SaveStatusIndicator } from "@/components/editor/save-status";

describe("SaveStatusIndicator", () => {
  it("renders nothing when idle so an empty page stays quiet", () => {
    const { container } = render(
      <SaveStatusIndicator status="idle" lastSavedAt={null} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows Unsaved when dirty", () => {
    render(<SaveStatusIndicator status="dirty" lastSavedAt={null} />);
    expect(screen.getByRole("status")).toHaveTextContent(/unsaved/i);
  });

  it("shows Saving while a save is in flight", () => {
    render(<SaveStatusIndicator status="saving" lastSavedAt={null} />);
    expect(screen.getByRole("status")).toHaveTextContent(/saving/i);
  });

  it("shows 'a moment ago' right after saving", () => {
    const now = new Date();
    const tenSecondsAgo = new Date(now.getTime() - 10_000);
    render(<SaveStatusIndicator status="saved" lastSavedAt={tenSecondsAgo} />);
    expect(screen.getByRole("status")).toHaveTextContent(/saved a moment ago/i);
  });

  it("shows minutes once the save is older than a minute", () => {
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60_000);
    render(<SaveStatusIndicator status="saved" lastSavedAt={fiveMinutesAgo} />);
    expect(screen.getByRole("status").textContent).toMatch(/\d+m ago/);
  });

  it("shows the offline copy when the gateway is unreachable", () => {
    render(<SaveStatusIndicator status="offline" lastSavedAt={null} />);
    expect(screen.getByRole("status")).toHaveTextContent(/offline/i);
  });
});
