import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { generateExplanation, replayCalculation } from "../api";
import { makeExplanationDetails, makeInvestigationData } from "../test/fixtures";
import { InvestigationWorkspace } from "./InvestigationWorkspace";

vi.mock("../api", async (importOriginal) => {
  const original = await importOriginal<typeof import("../api")>();
  return { ...original, generateExplanation: vi.fn(), replayCalculation: vi.fn() };
});

const mockedGenerate = vi.mocked(generateExplanation);
const mockedReplay = vi.mocked(replayCalculation);

describe("InvestigationWorkspace", () => {
  beforeEach(() => {
    mockedGenerate.mockReset();
    mockedGenerate.mockResolvedValue(makeExplanationDetails());
    mockedReplay.mockReset();
    mockedReplay.mockResolvedValue({
      calculation_id: "calc:snapshot-analysis:0123456789abcdefabcd",
      replay_success: true,
      expected_output_hash: "b".repeat(64),
      actual_output_hash: "b".repeat(64),
      numeric_differences: [],
      version_match: true,
      configuration_match: true,
      stale_dependencies: [],
      explanation: "Replay matched authoritative evidence",
    });
  });

  it("switches state, reveals score components, and preserves accessible layer controls", async () => {
    const user = userEvent.setup();
    render(
      <InvestigationWorkspace
        data={makeInvestigationData()}
        fixtureIds={["positive-interaction"]}
        selectedFixture="positive-interaction"
        onFixtureChange={vi.fn()}
      />,
    );

    const alternative = screen.getByRole("button", { name: "Alternative" });
    await user.click(alternative);
    expect(alternative).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("0.190", { selector: ".metric-callout strong" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "5. Tactical score components" }));
    expect(screen.getByTestId("score-components")).toBeInTheDocument();

    await user.click(
      screen.getByRole("checkbox", { name: /Pressure field/i }),
    );
    expect(screen.getByTestId("pressure-layer")).toBeInTheDocument();
  });

  it("retrieves replay evidence and closes the ledger with Escape", async () => {
    const user = userEvent.setup();
    render(
      <InvestigationWorkspace
        data={makeInvestigationData()}
        fixtureIds={["positive-interaction"]}
        selectedFixture="positive-interaction"
        onFixtureChange={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Inspect evidence" }));
    const drawer = await screen.findByRole("dialog", { name: "Evidence ledger" });
    expect(
      within(drawer).getAllByLabelText("Status: SUPPORTED"),
    ).not.toHaveLength(0);
    expect(within(drawer).getAllByText(/calc:snapshot-analysis/)).not.toHaveLength(
      0,
    );

    await user.click(within(drawer).getByRole("button", { name: "Run deterministic replay" }));
    expect(mockedReplay).toHaveBeenCalledWith("calc:snapshot-analysis:0123456789abcdefabcd");
    expect(await within(drawer).findByText("Authoritative output matched")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog", { name: "Evidence ledger" })).not.toBeInTheDocument();
  });

  it("presents replay failures without replacing authoritative evidence", async () => {
    mockedReplay.mockRejectedValueOnce(new Error("Replay service unavailable"));
    const user = userEvent.setup();
    render(
      <InvestigationWorkspace
        data={makeInvestigationData()}
        fixtureIds={["positive-interaction"]}
        selectedFixture="positive-interaction"
        onFixtureChange={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Inspect evidence" }));
    const drawer = await screen.findByRole("dialog", { name: "Evidence ledger" });
    await user.click(
      within(drawer).getByRole("button", { name: "Run deterministic replay" }),
    );

    expect(await within(drawer).findByRole("alert")).toHaveTextContent(
      "Replay service unavailable",
    );
    expect(within(drawer).getAllByText(/calc:snapshot-analysis/)).not.toHaveLength(
      0,
    );
  });

  it("opens authoritative evidence from a sentence-level citation", async () => {
    const user = userEvent.setup();
    render(
      <InvestigationWorkspace
        data={makeInvestigationData()}
        fixtureIds={["positive-interaction"]}
        selectedFixture="positive-interaction"
        onFixtureChange={vi.fn()}
      />,
    );

    const citation = await screen.findByRole("button", {
      name: "Open evidence citation 1 for sentence sentence-01",
    });
    await user.click(citation);

    expect(await screen.findByRole("dialog", { name: "Evidence ledger" })).toBeInTheDocument();
  });
});
