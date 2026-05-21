"use client";

import { useEditor, type Editor } from "@tiptap/react";
import { useEffect, useState } from "react";
import { lyricEditorExtensions } from "./editor-extensions";
import { getEditorText } from "./editor-lines";

export interface LyricEditorState {
  editor: Editor | null;
  activeLine: string;
  content: string;
}

function readActiveLine(editor: Editor): string {
  const { $from } = editor.state.selection;
  // The cursor's nearest block (paragraph) — treat each paragraph as one lyric line.
  const block = $from.node($from.depth);
  return (block?.textContent ?? "").trim();
}

export function useLyricEditor(): LyricEditorState {
  const [activeLine, setActiveLine] = useState<string>("");
  const [content, setContent] = useState<string>("");

  const editor = useEditor({
    extensions: lyricEditorExtensions,
    content: "",
    immediatelyRender: false,
    editorProps: {
      attributes: {
        class: "tiptap",
        "aria-label": "Lyric editor",
        spellcheck: "false",
        autocorrect: "off",
        autocapitalize: "off",
      },
    },
    onTransaction({ editor: instance }) {
      setActiveLine(readActiveLine(instance));
    },
    onUpdate({ editor: instance }) {
      setContent(getEditorText(instance));
    },
    onCreate({ editor: instance }) {
      setContent(getEditorText(instance));
    },
  });

  useEffect(() => {
    if (editor) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- seeding state from the editor instance when it mounts
      setActiveLine(readActiveLine(editor));
      setContent(getEditorText(editor));
    }
  }, [editor]);

  return { editor, activeLine, content };
}
