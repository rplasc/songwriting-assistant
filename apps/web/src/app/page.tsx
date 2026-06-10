import { LyricEditorShell } from "@/components/editor/lyric-editor-shell";

export default function Home() {
  return (
    <main className="flex flex-1 justify-center px-4 py-8 sm:px-10 sm:py-12 2xl:px-20 2xl:py-16">
      <div className="w-full max-w-6xl 2xl:max-w-432">
        <LyricEditorShell />
      </div>
    </main>
  );
}
