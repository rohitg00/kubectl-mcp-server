import React, { useState, useEffect, useCallback } from "react";
import { Table, StatusBadge, ProgressBar } from "@shared/components";
import type { Column } from "@shared/components";
import { baseStyles, getTheme, setTheme, type Theme } from "@shared/theme";

interface Deployment {
  name: string;
  namespace: string;
  replicas: number;
  readyReplicas: number;
  updatedReplicas: number;
  availableReplicas: number;
  strategy: string;
  age: string;
  image: string;
  conditions?: Array<{ type: string; status: string; reason?: string }>;
}

interface AppState {
  deployments: Deployment[];
  namespaces: string[];
  loading: boolean;
  error: string | null;
  selectedNamespace: string;
  searchQuery: string;
  selectedDeployment: Deployment | null;
  scaleModalOpen: boolean;
  scaleReplicas: number;
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

export function DeploymentDashboard(): React.ReactElement {
  const [state, setState] = useState<AppState>({
    deployments: [],
    namespaces: ["all"],
    loading: true,
    error: null,
    selectedNamespace: window.initialArgs?.namespace || "all",
    searchQuery: "",
    selectedDeployment: null,
    scaleModalOpen: false,
    scaleReplicas: 1,
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

  const fetchDeployments = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const namespace =
        state.selectedNamespace === "all" ? "" : state.selectedNamespace;
      const data = await callTool("get_deployments", {
        namespace,
        context: window.initialArgs?.context || "",
      });

      if (data?.deployments) {
        setState((prev) => ({
          ...prev,
          deployments: data.deployments,
          loading: false,
        }));
      } else {
        setState((prev) => ({
          ...prev,
          deployments: getMockDeployments(),
          loading: false,
        }));
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        deployments: getMockDeployments(),
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch deployments",
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
    fetchDeployments();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fetch on mount only
  }, []);

  useEffect(() => {
    fetchDeployments();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- re-fetch when namespace changes
  }, [state.selectedNamespace]);

  const handleScale = useCallback(
    async (deployment: Deployment, replicas: number) => {
      try {
        await callTool("scale_deployment", {
          name: deployment.name,
          namespace: deployment.namespace,
          replicas,
          context: window.initialArgs?.context || "",
        });
        fetchDeployments();
        setState((prev) => ({ ...prev, scaleModalOpen: false }));
      } catch (error) {
        alert(
          `Failed to scale: ${error instanceof Error ? error.message : error}`
        );
      }
    },
    [callTool, fetchDeployments]
  );

  const handleRestart = useCallback(
    async (deployment: Deployment) => {
      if (!confirm(`Restart deployment ${deployment.name}?`)) return;
      try {
        await callTool("restart_deployment", {
          name: deployment.name,
          namespace: deployment.namespace,
          context: window.initialArgs?.context || "",
        });
        fetchDeployments();
      } catch (error) {
        alert(
          `Failed to restart: ${error instanceof Error ? error.message : error}`
        );
      }
    },
    [callTool, fetchDeployments]
  );

  const handleRollback = useCallback(
    async (deployment: Deployment) => {
      if (!confirm(`Rollback deployment ${deployment.name} to previous revision?`))
        return;
      try {
        await callTool("rollback_deployment", {
          name: deployment.name,
          namespace: deployment.namespace,
          revision: 0,
          context: window.initialArgs?.context || "",
        });
        fetchDeployments();
      } catch (error) {
        alert(
          `Failed to rollback: ${error instanceof Error ? error.message : error}`
        );
      }
    },
    [callTool, fetchDeployments]
  );

  const openScaleModal = useCallback((deployment: Deployment) => {
    setState((prev) => ({
      ...prev,
      selectedDeployment: deployment,
      scaleReplicas: deployment.replicas,
      scaleModalOpen: true,
    }));
  }, []);

  const toggleTheme = useCallback(() => {
    const newTheme = state.theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    setState((prev) => ({ ...prev, theme: newTheme }));
  }, [state.theme]);

  const filteredDeployments = state.deployments.filter((d) => {
    if (!state.searchQuery) return true;
    const query = state.searchQuery.toLowerCase();
    return (
      d.name.toLowerCase().includes(query) ||
      d.namespace.toLowerCase().includes(query) ||
      d.image.toLowerCase().includes(query)
    );
  });

  const getDeploymentStatus = (d: Deployment): string => {
    if (d.replicas === 0) return "Scaled to zero";
    if (d.readyReplicas === d.replicas && d.replicas > 0) return "Running";
    if (d.updatedReplicas < d.replicas) return "Progressing";
    if (d.readyReplicas === 0) return "Failed";
    return "Degraded";
  };

  const columns: Column<Deployment>[] = [
    {
      key: "name",
      header: "Name",
      width: "25%",
      render: (d) => (
        <div className="deployment-name">
          <span className="name">{d.name}</span>
          <span className="namespace">{d.namespace}</span>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      width: "12%",
      render: (d) => <StatusBadge status={getDeploymentStatus(d)} />,
    },
    {
      key: "replicas",
      header: "Replicas",
      width: "15%",
      render: (d) => (
        <div className="replicas">
          <ProgressBar
            value={d.readyReplicas}
            max={d.replicas || 1}
            size="sm"
            showPercentage={false}
            color={d.readyReplicas === d.replicas ? "success" : "warning"}
          />
          <span className="replica-count">
            {d.readyReplicas}/{d.replicas}
          </span>
        </div>
      ),
    },
    {
      key: "strategy",
      header: "Strategy",
      width: "10%",
    },
    {
      key: "image",
      header: "Image",
      width: "20%",
      render: (d) => (
        <span className="image" title={d.image}>
          {d.image.split("/").pop()?.split(":")[0] || d.image}
        </span>
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
      width: "10%",
      sortable: false,
      render: (d) => (
        <div className="actions">
          <button
            className="btn-icon"
            onClick={() => openScaleModal(d)}
            title="Scale"
          >
            ⚖️
          </button>
          <button
            className="btn-icon"
            onClick={() => handleRestart(d)}
            title="Restart"
          >
            🔄
          </button>
          <button
            className="btn-icon"
            onClick={() => handleRollback(d)}
            title="Rollback"
          >
            ⏪
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
          <h1>Deployments</h1>
          <span className="count">{filteredDeployments.length} deployments</span>
        </div>
        <div className="header-right">
          <input
            type="text"
            placeholder="Search deployments..."
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
            onClick={fetchDeployments}
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
          data={filteredDeployments}
          columns={columns}
          keyExtractor={(d) => `${d.namespace}/${d.name}`}
          loading={state.loading}
          emptyMessage="No deployments found"
        />
      </main>

      {state.scaleModalOpen && state.selectedDeployment && (
        <div className="modal-overlay" onClick={() => setState((prev) => ({ ...prev, scaleModalOpen: false }))}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Scale Deployment</h2>
            <p>
              Scaling <strong>{state.selectedDeployment.name}</strong> in{" "}
              {state.selectedDeployment.namespace}
            </p>
            <div className="scale-input">
              <label>Replicas:</label>
              <input
                type="number"
                min="0"
                max="100"
                value={state.scaleReplicas}
                onChange={(e) =>
                  setState((prev) => ({
                    ...prev,
                    scaleReplicas: Number(e.target.value),
                  }))
                }
              />
            </div>
            <div className="modal-actions">
              <button
                className="btn-secondary"
                onClick={() =>
                  setState((prev) => ({ ...prev, scaleModalOpen: false }))
                }
              >
                Cancel
              </button>
              <button
                className="btn-primary"
                onClick={() =>
                  handleScale(state.selectedDeployment!, state.scaleReplicas)
                }
              >
                Scale
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

  .header-left h1 {
    font-size: 20px;
    font-weight: 600;
  }

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

  .app-main {
    flex: 1;
    padding: 24px;
  }

  .deployment-name {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .deployment-name .name { font-weight: 500; }
  .deployment-name .namespace { font-size: 11px; color: var(--text-muted); }

  .replicas {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .replica-count {
    font-size: 11px;
    color: var(--text-secondary);
  }

  .image {
    font-family: monospace;
    font-size: 12px;
    color: var(--text-secondary);
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: block;
  }

  .actions {
    display: flex;
    gap: 6px;
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

  .btn-icon:hover { background: var(--border); }

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
    min-width: 320px;
  }

  .modal h2 {
    margin-bottom: 8px;
  }

  .modal p {
    color: var(--text-secondary);
    margin-bottom: 16px;
  }

  .scale-input {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
  }

  .scale-input input {
    width: 80px;
    padding: 8px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-size: 16px;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }

  .btn-secondary, .btn-primary {
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
  }

  .btn-secondary {
    background: var(--bg-tertiary);
    border: 1px solid var(--border);
    color: var(--text);
  }

  .btn-primary {
    background: var(--primary);
    border: none;
    color: #fff;
  }

  .btn-secondary:hover { background: var(--border); }
  .btn-primary:hover { opacity: 0.9; }
`;

function getMockDeployments(): Deployment[] {
  return [
    {
      name: "nginx-deployment",
      namespace: "default",
      replicas: 3,
      readyReplicas: 3,
      updatedReplicas: 3,
      availableReplicas: 3,
      strategy: "RollingUpdate",
      age: "5d",
      image: "nginx:1.21",
    },
    {
      name: "api-server",
      namespace: "production",
      replicas: 5,
      readyReplicas: 4,
      updatedReplicas: 5,
      availableReplicas: 4,
      strategy: "RollingUpdate",
      age: "2d",
      image: "myapp/api:v2.3.1",
    },
    {
      name: "redis",
      namespace: "default",
      replicas: 1,
      readyReplicas: 1,
      updatedReplicas: 1,
      availableReplicas: 1,
      strategy: "Recreate",
      age: "30d",
      image: "redis:7",
    },
  ];
}

export default DeploymentDashboard;
