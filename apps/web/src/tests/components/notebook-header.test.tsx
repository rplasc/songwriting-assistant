import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { NotebookHeader } from "@/components/editor/notebook-header";

function setup(displayTitle: string, editableTitle: string) {
  const onTitleChange = vi.fn();
  render(
    <NotebookHeader
      displayTitle={displayTitle}
      editableTitle={editableTitle}
      onTitleChange={onTitleChange}
      rhymeMode="perfect"
      onRhymeModeChange={vi.fn()}
      language="en"
      onLanguageChange={vi.fn()}
      saveStatus="idle"
      lastSavedAt={null}
      drafts={[]}
      currentDraftId={null}
      onSelectDraft={vi.fn()}
      onNewDraft={vi.fn()}
      onDeleteDraft={vi.fn()}
      theme="system"
      onThemeChange={vi.fn()}
      rhymeHighlights={true}
      onRhymeHighlightsChange={vi.fn()}
      rhymeHighlightStyle="marker"
      onRhymeHighlightStyleChange={vi.fn()}
    />,
  );
  return { onTitleChange };
}

describe("NotebookHeader title", () => {
  it("shows the display title and the untruncated editable title when editing", async () => {
    const user = userEvent.setup();
    setup("A letter to tomorrow", "A letter to tomorrow");

    const titleButton = screen.getByRole("button", { name: /edit draft title/i });
    expect(titleButton).toHaveTextContent("A letter to tomorrow");

    await user.click(titleButton);
    const input = screen.getByRole("textbox", { name: /edit draft title/i });
    expect(input).toHaveValue("A letter to tomorrow");
  });

  it("commits an edited title on Enter", async () => {
    const user = userEvent.setup();
    const { onTitleChange } = setup("Old title", "Old title");

    await user.click(screen.getByRole("button", { name: /edit draft title/i }));
    const input = screen.getByRole("textbox", { name: /edit draft title/i });
    await user.clear(input);
    await user.type(input, "New title{Enter}");

    expect(onTitleChange).toHaveBeenCalledWith("New title");
    expect(screen.getByRole("button", { name: /edit draft title/i })).toBeInTheDocument();
  });

  it("discards changes on Escape without committing", async () => {
    const user = userEvent.setup();
    const { onTitleChange } = setup("Old title", "Old title");

    await user.click(screen.getByRole("button", { name: /edit draft title/i }));
    const input = screen.getByRole("textbox", { name: /edit draft title/i });
    await user.clear(input);
    await user.type(input, "Discarded");
    await user.keyboard("{Escape}");

    expect(onTitleChange).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /edit draft title/i })).toHaveTextContent(
      "Old title",
    );
  });

  it("shows the placeholder and default title for an empty draft", async () => {
    const user = userEvent.setup();
    setup("Untitled Draft", "");

    const titleButton = screen.getByRole("button", { name: /edit draft title/i });
    expect(titleButton).toHaveTextContent("Untitled Draft");

    await user.click(titleButton);
    expect(screen.getByRole("textbox", { name: /edit draft title/i })).toHaveAttribute(
      "placeholder",
      "Untitled draft",
    );
  });
});
