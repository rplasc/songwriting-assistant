"use client";

import { EditorContent, type Editor } from "@tiptap/react";

interface LyricEditorProps {
  editor: Editor | null;
}

export function LyricEditor({ editor }: LyricEditorProps) {
  return (
    <div className="min-h-80 rounded-lg border border-border bg-surface px-5 py-4 shadow-sm focus-within:border-accent focus-within:ring-1 focus-within:ring-accent/40">
      <EditorContent editor={editor} />
    </div>
  );
}
