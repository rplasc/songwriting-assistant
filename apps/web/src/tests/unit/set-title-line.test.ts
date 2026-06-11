import { describe, expect, it } from "vitest";
import { Editor } from "@tiptap/core";
import StarterKit from "@tiptap/starter-kit";
import { getEditorText } from "@/features/editor/tiptap/editor-lines";
import { setTitleLine } from "@/features/editor/tiptap/set-title-line";

function makeEditor(content: string) {
  return new Editor({
    extensions: [
      StarterKit.configure({
        heading: false,
        blockquote: false,
        code: false,
        codeBlock: false,
        horizontalRule: false,
        bulletList: false,
        orderedList: false,
        listItem: false,
        strike: false,
      }),
    ],
    content: content
      .split("\n")
      .map((line) => `<p>${line}</p>`)
      .join(""),
  });
}

describe("setTitleLine", () => {
  it("rewrites the first lyric line", () => {
    const editor = makeEditor("Old title\nSecond line");
    setTitleLine(editor, "New title");
    expect(getEditorText(editor)).toBe("New title\nSecond line");
    editor.destroy();
  });

  it("skips section-label lines to find the title line", () => {
    const editor = makeEditor("[Verse]\nOld title\nSecond line");
    setTitleLine(editor, "New title");
    expect(getEditorText(editor)).toBe("[Verse]\nNew title\nSecond line");
    editor.destroy();
  });

  it("inserts a new first line when the draft is empty", () => {
    const editor = makeEditor("");
    setTitleLine(editor, "First line");
    expect(getEditorText(editor)).toBe("First line\n");
    editor.destroy();
  });

  it("inserts a new first line when only section labels exist", () => {
    const editor = makeEditor("[Verse]");
    setTitleLine(editor, "First line");
    expect(getEditorText(editor)).toBe("First line\n[Verse]");
    editor.destroy();
  });

  it("clears the title line when given an empty string", () => {
    const editor = makeEditor("Old title\nSecond line");
    setTitleLine(editor, "");
    expect(getEditorText(editor)).toBe("\nSecond line");
    editor.destroy();
  });

  it("does nothing for an empty title on an empty draft", () => {
    const editor = makeEditor("");
    setTitleLine(editor, "  ");
    expect(getEditorText(editor)).toBe("");
    editor.destroy();
  });
});
