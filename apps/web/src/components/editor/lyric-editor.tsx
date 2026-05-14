"use client";

import { EditorContent, type Editor } from "@tiptap/react";

interface LyricEditorProps {
  editor: Editor | null;
}

export function LyricEditor({ editor }: LyricEditorProps) {
  return (
    <div className="min-h-96 rounded-md border border-border bg-surface px-6 py-5 shadow-[0_1px_3px_0_rgb(0,0,0,0.04)] transition-shadow duration-200 focus-within:border-accent/60 focus-within:shadow-[0_1px_3px_0_rgb(0,0,0,0.04),0_0_0_3px_oklch(from_var(--accent)_l_c_h_/_0.12)]">
      <EditorContent editor={editor} />
    </div>
  );
}
