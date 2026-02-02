import React, { useState, useEffect, useCallback } from "react";
import { Table, StatusBadge } from "@shared/components";
import type { Column } from "@shared/components";
import { baseStyles, getTheme, setTheme, type Theme } from "@shared/theme";

interface HelmRelease {
  name: string;
  namespace: string;
  revision: number;
  status: string;
  chart: string;
  chartVersion: string;
  appVersion: string;
  updated: string;
}

interface AppState {
  releases: HelmRelease[];
  namespaces: string[];
  loading: boolean;
  error: string | null;
  selectedNamespace: string;
  searchQuery: string;
  selectedRelease: HelmRelease | null;
  detailsOpen: boolean;
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
    };
  }
}

export function HelmManager(): React.ReactElement {
  const [state, setState] = useState<AppState>({
    releases: [],
    namespaces: ["all"],
    loading: true,
    error: null,
    selectedNamespace: window.initialArgs?.namespace || "all",
    searchQuery: "",
    selectedRelease: null,
    detailsOpen: false,
    theme: getTheme(),
  });

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

  const fetchReleases = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const namespace =
        state.selectedNamespace === "all" ? "all" : state.selectedNamespace;
      const data = await callTool("list_helm_releases", {
        namespace,
        context: window.initialArgs?.context || "",
      });

      if (data?.releases !== undefined) {
        setState((prev) => ({
          ...prev,
          releases: data.releases,
          loading: false,
        }));
      } else {
        setState((prev) => ({
          ...prev,
          releases: getMockReleases(),
          loading: false,
        }));
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        releases: getMockReleases(),
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch releases",
      }));
    }
  }, [callTool, state.selectedNamespace]);

  const fetchNamespaces = useCallback(async () => {
    try {
      const data = await callTool("get_namespaces", {
        context: window.initialArgs?.context || "",
      });
      if (data?.namespaces) {
        const names = data.namespaces.map((ns: { name: string }) => ns.name);
        setState((prev) => ({
          ...prev,
          namespaces: ["all", ...names],
        }));
      }
    } catch {
      setState((prev) => ({
        ...prev,
        namespaces: ["all", "default", "kube-system"],
      }));
    }
  }, [callTool]);

  useEffect(() => {
    fetchNamespaces();
    fetchReleases();
  }, []);

  useEffect(() => {
    fetchReleases();
  }, [state.selectedNamespace]);

  const handleRollback = useCallback(
    async (release: HelmRelease) => {
      if (!confirm(`Rollback ${release.name} to previous revision?`)) return;
      try {
        await callTool("rollback_helm_release", {
          name: release.name,
          namespace: release.namespace,
          revision: release.revision - 1,
          context: window.initialArgs?.context || "",
        });
        fetchReleases();
      } catch (error) {
        alert(
          `Failed to rollback: ${error instanceof Error ? error.message : error}`
        );
      }
    },
    [callTool, fetchReleases]
  );

  const handleUninstall = useCallback(
    async (release: HelmRelease) => {
      if (
        !confirm(
          `Uninstall ${release.name}? This will delete all associated resources.`
        )
      )
        return;
      try {
        await callTool("uninstall_helm_release", {
          name: release.name,
          namespace: release.namespace,
          context: window.initialArgs?.context || "",
        });
        fetchReleases();
      } catch (error) {
        alert(
          `Failed to uninstall: ${error instanceof Error ? error.message : error}`
        );
      }
    },
    [callTool, fetchReleases]
  );

  const openDetails = useCallback((release: HelmRelease) => {
    setState((prev) => ({
      ...prev,
      selectedRelease: release,
      detailsOpen: true,
    }));
  }, []);

  const toggleTheme = useCallback(() => {
    const newTheme = state.theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    setState((prev) => ({ ...prev, theme: newTheme }));
  }, [state.theme]);

  const filteredReleases = state.releases.filter((r) => {
    if (!state.searchQuery) return true;
    const query = state.searchQuery.toLowerCase();
    return (
      r.name.toLowerCase().includes(query) ||
      r.namespace.toLowerCase().includes(query) ||
      r.chart.toLowerCase().includes(query)
    );
  });

  const columns: Column<HelmRelease>[] = [
    {
      key: "name",
      header: "Name",
      width: "20%",
      render: (r) => (
        <div className="release-name">
          <span className="name">{r.name}</span>
          <span className="namespace">{r.namespace}</span>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      width: "12%",
      render: (r) => <StatusBadge status={r.status} />,
    },
    {
      key: "chart",
      header: "Chart",
      width: "20%",
      render: (r) => (
        <span className="chart">
          {r.chart}:{r.chartVersion}
        </span>
      ),
    },
    {
      key: "appVersion",
      header: "App Version",
      width: "12%",
    },
    {
      key: "revision",
      header: "Revision",
      width: "8%",
    },
    {
      key: "updated",
      header: "Updated",
      width: "15%",
      render: (r) => (
        <span className="updated" title={r.updated}>
          {formatDate(r.updated)}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      width: "13%",
      sortable: false,
      render: (r) => (
        <div className="actions">
          <button
            className="btn-icon"
            onClick={() => openDetails(r)}
            title="Details"
          >
            ℹ️
          </button>
          <button
            className="btn-icon"
            onClick={() => handleRollback(r)}
            title="Rollback"
            disabled={r.revision <= 1}
          >
            ⏪
          </button>
          <button
            className="btn-icon danger"
            onClick={() => handleUninstall(r)}
            title="Uninstall"
          >
            🗑️
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="app" data-theme={state.theme}>
      <style>{baseStyles}</style>
      <style>{appStyles}</style>

      <header className="app-header">
        <div className="header-left">
          <h1>Helm Releases</h1>
          <span className="count">{filteredReleases.length} releases</span>
        </div>
        <div className="header-right">
          <input
            type="text"
            placeholder="Search releases..."
            value={state.searchQuery}
            onChange={(e) =>
              setState((prev) => ({ ...prev, searchQuery: e.target.value }))
            }
            className="search-input"
          />
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
            {state.namespaces.map((ns) => (
              <option key={ns} value={ns}>
                {ns === "all" ? "All Namespaces" : ns}
              </option>
            ))}
          </select>
          <button
            onClick={fetchReleases}
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
        <Table
          data={filteredReleases}
          columns={columns}
          keyExtractor={(r) => `${r.namespace}/${r.name}`}
          loading={state.loading}
          emptyMessage="No Helm releases found"
        />
      </main>

      {state.detailsOpen && state.selectedRelease && (
        <div className="modal-overlay" onClick={() => setState((prev) => ({ ...prev, detailsOpen: false }))}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{state.selectedRelease.name}</h2>
            <div className="details-grid">
              <div className="detail-row">
                <span className="label">Namespace</span>
                <span className="value">{state.selectedRelease.namespace}</span>
              </div>
              <div className="detail-row">
                <span className="label">Status</span>
                <StatusBadge status={state.selectedRelease.status} />
              </div>
              <div className="detail-row">
                <span className="label">Chart</span>
                <span className="value">
                  {state.selectedRelease.chart}:{state.selectedRelease.chartVersion}
                </span>
              </div>
              <div className="detail-row">
                <span className="label">App Version</span>
                <span className="value">{state.selectedRelease.appVersion}</span>
              </div>
              <div className="detail-row">
                <span className="label">Revision</span>
                <span className="value">{state.selectedRelease.revision}</span>
              </div>
              <div className="detail-row">
                <span className="label">Updated</span>
                <span className="value">{state.selectedRelease.updated}</span>
              </div>
            </div>
            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() => setState((prev) => ({ ...prev, detailsOpen: false }))}
              >
                Close
              </button>
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
    gap: 12px;
  }

  .header-left h1 { font-size: 20px; font-weight: 600; }

  .count {
    padding: 4px 8px;
    background: var(--bg-tertiary);
    border-radius: 12px;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .search-input, .namespace-select {
    padding: 8px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
  }

  .search-input { width: 200px; outline: none; }
  .search-input:focus { border-color: var(--primary); }

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

  .release-name {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .release-name .name { font-weight: 500; }
  .release-name .namespace { font-size: 11px; color: var(--text-muted); }

  .chart {
    font-family: monospace;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .updated { font-size: 12px; color: var(--text-secondary); }

  .actions { display: flex; gap: 6px; }

  .btn-icon {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
  }

  .btn-icon:hover { background: var(--border); }
  .btn-icon:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-icon.danger:hover:not(:disabled) { background: var(--error-bg); border-color: var(--error); }

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
    padding: 24px;
    min-width: 400px;
  }

  .modal h2 { margin-bottom: 16px; }

  .details-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 24px;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-row .label {
    color: var(--text-secondary);
    font-size: 13px;
  }

  .detail-row .value {
    color: var(--text);
    font-weight: 500;
  }

  .modal-actions { display: flex; justify-content: flex-end; }

  .btn-secondary {
    padding: 8px 16px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    cursor: pointer;
    font-weight: 500;
  }

  .btn-secondary:hover { background: var(--border); }
`;

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

function getMockReleases(): HelmRelease[] {
  return [
    {
      name: "nginx-ingress",
      namespace: "ingress-nginx",
      revision: 5,
      status: "deployed",
      chart: "ingress-nginx",
      chartVersion: "4.7.1",
      appVersion: "1.8.1",
      updated: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      name: "prometheus",
      namespace: "monitoring",
      revision: 3,
      status: "deployed",
      chart: "kube-prometheus-stack",
      chartVersion: "48.3.1",
      appVersion: "0.66.0",
      updated: new Date(Date.now() - 172800000).toISOString(),
    },
    {
      name: "redis",
      namespace: "default",
      revision: 1,
      status: "failed",
      chart: "redis",
      chartVersion: "17.15.3",
      appVersion: "7.2.0",
      updated: new Date(Date.now() - 3600000).toISOString(),
    },
  ];
}

export default HelmManager;
