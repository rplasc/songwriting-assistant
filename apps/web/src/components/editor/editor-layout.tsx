import type { ReactNode } from "react";

interface EditorLayoutProps {
  editor: ReactNode;
  panels: ReactNode;
}

export function EditorLayout({ editor, panels }: EditorLayoutProps) {
  return (
    <div className="grid w-full gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <div className="min-w-0">{editor}</div>
      <aside className="flex min-w-0 flex-col gap-4">{panels}</aside>
    </div>
  );
}
