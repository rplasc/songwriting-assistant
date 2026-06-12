import { LyricEditorShell } from "@/components/editor/lyric-editor-shell";

export default function Home() {
  return (
    <main className="flex flex-1 justify-center px-4 py-8 sm:px-6 sm:py-12 2xl:px-12 2xl:py-16">
      <div className="w-full max-w-7xl 2xl:max-w-440">
        <p className="mb-1.5 font-mono text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground">
          Songwriting Tool Demo
        </p>
        <LyricEditorShell />
      </div>
    </main>
  );
}
