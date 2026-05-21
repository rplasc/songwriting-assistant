import type { ReactNode } from "react";

interface EditorLayoutProps {
  editor: ReactNode;
  panels: ReactNode;
  rail?: ReactNode;
}

export function EditorLayout({ editor, panels, rail }: EditorLayoutProps) {
  return (
    <div
      className={
        rail
          ? "grid w-full gap-5 2xl:gap-8 lg:grid-cols-[minmax(0,1fr)_18rem] xl:grid-cols-[minmax(0,1fr)_17rem_15rem] 2xl:grid-cols-[minmax(0,1fr)_21rem_18rem]"
          : "grid w-full gap-5 2xl:gap-8 lg:grid-cols-[minmax(0,1fr)_18rem] xl:grid-cols-[minmax(0,1fr)_20rem] 2xl:grid-cols-[minmax(0,1fr)_26rem]"
      }
    >
      <div className="min-w-0">{editor}</div>
      <aside className="flex min-w-0 flex-col gap-3">{panels}</aside>
      {rail ? <div className="lg:col-start-2 xl:contents">{rail}</div> : null}
    </div>
  );
}
