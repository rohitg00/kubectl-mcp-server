import React from "react";

export type StatusType =
  | "success"
  | "warning"
  | "error"
  | "info"
  | "neutral"
  | "pending";

export interface StatusBadgeProps {
  status: string;
  type?: StatusType;
  size?: "sm" | "md" | "lg";
  icon?: boolean;
  pulse?: boolean;
}

const STATUS_MAP: Record<string, StatusType> = {
  Running: "success",
  Succeeded: "success",
  Active: "success",
  Ready: "success",
  deployed: "success",
  Healthy: "success",
  Complete: "success",
  Bound: "success",

  Pending: "pending",
  ContainerCreating: "pending",
  "pending-install": "pending",
  "pending-upgrade": "pending",
  "pending-rollback": "pending",
  Progressing: "pending",
  Waiting: "pending",

  Warning: "warning",
  Unknown: "warning",
  Unschedulable: "warning",
  superseded: "warning",

  Failed: "error",
  Error: "error",
  CrashLoopBackOff: "error",
  ImagePullBackOff: "error",
  ErrImagePull: "error",
  Terminating: "error",
  NotReady: "error",
  failed: "error",
  uninstalling: "error",

  Normal: "info",
  Info: "info",
  uninstalled: "neutral",
};

const ICONS: Record<StatusType, string> = {
  success: "✓",
  warning: "⚠",
  error: "✕",
  info: "ℹ",
  neutral: "○",
  pending: "◐",
};

export function StatusBadge({
  status,
  type,
  size = "md",
  icon = true,
  pulse = false,
}: StatusBadgeProps): React.ReactElement {
  const statusType = type || STATUS_MAP[status] || "neutral";
  const shouldPulse = pulse || statusType === "pending";

  return (
    <span className={`status-badge ${statusType} ${size} ${shouldPulse ? "pulse" : ""}`}>
      {icon && <span className="status-icon">{ICONS[statusType]}</span>}
      <span className="status-text">{status}</span>

      <style>{`
        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 2px 8px;
          border-radius: 12px;
          font-weight: 500;
          white-space: nowrap;
        }

        .status-badge.sm {
          font-size: 11px;
          padding: 1px 6px;
        }

        .status-badge.md {
          font-size: 12px;
        }

        .status-badge.lg {
          font-size: 13px;
          padding: 4px 10px;
        }

        .status-icon {
          font-size: 0.9em;
        }

        .status-badge.success {
          background: var(--success-bg);
          color: var(--success);
        }

        .status-badge.warning {
          background: var(--warning-bg);
          color: var(--warning);
        }

        .status-badge.error {
          background: var(--error-bg);
          color: var(--error);
        }

        .status-badge.info {
          background: var(--info-bg);
          color: var(--info);
        }

        .status-badge.neutral {
          background: var(--bg-tertiary);
          color: var(--text-secondary);
        }

        .status-badge.pending {
          background: var(--info-bg);
          color: var(--info);
        }

        .status-badge.pulse .status-icon {
          animation: pulse 1.5s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </span>
  );
}

export function getStatusType(status: string): StatusType {
  return STATUS_MAP[status] || "neutral";
}
