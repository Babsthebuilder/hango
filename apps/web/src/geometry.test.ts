import { describe, expect, it } from "vitest";

import { applyPlayerOverrides, toPitchPoint } from "./geometry";
import type { PlayerState } from "./types";

describe("pitch coordinate mapping", () => {
  it("maps football metres to an SVG coordinate system with an inverted y axis", () => {
    expect(toPitchPoint({ x: 0, y: 0 })).toEqual({ x: 0, y: 68 });
    expect(toPitchPoint({ x: 105, y: 68 })).toEqual({ x: 105, y: 0 });
    expect(toPitchPoint({ x: 52.5, y: 34 })).toEqual({ x: 52.5, y: 34 });
  });

  it("rejects coordinates outside the validated pitch", () => {
    expect(() => toPitchPoint({ x: 106, y: 34 })).toThrow(RangeError);
    expect(() => toPitchPoint({ x: 52, y: -1 })).toThrow(RangeError);
  });

  it("applies alternatives without mutating the observed player state", () => {
    const players: PlayerState[] = [
      { player_id: "H07", team: "HOME", position: { x: 50, y: 25 } },
      { player_id: "H08", team: "HOME", position: { x: 50, y: 43 } },
    ];

    const alternative = applyPlayerOverrides(players, { H07: { x: 78, y: 26 } });

    expect(alternative[0].position).toEqual({ x: 78, y: 26 });
    expect(players[0].position).toEqual({ x: 50, y: 25 });
    expect(alternative).not.toBe(players);
    expect(alternative[0]).not.toBe(players[0]);
  });
});
