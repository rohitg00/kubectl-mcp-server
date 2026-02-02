import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import { KubectlMcpProxy } from "./proxy.js";
import type { KubectlMcpServerConfig } from "./types.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_UI_DIR = path.join(__dirname, "ui");

const RESOURCE_MIME_TYPE = "text/html";

interface UIConfig {
  name: string;
  title: string;
  description: string;
  schema: z.ZodObject<z.ZodRawShape>;
  primaryTool: string;
}

const UI_CONFIGS: Record<string, UIConfig> = {
  pods: {
    name: "k8s-pods",
    title: "Kubernetes Pods",
    description:
      "Interactive pod viewer with filtering, sorting, status indicators, and quick actions (logs, delete, exec)",
    schema: z.object({
      namespace: z.string().optional().describe("Namespace to view (empty for all namespaces)"),
      context: z.string().optional().describe("Kubernetes context to use"),
      labelSelector: z.string().optional().describe("Label selector to filter pods (e.g., app=nginx)"),
    }),
    primaryTool: "get_pods",
  },
  logs: {
    name: "k8s-logs",
    title: "Kubernetes Logs",
    description:
      "Real-time log viewer with syntax highlighting, search, filtering by level, and multi-container support",
    schema: z.object({
      namespace: z.string().describe("Namespace of the pod"),
      pod: z.string().describe("Pod name to view logs for"),
      container: z.string().optional().describe("Container name (optional for single-container pods)"),
      tail: z.number().optional().default(100).describe("Number of lines to show from the end"),
      follow: z.boolean().optional().default(true).describe("Follow log output in real-time"),
    }),
    primaryTool: "get_pod_logs",
  },
  deployments: {
    name: "k8s-deploy",
    title: "Deployment Dashboard",
    description:
      "Deployment management with rollout status, scaling, restart, rollback, and revision history",
    schema: z.object({
      namespace: z.string().optional().describe("Namespace to view (empty for all namespaces)"),
      context: z.string().optional().describe("Kubernetes context to use"),
    }),
    primaryTool: "get_deployments",
  },
  helm: {
    name: "k8s-helm",
    title: "Helm Manager",
    description:
      "Helm release management with upgrade, rollback, uninstall, values diff, and release notes",
    schema: z.object({
      namespace: z.string().optional().describe("Namespace to view (empty for all namespaces)"),
      context: z.string().optional().describe("Kubernetes context to use"),
    }),
    primaryTool: "list_helm_releases",
  },
  cluster: {
    name: "k8s-cluster",
    title: "Cluster Overview",
    description:
      "Cluster health summary with node status, resource allocation, namespace quotas, and storage overview",
    schema: z.object({
      context: z.string().optional().describe("Kubernetes context to use"),
    }),
    primaryTool: "get_cluster_info",
  },
  cost: {
    name: "k8s-cost",
    title: "Cost Analyzer",
    description:
      "Resource utilization analysis with waste detection, right-sizing recommendations, and savings calculator",
    schema: z.object({
      namespace: z.string().optional().describe("Namespace to analyze (empty for all namespaces)"),
      context: z.string().optional().describe("Kubernetes context to use"),
    }),
    primaryTool: "analyze_cost_optimization",
  },
  events: {
    name: "k8s-events",
    title: "Events Timeline",
    description:
      "Event timeline visualization with type filtering, resource grouping, and time range selection",
    schema: z.object({
      namespace: z.string().optional().describe("Namespace to view (empty for all namespaces)"),
      context: z.string().optional().describe("Kubernetes context to use"),
      types: z.string().optional().default("Normal,Warning").describe("Event types to show (Normal, Warning, or both)"),
    }),
    primaryTool: "get_events",
  },
  network: {
    name: "k8s-network",
    title: "Network Topology",
    description:
      "Network topology graph showing Services, Pods, Ingress connections with click-to-inspect details",
    schema: z.object({
      namespace: z.string().optional().describe("Namespace to view (empty for all namespaces)"),
      context: z.string().optional().describe("Kubernetes context to use"),
    }),
    primaryTool: "get_services",
  },
};

export function createServer(config: KubectlMcpServerConfig = {}): McpServer {
  const server = new McpServer({
    name: "kubectl-mcp-app",
    version: "1.0.0",
  });

  const proxy = new KubectlMcpProxy(config);

  for (const [uiName, uiConfig] of Object.entries(UI_CONFIGS)) {
    const resourceUri = `ui://k8s/${uiName}.html`;

    server.tool(
      uiConfig.name,
      uiConfig.description,
      uiConfig.schema.shape,
      async (args) => {
        try {
          const result = await proxy.callTool(
            uiConfig.primaryTool,
            args as Record<string, unknown>
          );
          return {
            content: [
              {
                type: "text" as const,
                text: JSON.stringify({
                  ui: resourceUri,
                  title: uiConfig.title,
                  args,
                  data: result.content[0]?.text
                    ? JSON.parse(result.content[0].text)
                    : null,
                }),
              },
            ],
            _meta: {
              ui: { resourceUri },
            },
          };
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          return {
            content: [
              {
                type: "text" as const,
                text: JSON.stringify({ error: message }),
              },
            ],
            isError: true,
          };
        }
      }
    );

    server.resource(resourceUri, uiConfig.title, async () => {
      const htmlPath = path.join(DIST_UI_DIR, `${uiName}.html`);

      try {
        const html = await fs.readFile(htmlPath, "utf-8");
        return {
          contents: [
            {
              uri: resourceUri,
              mimeType: RESOURCE_MIME_TYPE,
              text: html,
            },
          ],
        };
      } catch {
        const fallbackHtml = generateFallbackHtml(uiConfig);
        return {
          contents: [
            {
              uri: resourceUri,
              mimeType: RESOURCE_MIME_TYPE,
              text: fallbackHtml,
            },
          ],
        };
      }
    });
  }

  server.tool(
    "k8s-proxy",
    "Proxy any kubectl-mcp-server tool call",
    {
      tool: z.string().describe("Name of the kubectl-mcp-server tool to call"),
      args: z.record(z.string(), z.unknown()).optional().describe("Arguments to pass to the tool"),
    },
    async ({ tool, args }) => {
      try {
        const result = await proxy.callTool(
          tool,
          args || {}
        );
        return {
          content: result.content,
          isError: result.isError,
        };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return {
          content: [{ type: "text" as const, text: JSON.stringify({ error: message }) }],
          isError: true,
        };
      }
    }
  );

  return server;
}

function generateFallbackHtml(config: UIConfig): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${config.title}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #1a1a2e;
      color: #eee;
      padding: 20px;
      min-height: 100vh;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
    }
    h1 {
      font-size: 24px;
      margin-bottom: 8px;
      color: #fff;
    }
    .description {
      color: #888;
      margin-bottom: 24px;
    }
    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 60px;
      color: #666;
    }
    .spinner {
      width: 24px;
      height: 24px;
      border: 2px solid #333;
      border-top-color: #3498db;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-right: 12px;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .error {
      background: rgba(231, 76, 60, 0.1);
      border: 1px solid #e74c3c;
      border-radius: 8px;
      padding: 16px;
      color: #e74c3c;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>${config.title}</h1>
    <p class="description">${config.description}</p>
    <div class="loading">
      <div class="spinner"></div>
      <span>Loading UI components...</span>
    </div>
  </div>
  <script>
    console.log('${config.name} UI fallback loaded');
  </script>
</body>
</html>`;
}

export async function startServer(
  config: KubectlMcpServerConfig = {}
): Promise<void> {
  const server = createServer(config);
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[server] kubectl-mcp-app started on stdio");
}
