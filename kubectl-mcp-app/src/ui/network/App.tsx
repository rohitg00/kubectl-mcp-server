import React, { useState, useEffect, useCallback } from "react";
import { ResourceGraph, StatusBadge } from "@shared/components";
import type { GraphNode, GraphEdge } from "@shared/components";
import { baseStyles, getTheme, setTheme, type Theme } from "@shared/theme";

interface NetworkResource {
  kind: string;
  name: string;
  namespace: string;
  labels?: Record<string, string>;
  selector?: Record<string, string>;
  ports?: Array<{ port: number; targetPort: number; protocol: string }>;
  endpoints?: string[];
  hosts?: string[];
  clusterIP?: string;
  externalIP?: string;
  type?: string;
}

interface AppState {
  services: NetworkResource[];
  pods: NetworkResource[];
  ingresses: NetworkResource[];
  loading: boolean;
  error: string | null;
  selectedNamespace: string;
  selectedNode: GraphNode | null;
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

export function NetworkTopology(): React.ReactElement {
  const [state, setState] = useState<AppState>({
    services: [],
    pods: [],
    ingresses: [],
    loading: true,
    error: null,
    selectedNamespace: window.initialArgs?.namespace || "default",
    selectedNode: null,
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

  const fetchNetworkData = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const namespace = state.selectedNamespace;
      const context = window.initialArgs?.context || "";

      const [servicesData, podsData, ingressesData] = await Promise.all([
        callTool("get_services", { namespace, context }),
        callTool("get_pods", { namespace, context }),
        callTool("get_ingresses", { namespace, context }),
      ]);

      setState((prev) => ({
        ...prev,
        services: servicesData?.services || getMockServices(),
        pods: podsData?.pods || getMockPods(),
        ingresses: ingressesData?.ingresses || getMockIngresses(),
        loading: false,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        services: getMockServices(),
        pods: getMockPods(),
        ingresses: getMockIngresses(),
        loading: false,
        error:
          error instanceof Error
            ? error.message
            : "Failed to fetch network data",
      }));
    }
  }, [callTool, state.selectedNamespace]);

  useEffect(() => {
    fetchNetworkData();
  }, []);

  useEffect(() => {
    fetchNetworkData();
  }, [state.selectedNamespace]);

  const toggleTheme = useCallback(() => {
    const newTheme = state.theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    setState((prev) => ({ ...prev, theme: newTheme }));
  }, [state.theme]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    setState((prev) => ({ ...prev, selectedNode: node }));
  }, []);

  const buildGraphData = useCallback((): {
    nodes: GraphNode[];
    edges: GraphEdge[];
  } => {
    const nodes: GraphNode[] = [];
    const edges: GraphEdge[] = [];

    state.ingresses.forEach((ingress) => {
      nodes.push({
        id: `ingress-${ingress.name}`,
        type: "Ingress",
        label: ingress.name,
        namespace: ingress.namespace,
      });
    });

    state.services.forEach((service) => {
      nodes.push({
        id: `service-${service.name}`,
        type: "Service",
        label: service.name,
        namespace: service.namespace,
        labels: service.labels,
      });

      state.ingresses.forEach((ingress) => {
        const matchesEndpoint = ingress.endpoints?.includes(service.name);
        if (matchesEndpoint) {
          edges.push({
            source: `ingress-${ingress.name}`,
            target: `service-${service.name}`,
          });
        }
      });
    });

    state.pods.forEach((pod) => {
      nodes.push({
        id: `pod-${pod.name}`,
        type: "Pod",
        label: pod.name.length > 20 ? pod.name.slice(0, 17) + "..." : pod.name,
        namespace: pod.namespace,
        labels: pod.labels,
      });

      state.services.forEach((service) => {
        if (service.selector) {
          const matches = Object.entries(service.selector).every(
            ([key, value]) => pod.labels?.[key] === value
          );
          if (matches) {
            edges.push({
              source: `service-${service.name}`,
              target: `pod-${pod.name}`,
              port: service.ports?.[0]?.port,
            });
          }
        }
      });
    });

    return { nodes, edges };
  }, [state.services, state.pods, state.ingresses]);

  const { nodes, edges } = buildGraphData();

  const getResourceDetails = (node: GraphNode | null) => {
    if (!node) return null;

    const [type, name] = node.id.split("-").slice(0, 1).concat(node.id.split("-").slice(1).join("-"));

    if (type === "service") {
      return state.services.find((s) => s.name === name);
    } else if (type === "pod") {
      return state.pods.find((p) => p.name === name);
    } else if (type === "ingress") {
      return state.ingresses.find((i) => i.name === name);
    }
    return null;
  };

  const selectedResource = getResourceDetails(state.selectedNode);

  return (
    <div className="app" data-theme={state.theme}>
      <style>{baseStyles}</style>
      <style>{appStyles}</style>

      <header className="app-header">
        <div className="header-left">
          <h1>Network Topology</h1>
          <div className="resource-counts">
            <span>{state.ingresses.length} Ingresses</span>
            <span>{state.services.length} Services</span>
            <span>{state.pods.length} Pods</span>
          </div>
        </div>
        <div className="header-right">
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
            <option value="default">default</option>
            <option value="kube-system">kube-system</option>
            <option value="production">production</option>
            <option value="staging">staging</option>
          </select>
          <button
            onClick={fetchNetworkData}
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
          <div className="loading">Loading network topology...</div>
        ) : (
          <div className="content-grid">
            <div className="graph-container">
              <ResourceGraph
                nodes={nodes}
                edges={edges}
                width={Math.max(600, window.innerWidth - 400)}
                height={Math.max(400, window.innerHeight - 200)}
                onNodeClick={handleNodeClick}
                selectedNodeId={state.selectedNode?.id}
              />
            </div>

            <div className="details-panel">
              {state.selectedNode ? (
                <>
                  <div className="details-header">
                    <h2>{state.selectedNode.label}</h2>
                    <StatusBadge status={state.selectedNode.type} type="info" />
                  </div>

                  {selectedResource && (
                    <div className="details-content">
                      <div className="detail-row">
                        <span className="label">Namespace</span>
                        <span className="value">
                          {selectedResource.namespace}
                        </span>
                      </div>

                      {selectedResource.type && (
                        <div className="detail-row">
                          <span className="label">Type</span>
                          <span className="value">{selectedResource.type}</span>
                        </div>
                      )}

                      {selectedResource.clusterIP && (
                        <div className="detail-row">
                          <span className="label">Cluster IP</span>
                          <span className="value mono">
                            {selectedResource.clusterIP}
                          </span>
                        </div>
                      )}

                      {selectedResource.externalIP && (
                        <div className="detail-row">
                          <span className="label">External IP</span>
                          <span className="value mono">
                            {selectedResource.externalIP}
                          </span>
                        </div>
                      )}

                      {selectedResource.ports &&
                        selectedResource.ports.length > 0 && (
                          <div className="detail-section">
                            <h3>Ports</h3>
                            <div className="ports-list">
                              {selectedResource.ports.map((port, i) => (
                                <div key={i} className="port-item">
                                  <span className="port-number">
                                    {port.port}
                                  </span>
                                  <span className="port-arrow">→</span>
                                  <span className="port-target">
                                    {port.targetPort}
                                  </span>
                                  <span className="port-protocol">
                                    {port.protocol}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                      {selectedResource.hosts &&
                        selectedResource.hosts.length > 0 && (
                          <div className="detail-section">
                            <h3>Hosts</h3>
                            <div className="hosts-list">
                              {selectedResource.hosts.map((host, i) => (
                                <div key={i} className="host-item">
                                  {host}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                      {selectedResource.selector && (
                        <div className="detail-section">
                          <h3>Selector</h3>
                          <div className="labels-list">
                            {Object.entries(selectedResource.selector).map(
                              ([key, value]) => (
                                <div key={key} className="label-item">
                                  <span className="label-key">{key}</span>
                                  <span className="label-value">{value}</span>
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      )}

                      {selectedResource.labels && (
                        <div className="detail-section">
                          <h3>Labels</h3>
                          <div className="labels-list">
                            {Object.entries(selectedResource.labels)
                              .slice(0, 5)
                              .map(([key, value]) => (
                                <div key={key} className="label-item">
                                  <span className="label-key">{key}</span>
                                  <span className="label-value">{value}</span>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <div className="details-empty">
                  <p>Click on a node to view details</p>
                </div>
              )}
            </div>
          </div>
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
    gap: 16px;
  }

  .header-left h1 { font-size: 20px; font-weight: 600; }

  .resource-counts {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .header-right { display: flex; gap: 12px; }

  .namespace-select {
    padding: 8px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
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

  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 400px;
    color: var(--text-muted);
  }

  .content-grid {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 24px;
    height: calc(100vh - 140px);
  }

  .graph-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
  }

  .details-panel {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    overflow-y: auto;
  }

  .details-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
  }

  .details-header h2 {
    font-size: 16px;
    font-weight: 600;
    word-break: break-word;
  }

  .details-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .detail-row .label {
    font-size: 12px;
    color: var(--text-secondary);
  }

  .detail-row .value {
    font-size: 13px;
    color: var(--text);
    text-align: right;
  }

  .detail-row .value.mono {
    font-family: monospace;
    font-size: 12px;
  }

  .detail-section {
    margin-top: 8px;
  }

  .detail-section h3 {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .ports-list, .hosts-list, .labels-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .port-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    font-size: 12px;
  }

  .port-number { font-weight: 500; color: var(--primary); }
  .port-arrow { color: var(--text-muted); }
  .port-target { color: var(--text); }
  .port-protocol {
    margin-left: auto;
    color: var(--text-muted);
    font-size: 10px;
  }

  .host-item {
    padding: 6px 8px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    font-size: 12px;
    font-family: monospace;
  }

  .label-item {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .label-key {
    padding: 2px 6px;
    background: var(--primary);
    color: #fff;
    border-radius: 4px 0 0 4px;
    font-size: 11px;
    font-family: monospace;
  }

  .label-value {
    padding: 2px 6px;
    background: var(--bg-tertiary);
    border-radius: 0 4px 4px 0;
    font-size: 11px;
    font-family: monospace;
  }

  .details-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 200px;
    color: var(--text-muted);
    text-align: center;
  }

  @media (max-width: 900px) {
    .content-grid {
      grid-template-columns: 1fr;
      grid-template-rows: 1fr auto;
    }

    .details-panel {
      max-height: 300px;
    }
  }
`;

function getMockServices(): NetworkResource[] {
  return [
    {
      kind: "Service",
      name: "nginx-service",
      namespace: "default",
      type: "ClusterIP",
      clusterIP: "10.96.0.100",
      selector: { app: "nginx" },
      ports: [{ port: 80, targetPort: 80, protocol: "TCP" }],
      labels: { app: "nginx", tier: "frontend" },
    },
    {
      kind: "Service",
      name: "api-service",
      namespace: "default",
      type: "ClusterIP",
      clusterIP: "10.96.0.101",
      selector: { app: "api" },
      ports: [{ port: 8080, targetPort: 8080, protocol: "TCP" }],
      labels: { app: "api", tier: "backend" },
    },
    {
      kind: "Service",
      name: "redis-service",
      namespace: "default",
      type: "ClusterIP",
      clusterIP: "10.96.0.102",
      selector: { app: "redis" },
      ports: [{ port: 6379, targetPort: 6379, protocol: "TCP" }],
      labels: { app: "redis", tier: "cache" },
    },
  ];
}

function getMockPods(): NetworkResource[] {
  return [
    {
      kind: "Pod",
      name: "nginx-abc123",
      namespace: "default",
      labels: { app: "nginx", tier: "frontend" },
    },
    {
      kind: "Pod",
      name: "nginx-def456",
      namespace: "default",
      labels: { app: "nginx", tier: "frontend" },
    },
    {
      kind: "Pod",
      name: "api-xyz789",
      namespace: "default",
      labels: { app: "api", tier: "backend" },
    },
    {
      kind: "Pod",
      name: "api-uvw012",
      namespace: "default",
      labels: { app: "api", tier: "backend" },
    },
    {
      kind: "Pod",
      name: "redis-master-0",
      namespace: "default",
      labels: { app: "redis", tier: "cache" },
    },
  ];
}

function getMockIngresses(): NetworkResource[] {
  return [
    {
      kind: "Ingress",
      name: "main-ingress",
      namespace: "default",
      hosts: ["app.example.com", "api.example.com"],
      endpoints: ["nginx-service", "api-service"],
    },
  ];
}

export default NetworkTopology;
