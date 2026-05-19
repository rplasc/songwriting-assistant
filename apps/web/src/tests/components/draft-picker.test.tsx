import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DraftPicker } from "@/components/editor/draft-picker";
import type { DraftSummary } from "@/features/drafts/drafts-types";

const DRAFTS: DraftSummary[] = [
  { id: "a", title: "First lines", language: "en", updatedAt: "2026-05-18T10:00:00.000Z" },
  { id: "b", title: "Bridge ideas", language: "en", updatedAt: "2026-05-17T18:30:00.000Z" },
];

describe("DraftPicker", () => {
  it("hides the menu until the trigger is clicked", () => {
    render(
      <DraftPicker
        drafts={DRAFTS}
        currentDraftId={null}
        onSelect={() => {}}
        onNew={() => {}}
        onDelete={() => {}}
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
        onDelete={() => {}}
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
        onDelete={() => {}}
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
        onDelete={() => {}}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /drafts/i }));
    await userEvent.click(screen.getByRole("menuitem", { name: /new draft/i }));
    expect(onNew).toHaveBeenCalledTimes(1);
  });

  it("fires onDelete with the draft id when the trash button is clicked", async () => {
    const onDelete = vi.fn();
    const onSelect = vi.fn();
    render(
      <DraftPicker
        drafts={DRAFTS}
        currentDraftId={null}
        onSelect={onSelect}
        onNew={() => {}}
        onDelete={onDelete}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /drafts/i }));
    await userEvent.click(
      screen.getByRole("button", { name: /delete draft “first lines”/i }),
    );
    expect(onDelete).toHaveBeenCalledWith("a");
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("shows an empty hint when there are no drafts", async () => {
    render(
      <DraftPicker
        drafts={[]}
        currentDraftId={null}
        onSelect={() => {}}
        onNew={() => {}}
        onDelete={() => {}}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /drafts/i }));
    expect(screen.getByText(/nothing saved yet/i)).toBeInTheDocument();
  });
});
