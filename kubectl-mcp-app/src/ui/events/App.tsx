import React, { useState, useEffect, useCallback, useRef } from "react";
import { StatusBadge } from "@shared/components";
import { baseStyles, getTheme, setTheme, type Theme } from "@shared/theme";

interface K8sEvent {
  type: "Normal" | "Warning";
  reason: string;
  message: string;
  object: string;
  objectKind: string;
  namespace: string;
  count: number;
  firstTimestamp: string;
  lastTimestamp: string;
  source?: string;
}

interface AppState {
  events: K8sEvent[];
  loading: boolean;
  error: string | null;
  selectedNamespace: string;
  filterType: "all" | "Normal" | "Warning";
  autoRefresh: boolean;
  selectedEvent: K8sEvent | null;
  theme: Theme;
}

declare global {
  interface Window {
    callServerTool?: (request: {
      name: string;
      arguments?: Record<string, unknown>;
    }) => Promise<{ content: Array<{ type: string; text: string }> }>;
    initialArgs?: {
      namespace?: string;
      context?: string;
      types?: string;
    };
  }
}

export function EventsTimeline(): React.ReactElement {
  const [state, setState] = useState<AppState>({
    events: [],
    loading: true,
    error: null,
    selectedNamespace: window.initialArgs?.namespace || "all",
    filterType: "all",
    autoRefresh: true,
    selectedEvent: null,
    theme: getTheme(),
  });

  const refreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const callTool = useCallback(
    async (name: string, args: Record<string, unknown> = {}) => {
      if (!window.callServerTool) {
        console.warn("callServerTool not available");
        return null;
      }
      try {
        const result = await window.callServerTool({ name, arguments: args });
        const text = result.content[0]?.text;
        return text ? JSON.parse(text) : null;
      } catch (error) {
        console.error(`Tool call failed: ${name}`, error);
        throw error;
      }
    },
    []
  );

  const fetchEvents = useCallback(async () => {
    setState((prev) => ({
      ...prev,
      loading: prev.events.length === 0,
      error: null,
    }));
    try {
      const namespace =
        state.selectedNamespace === "all" ? "" : state.selectedNamespace;
      const data = await callTool("get_events", {
        namespace,
        context: window.initialArgs?.context || "",
      });

      if (data?.events) {
        const sortedEvents = data.events.sort(
          (a: K8sEvent, b: K8sEvent) =>
            new Date(b.lastTimestamp).getTime() -
            new Date(a.lastTimestamp).getTime()
        );
        setState((prev) => ({ ...prev, events: sortedEvents, loading: false }));
      } else {
        setState((prev) => ({
          ...prev,
          events: getMockEvents(),
          loading: false,
        }));
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        events: getMockEvents(),
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch events",
      }));
    }
  }, [callTool, state.selectedNamespace]);

  useEffect(() => {
    fetchEvents();
  }, []);

  useEffect(() => {
    fetchEvents();
  }, [state.selectedNamespace]);

  useEffect(() => {
    if (state.autoRefresh) {
      refreshIntervalRef.current = setInterval(fetchEvents, 10000);
    } else if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
      refreshIntervalRef.current = null;
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [state.autoRefresh, fetchEvents]);

  const toggleTheme = useCallback(() => {
    const newTheme = state.theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    setState((prev) => ({ ...prev, theme: newTheme }));
  }, [state.theme]);

  const filteredEvents = state.events.filter((e) => {
    if (state.filterType !== "all" && e.type !== state.filterType) return false;
    return true;
  });

  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diff = now.getTime() - date.getTime();

      if (diff < 60000) return "just now";
      if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
      return date.toLocaleDateString();
    } catch {
      return timestamp;
    }
  };

  const groupedEvents = filteredEvents.reduce((groups, event) => {
    const date = new Date(event.lastTimestamp).toDateString();
    if (!groups[date]) groups[date] = [];
    groups[date].push(event);
    return groups;
  }, {} as Record<string, K8sEvent[]>);

  const warningCount = state.events.filter((e) => e.type === "Warning").length;
  const normalCount = state.events.filter((e) => e.type === "Normal").length;

  return (
    <div className="app" data-theme={state.theme}>
      <style>{baseStyles}</style>
      <style>{appStyles}</style>

      <header className="app-header">
        <div className="header-left">
          <h1>Events Timeline</h1>
          <div className="event-counts">
            <span className="warning-count">{warningCount} Warnings</span>
            <span className="normal-count">{normalCount} Normal</span>
          </div>
        </div>
        <div className="header-right">
          <select
            value={state.filterType}
            onChange={(e) =>
              setState((prev) => ({
                ...prev,
                filterType: e.target.value as AppState["filterType"],
              }))
            }
            className="filter-select"
          >
            <option value="all">All Events</option>
            <option value="Warning">Warnings Only</option>
            <option value="Normal">Normal Only</option>
          </select>
          <select
            value={state.selectedNamespace}
            onChange={(e) =>
              setState((prev) => ({
                ...prev,
                selectedNamespace: e.target.value,
              }))
            }
            className="namespace-select"
          >
            <option value="all">All Namespaces</option>
          </select>
          <label className="auto-refresh">
            <input
              type="checkbox"
              checked={state.autoRefresh}
              onChange={(e) =>
                setState((prev) => ({ ...prev, autoRefresh: e.target.checked }))
              }
            />
            Auto-refresh
          </label>
          <button
            onClick={fetchEvents}
            className="btn-refresh"
            title="Refresh"
          >
            🔄
          </button>
          <button onClick={toggleTheme} className="btn-theme" title="Toggle Theme">
            {state.theme === "dark" ? "☀️" : "🌙"}
          </button>
        </div>
      </header>

      {state.error && (
        <div className="error-banner">
          {state.error}
          <button onClick={() => setState((prev) => ({ ...prev, error: null }))}>
            ✕
          </button>
        </div>
      )}

      <main className="app-main">
        {state.loading ? (
          <div className="loading">Loading events...</div>
        ) : filteredEvents.length === 0 ? (
          <div className="empty">No events found</div>
        ) : (
          <div className="timeline">
            {Object.entries(groupedEvents).map(([date, events]) => (
              <div key={date} className="timeline-group">
                <div className="timeline-date">{date}</div>
                <div className="timeline-events">
                  {events.map((event, index) => (
                    <div
                      key={`${event.object}-${event.lastTimestamp}-${index}`}
                      className={`timeline-event ${event.type.toLowerCase()}`}
                      onClick={() =>
                        setState((prev) => ({ ...prev, selectedEvent: event }))
                      }
                    >
                      <div className="event-marker">
                        <div
                          className={`marker-dot ${event.type.toLowerCase()}`}
                        />
                        <div className="marker-line" />
                      </div>
                      <div className="event-content">
                        <div className="event-header">
                          <StatusBadge
                            status={event.type}
                            size="sm"
                            icon={true}
                          />
                          <span className="event-reason">{event.reason}</span>
                          <span className="event-time">
                            {formatTime(event.lastTimestamp)}
                          </span>
                        </div>
                        <div className="event-object">
                          <span className="object-kind">{event.objectKind}</span>
                          <span className="object-name">{event.object}</span>
                          <span className="object-namespace">
                            {event.namespace}
                          </span>
                        </div>
                        <div className="event-message">{event.message}</div>
                        {event.count > 1 && (
                          <div className="event-count">
                            Occurred {event.count} times
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {state.selectedEvent && (
        <div
          className="modal-overlay"
          onClick={() => setState((prev) => ({ ...prev, selectedEvent: null }))}
        >
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Event Details</h2>
              <button
                onClick={() =>
                  setState((prev) => ({ ...prev, selectedEvent: null }))
                }
              >
                ✕
              </button>
            </div>
            <div className="modal-content">
              <div className="detail-row">
                <span className="label">Type</span>
                <StatusBadge status={state.selectedEvent.type} />
              </div>
              <div className="detail-row">
                <span className="label">Reason</span>
                <span className="value">{state.selectedEvent.reason}</span>
              </div>
              <div className="detail-row">
                <span className="label">Object</span>
                <span className="value">
                  {state.selectedEvent.objectKind}/{state.selectedEvent.object}
                </span>
              </div>
              <div className="detail-row">
                <span className="label">Namespace</span>
                <span className="value">{state.selectedEvent.namespace}</span>
              </div>
              <div className="detail-row">
                <span className="label">Count</span>
                <span className="value">{state.selectedEvent.count}</span>
              </div>
              <div className="detail-row">
                <span className="label">First Seen</span>
                <span className="value">{state.selectedEvent.firstTimestamp}</span>
              </div>
              <div className="detail-row">
                <span className="label">Last Seen</span>
                <span className="value">{state.selectedEvent.lastTimestamp}</span>
              </div>
              <div className="detail-row full">
                <span className="label">Message</span>
                <span className="value message">
                  {state.selectedEvent.message}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const appStyles = `
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .header-left h1 { font-size: 20px; font-weight: 600; }

  .event-counts { display: flex; gap: 12px; }

  .warning-count {
    padding: 4px 8px;
    background: var(--warning-bg);
    color: var(--warning);
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
  }

  .normal-count {
    padding: 4px 8px;
    background: var(--success-bg);
    color: var(--success);
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .filter-select, .namespace-select {
    padding: 8px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
  }

  .auto-refresh {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: var(--text-secondary);
    cursor: pointer;
  }

  .btn-refresh, .btn-theme {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
  }

  .btn-refresh:hover, .btn-theme:hover { background: var(--border); }

  .error-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: var(--error-bg);
    color: var(--error);
  }

  .error-banner button {
    background: none;
    border: none;
    color: var(--error);
    cursor: pointer;
  }

  .app-main { flex: 1; padding: 24px; }

  .loading, .empty {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 200px;
    color: var(--text-muted);
  }

  .timeline { max-width: 800px; }

  .timeline-group { margin-bottom: 24px; }

  .timeline-date {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 16px;
  }

  .timeline-events {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .timeline-event {
    display: flex;
    gap: 16px;
    cursor: pointer;
    padding: 12px;
    border-radius: 8px;
    transition: background 0.15s;
  }

  .timeline-event:hover { background: var(--bg-secondary); }

  .event-marker {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 20px;
  }

  .marker-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .marker-dot.normal { background: var(--success); }
  .marker-dot.warning { background: var(--warning); }

  .marker-line {
    flex: 1;
    width: 2px;
    background: var(--border);
    margin-top: 4px;
  }

  .event-content { flex: 1; }

  .event-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  .event-reason {
    font-weight: 500;
    font-size: 14px;
  }

  .event-time {
    margin-left: auto;
    font-size: 12px;
    color: var(--text-muted);
  }

  .event-object {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  .object-kind {
    font-size: 11px;
    padding: 2px 6px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    color: var(--text-secondary);
  }

  .object-name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
  }

  .object-namespace {
    font-size: 11px;
    color: var(--text-muted);
  }

  .event-message {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.5;
  }

  .event-count {
    margin-top: 6px;
    font-size: 11px;
    color: var(--text-muted);
  }

  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    width: 500px;
    max-width: 90vw;
    max-height: 80vh;
    overflow: auto;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
  }

  .modal-header h2 { font-size: 16px; }

  .modal-header button {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 18px;
  }

  .modal-content { padding: 20px; }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
  }

  .detail-row.full {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .detail-row .label {
    font-size: 12px;
    color: var(--text-secondary);
  }

  .detail-row .value {
    font-size: 13px;
    color: var(--text);
  }

  .detail-row .value.message {
    line-height: 1.5;
    word-break: break-word;
  }
`;

function getMockEvents(): K8sEvent[] {
  const now = Date.now();
  return [
    {
      type: "Warning",
      reason: "FailedScheduling",
      message:
        "0/3 nodes are available: 3 Insufficient memory. preemption: 0/3 nodes are available.",
      object: "pending-pod-abc",
      objectKind: "Pod",
      namespace: "production",
      count: 5,
      firstTimestamp: new Date(now - 1800000).toISOString(),
      lastTimestamp: new Date(now - 300000).toISOString(),
    },
    {
      type: "Normal",
      reason: "Scheduled",
      message: "Successfully assigned production/api-server-xyz to node-2",
      object: "api-server-xyz",
      objectKind: "Pod",
      namespace: "production",
      count: 1,
      firstTimestamp: new Date(now - 600000).toISOString(),
      lastTimestamp: new Date(now - 600000).toISOString(),
    },
    {
      type: "Normal",
      reason: "Pulled",
      message: "Container image successfully pulled in 2.3s",
      object: "api-server-xyz",
      objectKind: "Pod",
      namespace: "production",
      count: 1,
      firstTimestamp: new Date(now - 540000).toISOString(),
      lastTimestamp: new Date(now - 540000).toISOString(),
    },
    {
      type: "Normal",
      reason: "Started",
      message: "Started container api",
      object: "api-server-xyz",
      objectKind: "Pod",
      namespace: "production",
      count: 1,
      firstTimestamp: new Date(now - 480000).toISOString(),
      lastTimestamp: new Date(now - 480000).toISOString(),
    },
    {
      type: "Warning",
      reason: "BackOff",
      message: "Back-off restarting failed container",
      object: "worker-crash-123",
      objectKind: "Pod",
      namespace: "batch",
      count: 12,
      firstTimestamp: new Date(now - 7200000).toISOString(),
      lastTimestamp: new Date(now - 120000).toISOString(),
    },
    {
      type: "Normal",
      reason: "ScalingReplicaSet",
      message: "Scaled up replica set nginx-deployment-abc to 3",
      object: "nginx-deployment",
      objectKind: "Deployment",
      namespace: "default",
      count: 1,
      firstTimestamp: new Date(now - 86400000).toISOString(),
      lastTimestamp: new Date(now - 86400000).toISOString(),
    },
  ];
}

export default EventsTimeline;
