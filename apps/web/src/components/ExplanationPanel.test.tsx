import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { generateExplanation } from "../api";
import { makeExplanationDetails } from "../test/fixtures";
import { ExplanationPanel } from "./ExplanationPanel";

vi.mock("../api", async (importOriginal) => {
  const original = await importOriginal<typeof import("../api")>();
  return { ...original, generateExplanation: vi.fn() };
});

const mockedGenerate = vi.mocked(generateExplanation);

describe("ExplanationPanel", () => {
  beforeEach(() => mockedGenerate.mockReset());

  it("shows grounded prose and exposes citations as keyboard buttons", async () => {
    mockedGenerate.mockResolvedValue(makeExplanationDetails());
    const onOpenEvidence = vi.fn();
    const user = userEvent.setup();
    render(
      <ExplanationPanel
        calculationId="calc:snapshot-analysis:0123456789abcdefabcd"
        claimId="workspace-claim"
        onOpenEvidence={onOpenEvidence}
      />,
    );

    expect(await screen.findByText("The modeled opportunity score is 0.040000.")).toBeInTheDocument();
    expect(screen.getByLabelText("Status: INTERPRETATION")).toBeInTheDocument();
    await user.tab();
    const citation = screen.getByRole("button", {
      name: "Open evidence citation 1 for sentence sentence-01",
    });
    citation.focus();
    await user.keyboard("{Enter}");
    expect(onOpenEvidence).toHaveBeenCalledOnce();
  });

  it("presents stale explanations as blocked editorial output", async () => {
    mockedGenerate.mockResolvedValue(makeExplanationDetails("STALE"));
    render(
      <ExplanationPanel
        calculationId="calc:snapshot-analysis:0123456789abcdefabcd"
        claimId="workspace-claim"
        onOpenEvidence={vi.fn()}
      />,
    );

    expect(await screen.findByLabelText("Status: STALE")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("not cleared for publication");
  });

  it("distinguishes invalidated prose from a merely stale draft", async () => {
    const details = makeExplanationDetails("REJECTED");
    details.artifact.validity_state = "INVALIDATED";
    details.artifact.publication_state = "INVALIDATED";
    mockedGenerate.mockResolvedValue(details);
    render(
      <ExplanationPanel
        calculationId="calc:snapshot-analysis:0123456789abcdefabcd"
        claimId="workspace-claim"
        onOpenEvidence={vi.fn()}
      />,
    );

    expect(await screen.findByText("INVALIDATED")).toHaveClass("publication-invalidated");
    expect(screen.getByRole("alert")).toHaveTextContent("not cleared for publication");
  });

  it("retains a retry path after provider failure", async () => {
    mockedGenerate
      .mockRejectedValueOnce(new Error("Provider unavailable"))
      .mockResolvedValueOnce(makeExplanationDetails());
    const user = userEvent.setup();
    render(
      <ExplanationPanel
        calculationId="calc:snapshot-analysis:0123456789abcdefabcd"
        claimId="workspace-claim"
        onOpenEvidence={vi.fn()}
      />,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Provider unavailable");
    await user.click(screen.getByRole("button", { name: "Retry explanation" }));
    expect(await screen.findByText("The modeled opportunity score is 0.040000.")).toBeInTheDocument();
    expect(mockedGenerate).toHaveBeenCalledTimes(2);
  });
});
