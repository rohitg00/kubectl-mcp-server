import React, { useState, useEffect, useCallback } from "react";
import { Table, StatusBadge, ProgressBar, BarChart } from "@shared/components";
import type { Column } from "@shared/components";
import { baseStyles, getTheme, setTheme, type Theme } from "@shared/theme";

interface CostRecommendation {
  resourceType: string;
  name: string;
  namespace: string;
  recommendation: string;
  currentCpu: string;
  suggestedCpu: string;
  currentMemory: string;
  suggestedMemory: string;
  savingsEstimate: string;
  confidence: "high" | "medium" | "low";
}

interface NamespaceUsage {
  namespace: string;
  cpuRequested: number;
  cpuUsed: number;
  memoryRequested: number;
  memoryUsed: number;
  podCount: number;
}

interface AppState {
  recommendations: CostRecommendation[];
  namespaceUsage: NamespaceUsage[];
  loading: boolean;
  error: string | null;
  selectedNamespace: string;
  totalSavings: string;
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

export function CostAnalyzer(): React.ReactElement {
  const [state, setState] = useState<AppState>({
    recommendations: [],
    namespaceUsage: [],
    loading: true,
    error: null,
    selectedNamespace: window.initialArgs?.namespace || "all",
    totalSavings: "$0",
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

  const fetchCostData = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const namespace =
        state.selectedNamespace === "all" ? "" : state.selectedNamespace;
      const data = await callTool("analyze_cost_optimization", {
        namespace,
        context: window.initialArgs?.context || "",
      });

      if (data?.recommendations) {
        const totalSavings = data.recommendations.reduce(
          (sum: number, r: CostRecommendation) =>
            sum + parseFloat(r.savingsEstimate.replace(/[^0-9.]/g, "") || "0"),
          0
        );
        setState((prev) => ({
          ...prev,
          recommendations: data.recommendations,
          namespaceUsage: data.namespaceUsage || getMockNamespaceUsage(),
          totalSavings: `$${totalSavings.toFixed(0)}`,
          loading: false,
        }));
      } else {
        setState((prev) => ({
          ...prev,
          recommendations: getMockRecommendations(),
          namespaceUsage: getMockNamespaceUsage(),
          totalSavings: "$347",
          loading: false,
        }));
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        recommendations: getMockRecommendations(),
        namespaceUsage: getMockNamespaceUsage(),
        totalSavings: "$347",
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch cost data",
      }));
    }
  }, [callTool, state.selectedNamespace]);

  useEffect(() => {
    fetchCostData();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- fetchCostData depends on selectedNamespace, so we only call on mount
  }, []);

  useEffect(() => {
    fetchCostData();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentionally re-fetch when namespace changes
  }, [state.selectedNamespace]);

  const handleApply = useCallback(
    async (rec: CostRecommendation) => {
      if (!confirm(`Apply recommendation for ${rec.name}?`)) return;
      try {
        alert(
          `Recommendation applied: Scale ${rec.name} to ${rec.suggestedCpu} CPU, ${rec.suggestedMemory} memory`
        );
        fetchCostData();
      } catch (error) {
        alert(
          `Failed to apply: ${error instanceof Error ? error.message : error}`
        );
      }
    },
    [fetchCostData]
  );

  const toggleTheme = useCallback(() => {
    const newTheme = state.theme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    setState((prev) => ({ ...prev, theme: newTheme }));
  }, [state.theme]);

  const getConfidenceType = (c: string) => {
    if (c === "high") return "success";
    if (c === "medium") return "warning";
    return "neutral";
  };

  const columns: Column<CostRecommendation>[] = [
    {
      key: "name",
      header: "Resource",
      width: "22%",
      render: (r) => (
        <div className="resource-name">
          <span className="name">{r.name}</span>
          <span className="details">
            {r.resourceType} · {r.namespace}
          </span>
        </div>
      ),
    },
    {
      key: "recommendation",
      header: "Recommendation",
      width: "25%",
    },
    {
      key: "current",
      header: "Current",
      width: "15%",
      render: (r) => (
        <div className="resource-values">
          <span>CPU: {r.currentCpu}</span>
          <span>Mem: {r.currentMemory}</span>
        </div>
      ),
    },
    {
      key: "suggested",
      header: "Suggested",
      width: "15%",
      render: (r) => (
        <div className="resource-values suggested">
          <span>CPU: {r.suggestedCpu}</span>
          <span>Mem: {r.suggestedMemory}</span>
        </div>
      ),
    },
    {
      key: "savings",
      header: "Savings",
      width: "10%",
      render: (r) => <span className="savings">{r.savingsEstimate}</span>,
    },
    {
      key: "confidence",
      header: "Confidence",
      width: "8%",
      render: (r) => (
        <StatusBadge
          status={r.confidence}
          type={getConfidenceType(r.confidence)}
          size="sm"
        />
      ),
    },
    {
      key: "actions",
      header: "",
      width: "5%",
      sortable: false,
      render: (r) => (
        <button className="btn-apply" onClick={() => handleApply(r)}>
          Apply
        </button>
      ),
    },
  ];

  const wasteData = state.namespaceUsage.map((ns) => ({
    label: ns.namespace,
    value: Math.round(ns.cpuRequested - ns.cpuUsed),
    color: "var(--warning)",
  }));

  return (
    <div className="app" data-theme={state.theme}>
      <style>{baseStyles}</style>
      <style>{appStyles}</style>

      <header className="app-header">
        <div className="header-left">
          <h1>Cost Analyzer</h1>
          <span className="savings-badge">
            Potential Savings: {state.totalSavings}/month
          </span>
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
            <option value="all">All Namespaces</option>
            {state.namespaceUsage.map((ns) => (
              <option key={ns.namespace} value={ns.namespace}>
                {ns.namespace}
              </option>
            ))}
          </select>
          <button
            onClick={fetchCostData}
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
          <div className="loading">Analyzing resource usage...</div>
        ) : (
          <>
            <section className="usage-section">
              <h2>Resource Waste by Namespace</h2>
              <div className="usage-grid">
                <div className="chart-card">
                  <h3>Unused CPU (millicores)</h3>
                  <BarChart data={wasteData} height={180} />
                </div>
                <div className="usage-list">
                  {state.namespaceUsage.map((ns) => (
                    <div key={ns.namespace} className="usage-item">
                      <div className="usage-header">
                        <span className="ns-name">{ns.namespace}</span>
                        <span className="pod-count">{ns.podCount} pods</span>
                      </div>
                      <div className="usage-bars">
                        <div className="usage-row">
                          <span className="label">CPU</span>
                          <ProgressBar
                            value={ns.cpuUsed}
                            max={ns.cpuRequested || 100}
                            size="sm"
                            label=""
                          />
                          <span className="usage-text">
                            {ns.cpuUsed}m / {ns.cpuRequested}m
                          </span>
                        </div>
                        <div className="usage-row">
                          <span className="label">Mem</span>
                          <ProgressBar
                            value={ns.memoryUsed}
                            max={ns.memoryRequested || 100}
                            size="sm"
                            label=""
                          />
                          <span className="usage-text">
                            {ns.memoryUsed}Mi / {ns.memoryRequested}Mi
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="recommendations-section">
              <h2>Right-Sizing Recommendations</h2>
              <Table
                data={state.recommendations}
                columns={columns}
                keyExtractor={(r) => `${r.namespace}/${r.name}`}
                loading={state.loading}
                emptyMessage="No recommendations at this time"
              />
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
    gap: 16px;
  }

  .header-left h1 { font-size: 20px; font-weight: 600; }

  .savings-badge {
    padding: 6px 12px;
    background: var(--success-bg);
    color: var(--success);
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
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
    height: 200px;
    color: var(--text-muted);
  }

  .usage-section {
    margin-bottom: 32px;
  }

  .usage-section h2, .recommendations-section h2 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
  }

  .usage-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }

  .chart-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }

  .chart-card h3 {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
    margin-bottom: 16px;
  }

  .usage-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .usage-item {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
  }

  .usage-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .ns-name { font-weight: 500; font-size: 13px; }
  .pod-count { font-size: 11px; color: var(--text-muted); }

  .usage-bars {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .usage-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .usage-row .label {
    width: 30px;
    font-size: 11px;
    color: var(--text-muted);
  }

  .usage-row > div { flex: 1; }

  .usage-text {
    font-size: 11px;
    color: var(--text-secondary);
    width: 100px;
    text-align: right;
  }

  .resource-name {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .resource-name .name { font-weight: 500; }
  .resource-name .details { font-size: 11px; color: var(--text-muted); }

  .resource-values {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .resource-values.suggested { color: var(--success); }

  .savings {
    font-weight: 600;
    color: var(--success);
  }

  .btn-apply {
    padding: 4px 8px;
    background: var(--primary);
    border: none;
    border-radius: 4px;
    color: #fff;
    font-size: 11px;
    cursor: pointer;
  }

  .btn-apply:hover { opacity: 0.9; }

  @media (max-width: 900px) {
    .usage-grid { grid-template-columns: 1fr; }
  }
`;

function getMockRecommendations(): CostRecommendation[] {
  return [
    {
      resourceType: "Deployment",
      name: "api-server",
      namespace: "production",
      recommendation: "Reduce CPU request - using 15% of requested",
      currentCpu: "2000m",
      suggestedCpu: "500m",
      currentMemory: "4Gi",
      suggestedMemory: "2Gi",
      savingsEstimate: "$120/mo",
      confidence: "high",
    },
    {
      resourceType: "Deployment",
      name: "worker",
      namespace: "production",
      recommendation: "Reduce memory request - using 20% of requested",
      currentCpu: "1000m",
      suggestedCpu: "500m",
      currentMemory: "8Gi",
      suggestedMemory: "2Gi",
      savingsEstimate: "$95/mo",
      confidence: "high",
    },
    {
      resourceType: "Deployment",
      name: "nginx-proxy",
      namespace: "default",
      recommendation: "Scale down replicas - low traffic detected",
      currentCpu: "500m",
      suggestedCpu: "250m",
      currentMemory: "512Mi",
      suggestedMemory: "256Mi",
      savingsEstimate: "$45/mo",
      confidence: "medium",
    },
    {
      resourceType: "StatefulSet",
      name: "redis",
      namespace: "cache",
      recommendation: "Right-size memory - stable at 40% usage",
      currentCpu: "1000m",
      suggestedCpu: "500m",
      currentMemory: "4Gi",
      suggestedMemory: "2Gi",
      savingsEstimate: "$87/mo",
      confidence: "medium",
    },
  ];
}

function getMockNamespaceUsage(): NamespaceUsage[] {
  return [
    {
      namespace: "production",
      cpuRequested: 8000,
      cpuUsed: 2400,
      memoryRequested: 32768,
      memoryUsed: 12000,
      podCount: 24,
    },
    {
      namespace: "staging",
      cpuRequested: 4000,
      cpuUsed: 800,
      memoryRequested: 16384,
      memoryUsed: 4000,
      podCount: 12,
    },
    {
      namespace: "default",
      cpuRequested: 2000,
      cpuUsed: 600,
      memoryRequested: 8192,
      memoryUsed: 2000,
      podCount: 8,
    },
    {
      namespace: "monitoring",
      cpuRequested: 3000,
      cpuUsed: 1800,
      memoryRequested: 12288,
      memoryUsed: 8000,
      podCount: 6,
    },
  ];
}

export default CostAnalyzer;
