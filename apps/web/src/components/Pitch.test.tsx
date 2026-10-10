import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { makeInvestigationData } from "../test/fixtures";
import { Pitch } from "./Pitch";

describe("Pitch", () => {
  it("reveals tactical layers progressively and distinguishes alternatives", () => {
    const data = makeInvestigationData();
    const { rerender } = render(
      <Pitch
        fixture={data.fixture}
        comparison={data.comparison}
        pressure={data.pressure.baseline}
        viewMode="actual"
        layerStage={0}
        showPressure={false}
      />,
    );

    expect(screen.queryByTestId("actual-triangle")).not.toBeInTheDocument();
    expect(screen.queryByTestId("pressure-layer")).not.toBeInTheDocument();

    rerender(
      <Pitch
        fixture={data.fixture}
        comparison={data.comparison}
        pressure={data.pressure.baseline}
        viewMode="compare"
        layerStage={3}
        showPressure
      />,
    );

    expect(screen.getByTestId("actual-triangle")).toBeInTheDocument();
    expect(screen.getByTestId("alternative-triangle")).toBeInTheDocument();
    expect(screen.getByTestId("actual-direct-lanes")).toBeInTheDocument();
    expect(screen.getByTestId("alternative-routes")).toBeInTheDocument();
    expect(screen.getAllByTestId("movement-vector")).toHaveLength(2);
    expect(screen.getByTestId("pressure-layer")).toHaveAttribute(
      "aria-label",
      "Modeled defensive pressure field",
    );
    expect(screen.getByLabelText("HOME attacks right")).toBeInTheDocument();
    expect(screen.getByLabelText("AWAY attacks left")).toBeInTheDocument();
  });
});
