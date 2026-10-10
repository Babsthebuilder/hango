import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it.each([
    ["OBSERVED", "status-observed"],
    ["CALCULATED", "status-calculated"],
    ["MODEL_ESTIMATE", "status-model-estimate"],
    ["INTERPRETATION", "status-interpretation"],
    ["SUPPORTED", "status-supported"],
    ["QUALIFIED", "status-qualified"],
    ["REJECTED", "status-rejected"],
    ["STALE", "status-stale"],
  ] as const)("presents %s with an explicit label and distinct class", (value, className) => {
    render(<StatusBadge value={value} />);

    expect(screen.getByLabelText(`Status: ${value.replace("_", " ")}`)).toHaveClass(
      className,
    );
  });
});
