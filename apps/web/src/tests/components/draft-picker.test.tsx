import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DraftPicker } from "@/components/editor/draft-picker";
import type { DraftSummary } from "@/features/drafts/drafts-types";

const DRAFTS: DraftSummary[] = [
  { id: "a", title: "First lines", updatedAt: "2026-05-18T10:00:00.000Z" },
  { id: "b", title: "Bridge ideas", updatedAt: "2026-05-17T18:30:00.000Z" },
];

describe("DraftPicker", () => {
  it("hides the menu until the trigger is clicked", () => {
    render(
      <DraftPicker
        drafts={DRAFTS}
        currentDraftId={null}
        onSelect={() => {}}
        onNew={() => {}}
      />,
    );
    expect(screen.queryByRole("menu")).toBeNull();
  });

  it("lists each summary when opened", async () => {
    render(
      <DraftPicker
        drafts={DRAFTS}
        currentDraftId="b"
        onSelect={() => {}}
        onNew={() => {}}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /drafts/i }));
    expect(screen.getByRole("menu")).toBeInTheDocument();
    expect(screen.getByText("First lines")).toBeInTheDocument();
    expect(screen.getByText("Bridge ideas")).toBeInTheDocument();
  });

  it("fires onSelect with the chosen id", async () => {
    const onSelect = vi.fn();
    render(
      <DraftPicker
        drafts={DRAFTS}
        currentDraftId={null}
        onSelect={onSelect}
        onNew={() => {}}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /drafts/i }));
    await userEvent.click(screen.getByText("First lines"));
    expect(onSelect).toHaveBeenCalledWith("a");
  });

  it("fires onNew when the New draft option is chosen", async () => {
    const onNew = vi.fn();
    render(
      <DraftPicker
        drafts={DRAFTS}
        currentDraftId={null}
        onSelect={() => {}}
        onNew={onNew}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /drafts/i }));
    await userEvent.click(screen.getByRole("menuitem", { name: /new draft/i }));
    expect(onNew).toHaveBeenCalledTimes(1);
  });

  it("shows an empty hint when there are no drafts", async () => {
    render(
      <DraftPicker
        drafts={[]}
        currentDraftId={null}
        onSelect={() => {}}
        onNew={() => {}}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /drafts/i }));
    expect(screen.getByText(/nothing saved yet/i)).toBeInTheDocument();
  });
});
