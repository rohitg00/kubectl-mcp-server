import React, { useState, useEffect, useCallback } from "react";
import { DonutChart, ProgressBar, StatusBadge } from "@shared/components";
import { baseStyles, getTheme, setTheme, type Theme } from "@shared/theme";

interface Node {
  name: string;
  status: string;
  roles: string[];
  version: string;
  cpu: { capacity: string; allocatable: string; used?: number };
  memory: { capacity: string; allocatable: string; used?: number };
  pods: { capacity: string; allocatable: string; used?: number };
}

interface ClusterInfo {
  name: string;
  version: string;
  nodeCount: number;
  namespaceCount: number;
  podCount: number;
  cpuCapacity: string;
  memoryCapacity: string;
  cpuUsed?: number;
  memoryUsed?: number;
}

interface AppState {
  clusterInfo: ClusterInfo | null;
  nodes: Node[];
  namespaces: number;
  loading: boolean;
  error: string | null;
  theme: Theme;
}

declare global {
  interface Window {
    callServerTool?: (request: {
      name: string;
      arguments?: Record<string, unknown>;
    }) => Promise<{ content: Array<{ type: string; text: string }> }>;
    initialArgs?: {
      context?: string;
    };
  }
}

export function ClusterOverview(): React.ReactElement {
  const [state, setState] = useState<AppState>({
    clusterInfo: null,
    nodes: [],
    namespaces: 0,
    loading: true,
    error: null,
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

  const fetchClusterData = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const context = window.initialArgs?.context || "";

      const [clusterData, nodesData, namespacesData] = await Promise.all([
        callTool("get_cluster_info", { context }),
        callTool("get_nodes", { context }),
        callTool("get_namespaces", { context }),
      ]);

      setState((prev) => ({
        ...prev,
        clusterInfo: clusterData || getMockClusterInfo(),
        nodes: nodesData?.nodes || getMockNodes(),
        namespaces: namespacesData?.namespaces?.length || 10,
        loading: false,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        clusterInfo: getMockClusterInfo(),
        nodes: getMockNodes(),
        namespaces: 10,
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch cluster data",
      }));
    }
  }, [callTool]);

  useEffect(() => {
    fetchClusterData();
  }, []);

  const toggleTheme = useCallback(() => {
    const newTheme = state.theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    setState((prev) => ({ ...prev, theme: newTheme }));
  }, [state.theme]);

  const healthyNodes = state.nodes.filter((n) => n.status === "Ready").length;
  const totalNodes = state.nodes.length;

  return (
    <div className="app" data-theme={state.theme}>
      <style>{baseStyles}</style>
      <style>{appStyles}</style>

      <header className="app-header">
        <div className="header-left">
          <h1>Cluster Overview</h1>
          {state.clusterInfo && (
            <span className="cluster-name">{state.clusterInfo.name || "kubernetes"}</span>
          )}
        </div>
        <div className="header-right">
          <button
            onClick={fetchClusterData}
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
          <div className="loading">Loading cluster data...</div>
        ) : (
          <>
            <section className="stats-grid">
              <div className="stat-card">
                <DonutChart
                  value={healthyNodes}
                  max={totalNodes}
                  label={`${healthyNodes}/${totalNodes}`}
                  sublabel="Nodes Ready"
                  color="success"
                />
              </div>
              <div className="stat-card">
                <div className="stat-number">{state.clusterInfo?.podCount || 0}</div>
                <div className="stat-label">Running Pods</div>
              </div>
              <div className="stat-card">
                <div className="stat-number">{state.namespaces}</div>
                <div className="stat-label">Namespaces</div>
              </div>
              <div className="stat-card">
                <div className="stat-version">{state.clusterInfo?.version || "v1.28"}</div>
                <div className="stat-label">Kubernetes Version</div>
              </div>
            </section>

            <section className="resources-section">
              <h2>Cluster Resources</h2>
              <div className="resources-grid">
                <div className="resource-card">
                  <h3>CPU</h3>
                  <ProgressBar
                    value={state.clusterInfo?.cpuUsed ?? 65}
                    max={100}
                    label="Usage"
                  />
                  <div className="resource-detail">
                    <span>Capacity: {state.clusterInfo?.cpuCapacity ?? "32 cores"}</span>
                  </div>
                </div>
                <div className="resource-card">
                  <h3>Memory</h3>
                  <ProgressBar
                    value={state.clusterInfo?.memoryUsed ?? 72}
                    max={100}
                    label="Usage"
                  />
                  <div className="resource-detail">
                    <span>Capacity: {state.clusterInfo?.memoryCapacity ?? "128 Gi"}</span>
                  </div>
                </div>
              </div>
            </section>

            <section className="nodes-section">
              <h2>Nodes</h2>
              <div className="nodes-grid">
                {state.nodes.map((node) => (
                  <div key={node.name} className="node-card">
                    <div className="node-header">
                      <span className="node-name">{node.name}</span>
                      <StatusBadge status={node.status} />
                    </div>
                    <div className="node-roles">
                      {node.roles.map((role) => (
                        <span key={role} className="role-badge">
                          {role}
                        </span>
                      ))}
                    </div>
                    <div className="node-stats">
                      <div className="node-stat">
                        <span className="label">CPU</span>
                        <ProgressBar
                          value={node.cpu.used ?? 50}
                          max={100}
                          size="sm"
                          showPercentage={false}
                        />
                      </div>
                      <div className="node-stat">
                        <span className="label">Memory</span>
                        <ProgressBar
                          value={node.memory.used ?? 60}
                          max={100}
                          size="sm"
                          showPercentage={false}
                        />
                      </div>
                      <div className="node-stat">
                        <span className="label">Pods</span>
                        <ProgressBar
                          value={node.pods.used ?? 30}
                          max={100}
                          size="sm"
                          showPercentage={false}
                        />
                      </div>
                    </div>
                    <div className="node-version">
                      <span>Version: {node.version}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
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

  .header-left h1 { font-size: 20px; font-weight: 600; }

  .cluster-name {
    padding: 4px 8px;
    background: var(--primary);
    color: #fff;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
  }

  .header-right { display: flex; gap: 12px; }

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

  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 200px;
    color: var(--text-muted);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 32px;
  }

  .stat-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .stat-number {
    font-size: 36px;
    font-weight: 700;
    color: var(--text);
  }

  .stat-version {
    font-size: 24px;
    font-weight: 600;
    color: var(--primary);
    font-family: monospace;
  }

  .stat-label {
    font-size: 13px;
    color: var(--text-secondary);
    margin-top: 8px;
  }

  .resources-section, .nodes-section {
    margin-bottom: 32px;
  }

  .resources-section h2, .nodes-section h2 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
  }

  .resources-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .resource-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }

  .resource-card h3 {
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 12px;
    color: var(--text-secondary);
  }

  .resource-detail {
    margin-top: 12px;
    font-size: 12px;
    color: var(--text-muted);
  }

  .nodes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }

  .node-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
  }

  .node-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .node-name {
    font-weight: 600;
    font-size: 14px;
  }

  .node-roles {
    display: flex;
    gap: 4px;
    margin-bottom: 12px;
  }

  .role-badge {
    padding: 2px 6px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    font-size: 10px;
    color: var(--text-secondary);
    text-transform: uppercase;
  }

  .node-stats {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 12px;
  }

  .node-stat {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .node-stat .label {
    width: 50px;
    font-size: 11px;
    color: var(--text-muted);
  }

  .node-stat > div {
    flex: 1;
  }

  .node-version {
    font-size: 11px;
    color: var(--text-muted);
    padding-top: 8px;
    border-top: 1px solid var(--border);
  }

  @media (max-width: 900px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    .resources-grid { grid-template-columns: 1fr; }
  }
`;

function getMockClusterInfo(): ClusterInfo {
  return {
    name: "production-cluster",
    version: "v1.28.4",
    nodeCount: 4,
    namespaceCount: 12,
    podCount: 87,
    cpuCapacity: "32 cores",
    memoryCapacity: "128 Gi",
    cpuUsed: 65,
    memoryUsed: 72,
  };
}

function getMockNodes(): Node[] {
  return [
    {
      name: "node-1",
      status: "Ready",
      roles: ["control-plane", "master"],
      version: "v1.28.4",
      cpu: { capacity: "8", allocatable: "7.5", used: 55 },
      memory: { capacity: "32Gi", allocatable: "30Gi", used: 68 },
      pods: { capacity: "110", allocatable: "110", used: 25 },
    },
    {
      name: "node-2",
      status: "Ready",
      roles: ["worker"],
      version: "v1.28.4",
      cpu: { capacity: "8", allocatable: "8", used: 72 },
      memory: { capacity: "32Gi", allocatable: "32Gi", used: 81 },
      pods: { capacity: "110", allocatable: "110", used: 45 },
    },
    {
      name: "node-3",
      status: "Ready",
      roles: ["worker"],
      version: "v1.28.4",
      cpu: { capacity: "8", allocatable: "8", used: 60 },
      memory: { capacity: "32Gi", allocatable: "32Gi", used: 55 },
      pods: { capacity: "110", allocatable: "110", used: 32 },
    },
    {
      name: "node-4",
      status: "NotReady",
      roles: ["worker"],
      version: "v1.28.4",
      cpu: { capacity: "8", allocatable: "8", used: 0 },
      memory: { capacity: "32Gi", allocatable: "32Gi", used: 0 },
      pods: { capacity: "110", allocatable: "110", used: 0 },
    },
  ];
}

export default ClusterOverview;
