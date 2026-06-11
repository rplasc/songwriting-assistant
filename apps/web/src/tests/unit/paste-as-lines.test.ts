import { describe, expect, it } from "vitest";
import { Editor } from "@tiptap/core";
import StarterKit from "@tiptap/starter-kit";
import { getEditorText } from "@/features/editor/tiptap/editor-lines";
import { PasteAsLines, splitPastedLines } from "@/features/editor/tiptap/paste-as-lines";

describe("splitPastedLines", () => {
  it("splits on newlines", () => {
    expect(splitPastedLines("a\nb\nc")).toEqual(["a", "b", "c"]);
  });

  it("normalizes CRLF", () => {
    expect(splitPastedLines("a\r\nb\r\nc")).toEqual(["a", "b", "c"]);
  });

  it("drops a single trailing newline", () => {
    expect(splitPastedLines("a\nb\n")).toEqual(["a", "b"]);
  });

  it("keeps interior blank lines", () => {
    expect(splitPastedLines("a\n\nb")).toEqual(["a", "", "b"]);
  });
});

function makeEditor() {
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
      PasteAsLines,
    ],
    content: "",
  });
}

function paste(editor: Editor, text: string): boolean {
  const handlePaste = editor.view.someProp("handlePaste");
  if (!handlePaste) return false;
  const event = {
    clipboardData: { getData: () => text },
  } as unknown as ClipboardEvent;
  return handlePaste(editor.view, event, editor.state.selection.content()) === true;
}

describe("PasteAsLines", () => {
  it("splits a multi-line paste into one paragraph per line", () => {
    const editor = makeEditor();
    const handled = paste(editor, "Counting down the days,\nTangled in my dreams,");
    expect(handled).toBe(true);
    expect(getEditorText(editor)).toBe(
      "Counting down the days,\nTangled in my dreams,",
    );
    editor.destroy();
  });

  it("drops a trailing newline instead of leaving a blank line", () => {
    const editor = makeEditor();
    paste(editor, "one\ntwo\n");
    expect(getEditorText(editor)).toBe("one\ntwo");
    editor.destroy();
  });

  it("leaves single-line pastes to default handling", () => {
    const editor = makeEditor();
    const handled = paste(editor, "just one line");
    expect(handled).toBe(false);
    editor.destroy();
  });
});
