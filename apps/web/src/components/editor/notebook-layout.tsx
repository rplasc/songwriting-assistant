import type { ReactNode } from "react";

interface NotebookLayoutProps {
  main: ReactNode;
  rail: ReactNode;
  railOpen: boolean;
}

/**
 * Notebook page: lyrics column plus the margin rail. When the rail is
 * collapsed it only needs a thin strip, so the grid tightens around it.
 */
export function NotebookLayout({ main, rail, railOpen }: NotebookLayoutProps) {
  return (
    <div
      className={
        railOpen
          ? "grid w-full gap-6 lg:grid-cols-[minmax(0,1fr)_17rem] 2xl:grid-cols-[minmax(0,1fr)_20rem] 2xl:gap-10"
          : "grid w-full gap-4 lg:grid-cols-[minmax(0,1fr)_2.25rem]"
      }
    >
      <div className="flex min-w-0 flex-col gap-4">{main}</div>
      {rail}
    </div>
  );
}
