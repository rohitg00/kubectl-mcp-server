export interface ToolCallRequest {
  name: string;
  arguments?: Record<string, unknown>;
}

export interface ToolCallResponse {
  content: Array<{ type: "text"; text: string }>;
  isError?: boolean;
}

export interface K8sClientConfig {
  onToolInput?: (input: ToolCallRequest) => void;
  onToolResult?: (result: ToolCallResponse) => void;
  onError?: (error: Error) => void;
}

export interface ServerToolRequest {
  name: string;
  arguments?: Record<string, unknown>;
}

export interface AppInterface {
  callServerTool(request: ServerToolRequest): Promise<ToolCallResponse>;
  ontoolinput?: (input: ToolCallRequest) => void | Promise<void>;
  ontoolresult?: (result: ToolCallResponse) => void | Promise<void>;
}

class K8sClient {
  private app: AppInterface | null = null;
  private pendingCalls: Map<
    string,
    {
      resolve: (value: ToolCallResponse) => void;
      reject: (error: Error) => void;
    }
  > = new Map();
  private callIdCounter = 0;
  private config: K8sClientConfig;

  constructor(config: K8sClientConfig = {}) {
    this.config = config;
  }

  setApp(app: AppInterface): void {
    this.app = app;
  }

  async callTool(
    name: string,
    args: Record<string, unknown> = {}
  ): Promise<unknown> {
    if (!this.app) {
      throw new Error("App not initialized. Call setApp() first.");
    }

    const request: ServerToolRequest = {
      name,
      arguments: args,
    };

    this.config.onToolInput?.({ name, arguments: args });

    try {
      const response = await this.app.callServerTool(request);

      this.config.onToolResult?.(response);

      if (response.isError) {
        const errorText = response.content[0]?.text || "Unknown error";
        throw new Error(errorText);
      }

      const text = response.content[0]?.text;
      if (!text) return null;

      try {
        return JSON.parse(text);
      } catch {
        return text;
      }
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.config.onError?.(err);
      throw err;
    }
  }

  async getPods(
    namespace = "",
    labelSelector = "",
    context = ""
  ): Promise<unknown> {
    return this.callTool("get_pods", {
      namespace,
      label_selector: labelSelector,
      context,
    });
  }

  async getPodLogs(
    namespace: string,
    pod: string,
    container = "",
    tail = 100,
    context = ""
  ): Promise<unknown> {
    return this.callTool("get_pod_logs", {
      namespace,
      pod_name: pod,
      container,
      tail_lines: tail,
      context,
    });
  }

  async deletePod(
    namespace: string,
    name: string,
    context = ""
  ): Promise<unknown> {
    return this.callTool("delete_pod", { namespace, name, context });
  }

  async getDeployments(namespace = "", context = ""): Promise<unknown> {
    return this.callTool("get_deployments", { namespace, context });
  }

  async scaleDeployment(
    namespace: string,
    name: string,
    replicas: number,
    context = ""
  ): Promise<unknown> {
    return this.callTool("scale_deployment", {
      namespace,
      name,
      replicas,
      context,
    });
  }

  async restartDeployment(
    namespace: string,
    name: string,
    context = ""
  ): Promise<unknown> {
    return this.callTool("restart_deployment", { namespace, name, context });
  }

  async rollbackDeployment(
    namespace: string,
    name: string,
    revision = 0,
    context = ""
  ): Promise<unknown> {
    return this.callTool("rollback_deployment", {
      namespace,
      name,
      revision,
      context,
    });
  }

  async getHelmReleases(namespace = "", context = ""): Promise<unknown> {
    return this.callTool("list_helm_releases", {
      namespace: namespace || "all",
      context,
    });
  }

  async upgradeHelmRelease(
    name: string,
    chart: string,
    namespace: string,
    values?: Record<string, unknown>,
    context = ""
  ): Promise<unknown> {
    return this.callTool("upgrade_helm_release", {
      name,
      chart,
      namespace,
      values: values ? JSON.stringify(values) : undefined,
      context,
    });
  }

  async rollbackHelmRelease(
    name: string,
    namespace: string,
    revision = 0,
    context = ""
  ): Promise<unknown> {
    return this.callTool("rollback_helm_release", {
      name,
      namespace,
      revision,
      context,
    });
  }

  async uninstallHelmRelease(
    name: string,
    namespace: string,
    context = ""
  ): Promise<unknown> {
    return this.callTool("uninstall_helm_release", { name, namespace, context });
  }

  async getClusterInfo(context = ""): Promise<unknown> {
    return this.callTool("get_cluster_info", { context });
  }

  async getNodes(context = ""): Promise<unknown> {
    return this.callTool("get_nodes", { context });
  }

  async getNamespaces(context = ""): Promise<unknown> {
    return this.callTool("get_namespaces", { context });
  }

  async getCostRecommendations(
    namespace = "",
    context = ""
  ): Promise<unknown> {
    return this.callTool("analyze_cost_optimization", { namespace, context });
  }

  async getEvents(
    namespace = "",
    types = "Normal,Warning",
    context = ""
  ): Promise<unknown> {
    const includesWarning = types.includes("Warning");
    const includesNormal = types.includes("Normal");
    let fieldSelector = "";
    if (includesWarning && !includesNormal) {
      fieldSelector = "type=Warning";
    } else if (includesNormal && !includesWarning) {
      fieldSelector = "type=Normal";
    }
    return this.callTool("get_events", {
      namespace,
      field_selector: fieldSelector,
      context,
    });
  }

  async getServices(namespace = "", context = ""): Promise<unknown> {
    return this.callTool("get_services", { namespace, context });
  }

  async getIngresses(namespace = "", context = ""): Promise<unknown> {
    return this.callTool("get_ingresses", { namespace, context });
  }

  async getEndpoints(namespace = "", context = ""): Promise<unknown> {
    return this.callTool("get_endpoints", { namespace, context });
  }

  async listContexts(): Promise<unknown> {
    return this.callTool("list_contexts_tool", {});
  }
}

let defaultClient: K8sClient | null = null;

export function getK8sClient(config?: K8sClientConfig): K8sClient {
  if (!defaultClient) {
    defaultClient = new K8sClient(config);
  }
  return defaultClient;
}

export function createK8sClient(config?: K8sClientConfig): K8sClient {
  return new K8sClient(config);
}

export { K8sClient };
