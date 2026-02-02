import React, { useState, useEffect, useCallback } from "react";
import { Table, StatusBadge, ProgressBar } from "@shared/components";
import type { Column } from "@shared/components";
import { baseStyles, getTheme, setTheme, type Theme } from "@shared/theme";

interface Pod {
  name: string;
  namespace: string;
  status: string;
  phase: string;
  ready: string;
  restarts: number;
  age: string;
  nodeName: string;
  ip: string;
  cpu?: { percentage: number };
  memory?: { percentage: number };
}

interface AppState {
  pods: Pod[];
  namespaces: string[];
  loading: boolean;
  error: string | null;
  selectedNamespace: string;
  searchQuery: string;
  theme: Theme;
  currentPage: number;
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
      labelSelector?: string;
    };
  }
}

export function PodViewer(): React.ReactElement {
  const [state, setState] = useState<AppState>({
    pods: [],
    namespaces: ["all"],
    loading: true,
    error: null,
    selectedNamespace: window.initialArgs?.namespace || "all",
    searchQuery: "",
    theme: getTheme(),
    currentPage: 1,
  });

  const callTool = useCallback(
    async (name: string, args: Record<string, unknown> = {}) => {
      if (!window.callServerTool) {
        console.warn("callServerTool not available, using mock data");
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

  const fetchPods = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const namespace =
        state.selectedNamespace === "all" ? "" : state.selectedNamespace;
      const data = await callTool("get_pods", {
        namespace,
        context: window.initialArgs?.context || "",
        label_selector: window.initialArgs?.labelSelector || "",
      });

      if (data?.pods) {
        setState((prev) => ({ ...prev, pods: data.pods, loading: false }));
      } else {
        setState((prev) => ({
          ...prev,
          pods: getMockPods(),
          loading: false,
        }));
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        pods: getMockPods(),
        loading: false,
        error: error instanceof Error ? error.message : "Failed to fetch pods",
      }));
    }
  }, [callTool, state.selectedNamespace]);

  const fetchNamespaces = useCallback(async () => {
    try {
      const data = await callTool("get_namespaces", {
        context: window.initialArgs?.context || "",
      });
      if (data?.namespaces) {
        const names = data.namespaces.map(
          (ns: { name: string }) => ns.name
        );
        setState((prev) => ({
          ...prev,
          namespaces: ["all", ...names],
        }));
      }
    } catch {
      setState((prev) => ({
        ...prev,
        namespaces: ["all", "default", "kube-system", "kube-public"],
      }));
    }
  }, [callTool]);

  useEffect(() => {
    fetchNamespaces();
    fetchPods();
  }, []);

  useEffect(() => {
    fetchPods();
  }, [state.selectedNamespace]);

  const handleDelete = useCallback(
    async (pod: Pod) => {
      if (!confirm(`Delete pod ${pod.name} in namespace ${pod.namespace}?`)) {
        return;
      }
      try {
        await callTool("delete_pod", {
          name: pod.name,
          namespace: pod.namespace,
          context: window.initialArgs?.context || "",
        });
        fetchPods();
      } catch (error) {
        alert(
          `Failed to delete pod: ${error instanceof Error ? error.message : error}`
        );
      }
    },
    [callTool, fetchPods]
  );

  const handleViewLogs = useCallback((pod: Pod) => {
    const params = new URLSearchParams({
      namespace: pod.namespace,
      pod: pod.name,
    });
    window.open(`logs.html?${params}`, "_blank");
  }, []);

  const toggleTheme = useCallback(() => {
    const newTheme = state.theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    setState((prev) => ({ ...prev, theme: newTheme }));
  }, [state.theme]);

  const filteredPods = state.pods.filter((pod) => {
    if (!state.searchQuery) return true;
    const query = state.searchQuery.toLowerCase();
    return (
      pod.name.toLowerCase().includes(query) ||
      pod.namespace.toLowerCase().includes(query) ||
      pod.status.toLowerCase().includes(query) ||
      pod.nodeName.toLowerCase().includes(query)
    );
  });

  const columns: Column<Pod>[] = [
    {
      key: "name",
      header: "Name",
      width: "25%",
      render: (pod) => (
        <div className="pod-name">
          <span className="name">{pod.name}</span>
          <span className="namespace">{pod.namespace}</span>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      width: "12%",
      render: (pod) => <StatusBadge status={pod.status} />,
    },
    {
      key: "ready",
      header: "Ready",
      width: "8%",
    },
    {
      key: "restarts",
      header: "Restarts",
      width: "8%",
      render: (pod) => (
        <span className={pod.restarts > 5 ? "warning" : ""}>
          {pod.restarts}
        </span>
      ),
    },
    {
      key: "cpu",
      header: "CPU",
      width: "12%",
      sortable: false,
      render: (pod) =>
        pod.cpu ? (
          <ProgressBar
            value={pod.cpu.percentage}
            max={100}
            size="sm"
            showPercentage={false}
          />
        ) : (
          <span className="muted">N/A</span>
        ),
    },
    {
      key: "memory",
      header: "Memory",
      width: "12%",
      sortable: false,
      render: (pod) =>
        pod.memory ? (
          <ProgressBar
            value={pod.memory.percentage}
            max={100}
            size="sm"
            showPercentage={false}
          />
        ) : (
          <span className="muted">N/A</span>
        ),
    },
    {
      key: "age",
      header: "Age",
      width: "8%",
    },
    {
      key: "actions",
      header: "Actions",
      width: "15%",
      sortable: false,
      render: (pod) => (
        <div className="actions">
          <button className="btn-icon" onClick={() => handleViewLogs(pod)} title="View Logs">
            📋
          </button>
          <button
            className="btn-icon danger"
            onClick={() => handleDelete(pod)}
            title="Delete"
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
          <h1>Kubernetes Pods</h1>
          <span className="pod-count">{filteredPods.length} pods</span>
        </div>
        <div className="header-right">
          <input
            type="text"
            placeholder="Search pods..."
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
          <button onClick={fetchPods} className="btn-refresh" title="Refresh">
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
          data={filteredPods}
          columns={columns}
          keyExtractor={(pod) => `${pod.namespace}/${pod.name}`}
          loading={state.loading}
          emptyMessage="No pods found"
          pagination={{
            pageSize: 20,
            currentPage: state.currentPage,
            onPageChange: (page) => setState((prev) => ({ ...prev, currentPage: page })),
          }}
        />
      </main>
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

  .header-left h1 {
    font-size: 20px;
    font-weight: 600;
  }

  .pod-count {
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

  .search-input {
    padding: 8px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    width: 200px;
    outline: none;
  }

  .search-input:focus {
    border-color: var(--primary);
  }

  .namespace-select {
    padding: 8px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    cursor: pointer;
  }

  .btn-refresh,
  .btn-theme {
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

  .btn-refresh:hover,
  .btn-theme:hover {
    background: var(--border);
  }

  .error-banner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: var(--error-bg);
    color: var(--error);
    border-bottom: 1px solid var(--error);
  }

  .error-banner button {
    background: none;
    border: none;
    color: var(--error);
    cursor: pointer;
    font-size: 16px;
  }

  .app-main {
    flex: 1;
    padding: 24px;
  }

  .pod-name {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .pod-name .name {
    font-weight: 500;
  }

  .pod-name .namespace {
    font-size: 11px;
    color: var(--text-muted);
  }

  .warning {
    color: var(--warning);
  }

  .muted {
    color: var(--text-muted);
  }

  .actions {
    display: flex;
    gap: 8px;
  }

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

  .btn-icon:hover {
    background: var(--border);
  }

  .btn-icon.danger:hover {
    background: var(--error-bg);
    border-color: var(--error);
  }
`;

function getMockPods(): Pod[] {
  return [
    {
      name: "nginx-deployment-7c79c4bf97-abcde",
      namespace: "default",
      status: "Running",
      phase: "Running",
      ready: "1/1",
      restarts: 0,
      age: "2d",
      nodeName: "node-1",
      ip: "10.244.0.5",
      cpu: { percentage: 25 },
      memory: { percentage: 40 },
    },
    {
      name: "redis-master-0",
      namespace: "default",
      status: "Running",
      phase: "Running",
      ready: "1/1",
      restarts: 2,
      age: "5d",
      nodeName: "node-2",
      ip: "10.244.1.3",
      cpu: { percentage: 15 },
      memory: { percentage: 60 },
    },
    {
      name: "api-server-5f8b9c7d4-xyz12",
      namespace: "production",
      status: "CrashLoopBackOff",
      phase: "Running",
      ready: "0/1",
      restarts: 15,
      age: "1h",
      nodeName: "node-1",
      ip: "10.244.0.8",
    },
    {
      name: "coredns-558bd4d5db-k8snf",
      namespace: "kube-system",
      status: "Running",
      phase: "Running",
      ready: "1/1",
      restarts: 0,
      age: "30d",
      nodeName: "node-1",
      ip: "10.244.0.2",
      cpu: { percentage: 5 },
      memory: { percentage: 20 },
    },
    {
      name: "pending-job-runner-abc",
      namespace: "batch",
      status: "Pending",
      phase: "Pending",
      ready: "0/1",
      restarts: 0,
      age: "5m",
      nodeName: "",
      ip: "",
    },
  ];
}

export default PodViewer;
