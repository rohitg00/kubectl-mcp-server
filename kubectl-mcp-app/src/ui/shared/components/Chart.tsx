import React from "react";

export interface DonutChartProps {
  value: number;
  max: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
  color?: "primary" | "success" | "warning" | "error";
}

export function DonutChart({
  value,
  max,
  size = 120,
  strokeWidth = 12,
  label,
  sublabel,
  color = "primary",
}: DonutChartProps): React.ReactElement {
  const percentage = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  const getColor = () => {
    if (percentage >= 90) return "var(--error)";
    if (percentage >= 75) return "var(--warning)";
    if (color === "success") return "var(--success)";
    if (color === "warning") return "var(--warning)";
    if (color === "error") return "var(--error)";
    return "var(--primary)";
  };

  return (
    <div className="donut-chart" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`}>
        <circle
          className="track"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          className="progress"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ stroke: getColor() }}
        />
      </svg>
      <div className="center">
        {label && <div className="label">{label}</div>}
        {sublabel && <div className="sublabel">{sublabel}</div>}
      </div>

      <style>{`
        .donut-chart {
          position: relative;
        }

        .donut-chart svg {
          transform: rotate(-90deg);
        }

        .donut-chart .track {
          fill: none;
          stroke: var(--border);
        }

        .donut-chart .progress {
          fill: none;
          stroke-linecap: round;
          transition: stroke-dashoffset 0.5s ease;
        }

        .donut-chart .center {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          text-align: center;
        }

        .donut-chart .label {
          font-size: 18px;
          font-weight: 600;
          color: var(--text);
        }

        .donut-chart .sublabel {
          font-size: 11px;
          color: var(--text-secondary);
          margin-top: 2px;
        }
      `}</style>
    </div>
  );
}

export interface BarChartProps {
  data: Array<{ label: string; value: number; color?: string }>;
  maxValue?: number;
  height?: number;
  showLabels?: boolean;
  showValues?: boolean;
}

export function BarChart({
  data,
  maxValue,
  height = 200,
  showLabels = true,
  showValues = true,
}: BarChartProps): React.ReactElement {
  const values = data.map((d) => d.value);
  const max = maxValue ?? (values.length > 0 ? Math.max(...values) : 0);

  return (
    <div className="bar-chart" style={{ height }}>
      <div className="bars">
        {data.map((item, index) => {
          const barHeight = max > 0 ? (item.value / max) * 100 : 0;
          return (
            <div key={index} className="bar-container">
              <div
                className="bar"
                style={{
                  height: `${barHeight}%`,
                  backgroundColor: item.color || "var(--primary)",
                }}
              >
                {showValues && (
                  <span className="bar-value">{item.value}</span>
                )}
              </div>
              {showLabels && <span className="bar-label">{item.label}</span>}
            </div>
          );
        })}
      </div>

      <style>{`
        .bar-chart {
          display: flex;
          flex-direction: column;
        }

        .bar-chart .bars {
          flex: 1;
          display: flex;
          align-items: flex-end;
          gap: 8px;
          padding-bottom: 24px;
        }

        .bar-chart .bar-container {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          height: 100%;
        }

        .bar-chart .bar {
          width: 100%;
          max-width: 40px;
          border-radius: 4px 4px 0 0;
          position: relative;
          min-height: 4px;
          transition: height 0.3s ease;
        }

        .bar-chart .bar-value {
          position: absolute;
          top: -20px;
          left: 50%;
          transform: translateX(-50%);
          font-size: 11px;
          color: var(--text-secondary);
          white-space: nowrap;
        }

        .bar-chart .bar-label {
          position: absolute;
          bottom: 0;
          font-size: 11px;
          color: var(--text-muted);
          white-space: nowrap;
          text-overflow: ellipsis;
          overflow: hidden;
          max-width: 60px;
        }
      `}</style>
    </div>
  );
}

export interface ProgressBarProps {
  value: number;
  max: number;
  label?: string;
  showPercentage?: boolean;
  color?: "primary" | "success" | "warning" | "error";
  size?: "sm" | "md" | "lg";
}

export function ProgressBar({
  value,
  max,
  label,
  showPercentage = true,
  color = "primary",
  size = "md",
}: ProgressBarProps): React.ReactElement {
  const percentage = max > 0 ? Math.min((value / max) * 100, 100) : 0;

  const getColor = () => {
    if (percentage >= 90) return "var(--error)";
    if (percentage >= 75) return "var(--warning)";
    if (color === "success") return "var(--success)";
    if (color === "warning") return "var(--warning)";
    if (color === "error") return "var(--error)";
    return "var(--primary)";
  };

  const heights = { sm: 4, md: 8, lg: 12 };

  return (
    <div className="progress-bar-container">
      {(label || showPercentage) && (
        <div className="progress-header">
          {label && <span className="progress-label">{label}</span>}
          {showPercentage && (
            <span className="progress-percentage">
              {percentage.toFixed(1)}%
            </span>
          )}
        </div>
      )}
      <div
        className="progress-track"
        style={{ height: heights[size] }}
      >
        <div
          className="progress-fill"
          style={{
            width: `${percentage}%`,
            backgroundColor: getColor(),
          }}
        />
      </div>

      <style>{`
        .progress-bar-container {
          width: 100%;
        }

        .progress-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
        }

        .progress-label {
          font-size: 12px;
          color: var(--text-secondary);
        }

        .progress-percentage {
          font-size: 12px;
          color: var(--text);
          font-weight: 500;
        }

        .progress-track {
          background: var(--bg-tertiary);
          border-radius: 4px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s ease;
        }
      `}</style>
    </div>
  );
}
