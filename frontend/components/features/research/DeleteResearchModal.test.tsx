import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import DeleteResearchModal from "@/components/features/research/DeleteResearchModal";

const labels = {
  title: "Delete research permanently?",
  description: '"{name}" will be removed from this browser.',
  irreversible: "This cannot be undone.",
  confirm: "Delete permanently",
  cancel: "Cancel",
  deleting: "Deleting…",
};

describe("DeleteResearchModal", () => {
  it("keeps the destructive action explicit and available", async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();

    render(
      <DeleteResearchModal
        open
        researchName="MUU"
        labels={labels}
        onClose={vi.fn()}
        onConfirm={onConfirm}
      />
    );

    const confirm = screen.getByRole("button", {
      name: "Delete permanently",
    });
    expect(confirm).toBeEnabled();
    expect(confirm).toHaveClass("btn--danger");

    await user.click(confirm);
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });
});
