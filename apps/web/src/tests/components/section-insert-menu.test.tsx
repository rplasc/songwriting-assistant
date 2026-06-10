import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SectionInsertMenu } from "@/components/editor/section-insert-menu";

describe("SectionInsertMenu", () => {
  it("keeps the preset menu hidden until opened", () => {
    render(<SectionInsertMenu language="en" onInsert={() => {}} />);
    expect(screen.queryByRole("menu")).toBeNull();
  });

  it("inserts the chosen preset and closes", async () => {
    const onInsert = vi.fn();
    render(<SectionInsertMenu language="en" onInsert={onInsert} />);
    await userEvent.click(screen.getByRole("button", { name: /\+ section/i }));
    await userEvent.click(screen.getByRole("menuitem", { name: /\[Chorus\]/ }));
    expect(onInsert).toHaveBeenCalledWith("Chorus");
    expect(screen.queryByRole("menu")).toBeNull();
  });

  it("offers Spanish presets for Spanish drafts", async () => {
    render(<SectionInsertMenu language="es" onInsert={() => {}} />);
    await userEvent.click(screen.getByRole("button", { name: /\+ sección/i }));
    expect(screen.getByRole("menuitem", { name: /\[Coro\]/ })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /\[Puente\]/ })).toBeInTheDocument();
  });
});
