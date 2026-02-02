import React, { useState, useRef, useEffect, useCallback } from "react";

export interface LogEntry {
  timestamp?: string;
  level?: "INFO" | "WARN" | "ERROR" | "DEBUG" | "TRACE";
  message: string;
  raw: string;
}

export interface LogViewerProps {
  logs: LogEntry[];
  loading?: boolean;
  autoScroll?: boolean;
  onAutoScrollChange?: (enabled: boolean) => void;
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  filterLevel?: string;
  onFilterChange?: (level: string) => void;
  onDownload?: () => void;
  maxLines?: number;
}

const LEVEL_COLORS: Record<string, string> = {
  INFO: "var(--info)",
  WARN: "var(--warning)",
  ERROR: "var(--error)",
  DEBUG: "var(--text-muted)",
  TRACE: "var(--text-muted)",
};

export function LogViewer({
  logs,
  loading = false,
  autoScroll = true,
  onAutoScrollChange,
  searchQuery = "",
  onSearchChange,
  filterLevel = "all",
  onFilterChange,
  onDownload,
  maxLines = 10000,
}: LogViewerProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isUserScrolling, setIsUserScrolling] = useState(false);

  const filteredLogs = logs
    .filter((log) => {
      if (filterLevel !== "all" && log.level !== filterLevel) return false;
      if (searchQuery && !log.raw.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      return true;
    })
    .slice(-maxLines);

  const scrollToBottom = useCallback(() => {
    if (containerRef.current && autoScroll && !isUserScrolling) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [autoScroll, isUserScrolling]);

  useEffect(() => {
    scrollToBottom();
  }, [filteredLogs.length, scrollToBottom]);

  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;

    if (!isAtBottom && autoScroll) {
      setIsUserScrolling(true);
      onAutoScrollChange?.(false);
    } else if (isAtBottom && !autoScroll) {
      setIsUserScrolling(false);
      onAutoScrollChange?.(true);
    }
  }, [autoScroll, onAutoScrollChange]);

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return "";
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString("en-US", {
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        fractionalSecondDigits: 3,
      });
    } catch {
      return timestamp;
    }
  };

  const highlightSearch = (text: string) => {
    if (!searchQuery) return text;

    const regex = new RegExp(`(${escapeRegex(searchQuery)})`, "gi");
    const parts = text.split(regex);

    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="highlight">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <div className="log-viewer">
      <div className="log-toolbar">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => onSearchChange?.(e.target.value)}
          />
          {searchQuery && (
            <span className="match-count">
              {filteredLogs.length} matches
            </span>
          )}
        </div>

        <select
          value={filterLevel}
          onChange={(e) => onFilterChange?.(e.target.value)}
          className="level-filter"
        >
          <option value="all">All Levels</option>
          <option value="ERROR">Error</option>
          <option value="WARN">Warning</option>
          <option value="INFO">Info</option>
          <option value="DEBUG">Debug</option>
        </select>

        <label className="auto-scroll-toggle">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => {
              setIsUserScrolling(!e.target.checked);
              onAutoScrollChange?.(e.target.checked);
            }}
          />
          Auto-scroll
        </label>

        {onDownload && (
          <button onClick={onDownload} className="download-btn">
            Download
          </button>
        )}
      </div>

      <div
        ref={containerRef}
        className="log-container"
        onScroll={handleScroll}
      >
        {loading && filteredLogs.length === 0 ? (
          <div className="log-loading">Loading logs...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="log-empty">No logs to display</div>
        ) : (
          filteredLogs.map((log, index) => (
            <div key={index} className={`log-line ${log.level?.toLowerCase() || ""}`}>
              {log.timestamp && (
                <span className="log-timestamp">
                  {formatTimestamp(log.timestamp)}
                </span>
              )}
              {log.level && (
                <span
                  className="log-level"
                  style={{ color: LEVEL_COLORS[log.level] }}
                >
                  [{log.level}]
                </span>
              )}
              <span className="log-message">
                {highlightSearch(log.message || log.raw)}
              </span>
            </div>
          ))
        )}
      </div>

      <div className="log-footer">
        <span>{filteredLogs.length} lines</span>
        {logs.length > maxLines && (
          <span className="truncated-notice">
            (showing last {maxLines} of {logs.length})
          </span>
        )}
      </div>

      <style>{`
        .log-viewer {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: var(--bg);
          border: 1px solid var(--border);
          border-radius: 8px;
          overflow: hidden;
        }

        .log-toolbar {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border);
          flex-wrap: wrap;
        }

        .search-box {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;
          min-width: 200px;
        }

        .search-box input {
          flex: 1;
          padding: 6px 10px;
          background: var(--bg);
          border: 1px solid var(--border);
          border-radius: 6px;
          color: var(--text);
          outline: none;
        }

        .search-box input:focus {
          border-color: var(--primary);
        }

        .match-count {
          font-size: 12px;
          color: var(--text-secondary);
        }

        .level-filter {
          padding: 6px 10px;
          background: var(--bg);
          border: 1px solid var(--border);
          border-radius: 6px;
          color: var(--text);
          cursor: pointer;
        }

        .auto-scroll-toggle {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
          color: var(--text-secondary);
          cursor: pointer;
        }

        .download-btn {
          padding: 6px 12px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border);
          border-radius: 6px;
          color: var(--text);
          cursor: pointer;
        }

        .download-btn:hover {
          background: var(--border);
        }

        .log-container {
          flex: 1;
          overflow-y: auto;
          font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
          font-size: 12px;
          line-height: 1.6;
          padding: 8px;
        }

        .log-line {
          display: flex;
          gap: 8px;
          padding: 2px 4px;
          border-radius: 2px;
        }

        .log-line:hover {
          background: var(--bg-secondary);
        }

        .log-line.error {
          background: var(--error-bg);
        }

        .log-line.warn {
          background: var(--warning-bg);
        }

        .log-timestamp {
          color: var(--text-muted);
          flex-shrink: 0;
        }

        .log-level {
          flex-shrink: 0;
          font-weight: 500;
        }

        .log-message {
          color: var(--text);
          word-break: break-word;
        }

        .highlight {
          background: var(--warning);
          color: var(--bg);
          padding: 0 2px;
          border-radius: 2px;
        }

        .log-loading,
        .log-empty {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: var(--text-muted);
        }

        .log-footer {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: var(--bg-secondary);
          border-top: 1px solid var(--border);
          font-size: 12px;
          color: var(--text-secondary);
        }

        .truncated-notice {
          color: var(--text-muted);
        }
      `}</style>
    </div>
  );
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
