import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SaveStatusIndicator } from "@/components/editor/save-status";

describe("SaveStatusIndicator", () => {
  it("shows the Idle copy when nothing has been saved", () => {
    render(<SaveStatusIndicator status="idle" lastSavedAt={null} />);
    expect(screen.getByRole("status")).toHaveTextContent(/untouched/i);
  });

  it("shows Unsaved when dirty", () => {
    render(<SaveStatusIndicator status="dirty" lastSavedAt={null} />);
    expect(screen.getByRole("status")).toHaveTextContent(/unsaved/i);
  });

  it("shows Saving while a save is in flight", () => {
    render(<SaveStatusIndicator status="saving" lastSavedAt={null} />);
    expect(screen.getByRole("status")).toHaveTextContent(/saving/i);
  });

  it("shows a relative timestamp once saved", () => {
    const now = new Date();
    const tenSecondsAgo = new Date(now.getTime() - 10_000);
    render(<SaveStatusIndicator status="saved" lastSavedAt={tenSecondsAgo} />);
    expect(screen.getByRole("status")).toHaveTextContent(/saved/i);
    expect(screen.getByRole("status").textContent).toMatch(/\d+s ago/);
  });

  it("shows the offline copy when the gateway is unreachable", () => {
    render(<SaveStatusIndicator status="offline" lastSavedAt={null} />);
    expect(screen.getByRole("status")).toHaveTextContent(/offline/i);
  });
});
