import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SectionLabelMenu } from "@/components/editor/section-label-menu";

const RANGE = { lineStart: 1, lineEnd: 4 };

describe("SectionLabelMenu", () => {
  it("shows the unlabeled affordance when no label is set", () => {
    render(
      <SectionLabelMenu
        range={RANGE}
        label={null}
        language="en"
        onAssign={() => {}}
        onClear={() => {}}
      />,
    );
    expect(screen.getByRole("button", { name: /label section/i })).toBeInTheDocument();
  });

  it("assigns a preset label when the menu item is clicked", () => {
    const onAssign = vi.fn();
    render(
      <SectionLabelMenu
        range={RANGE}
        label={null}
        language="en"
        onAssign={onAssign}
        onClear={() => {}}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /label section/i }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Chorus" }));
    expect(onAssign).toHaveBeenCalledWith(RANGE, "Chorus");
  });

  it("clears a label when the clear item is clicked", () => {
    const onClear = vi.fn();
    render(
      <SectionLabelMenu
        range={RANGE}
        label="Verse"
        language="en"
        onAssign={() => {}}
        onClear={onClear}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /verse/i }));
    fireEvent.click(screen.getByRole("menuitem", { name: /clear label/i }));
    expect(onClear).toHaveBeenCalledWith(RANGE);
  });
});
