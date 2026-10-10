import type { ClaimType, ValidityState, VerificationStatus } from "../types";

type BadgeValue = ClaimType | VerificationStatus | ValidityState;

interface StatusBadgeProps {
  value: BadgeValue;
  subtle?: boolean;
}

export function StatusBadge({ value, subtle = false }: StatusBadgeProps) {
  const label = value.replaceAll("_", " ");
  return (
    <span
      className={`status-badge status-${value.toLowerCase().replaceAll("_", "-")} ${subtle ? "status-subtle" : ""}`}
      aria-label={`Status: ${label}`}
    >
      <span className="status-dot" aria-hidden="true" />
      {label}
    </span>
  );
}
