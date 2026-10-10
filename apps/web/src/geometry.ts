import type { PlayerState, Position } from "./types";

export const PITCH_LENGTH_METRES = 105;
export const PITCH_WIDTH_METRES = 68;

export interface PitchPoint {
  x: number;
  y: number;
}

export function toPitchPoint(position: Position): PitchPoint {
  if (
    !Number.isFinite(position.x) ||
    !Number.isFinite(position.y) ||
    position.x < 0 ||
    position.x > PITCH_LENGTH_METRES ||
    position.y < 0 ||
    position.y > PITCH_WIDTH_METRES
  ) {
    throw new RangeError("Pitch coordinates must remain inside 105 x 68 metres");
  }
  return { x: position.x, y: PITCH_WIDTH_METRES - position.y };
}

export function applyPlayerOverrides(
  players: PlayerState[],
  overrides: Record<string, Position>,
): PlayerState[] {
  return players.map((player) => {
    const override = overrides[player.player_id];
    return override
      ? { ...player, position: { x: override.x, y: override.y } }
      : { ...player, position: { ...player.position } };
  });
}

export function indexPlayers(players: PlayerState[]): Map<string, PlayerState> {
  return new Map(players.map((player) => [player.player_id, player]));
}
