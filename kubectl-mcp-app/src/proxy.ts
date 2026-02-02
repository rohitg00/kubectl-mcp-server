import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import type { ToolCallResult, KubectlMcpServerConfig } from "./types.js";

export class KubectlMcpProxy {
  private client: Client | null = null;
  private config: KubectlMcpServerConfig;
  private connected: boolean = false;
  private connecting: Promise<void> | null = null;

  constructor(config: KubectlMcpServerConfig = {}) {
    this.config = config;
  }

  async connect(): Promise<void> {
    if (this.connected) return;
    if (this.connecting) return this.connecting;

    this.connecting = this._doConnect();
    try {
      await this.connecting;
      this.connected = true;
    } finally {
      this.connecting = null;
    }
  }

  private async _doConnect(): Promise<void> {
    if (this.config.backend) {
      console.error(
        `[proxy] Warning: Remote backend connection (${this.config.backend}) is not yet supported.`
      );
      console.error(`[proxy] Falling back to spawning local kubectl-mcp-server subprocess.`);
    } else {
      console.error("[proxy] Spawning kubectl-mcp-server subprocess");
    }

    const transport = new StdioClientTransport({
      command: "kubectl-mcp-server",
      args: [],
      env: {
        ...process.env,
        ...(this.config.context && { MCP_K8S_CONTEXT: this.config.context }),
      },
    });

    this.client = new Client(
      {
        name: "kubectl-mcp-app",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );

    await this.client.connect(transport);
    console.error("[proxy] Connected to kubectl-mcp-server");
  }

  async callTool(
    name: string,
    args: Record<string, unknown> = {}
  ): Promise<ToolCallResult> {
    await this.connect();

    if (!this.client) {
      throw new Error("Not connected to kubectl-mcp-server");
    }

    try {
      const result = await this.client.callTool({
        name,
        arguments: args,
      });

      return {
        content: result.content as Array<{ type: "text"; text: string }>,
        isError: result.isError as boolean | undefined,
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error(`[proxy] Tool call failed: ${name}`, message);
      return {
        content: [{ type: "text", text: JSON.stringify({ error: message }) }],
        isError: true,
      };
    }
  }

  async listTools(): Promise<Array<{ name: string; description?: string }>> {
    await this.connect();

    if (!this.client) {
      throw new Error("Not connected to kubectl-mcp-server");
    }

    const result = await this.client.listTools();
    return result.tools.map((t) => ({
      name: t.name,
      description: t.description,
    }));
  }

  async disconnect(): Promise<void> {
    if (this.client) {
      try {
        await this.client.close();
      } catch {
        // ignore
      }
      this.client = null;
    }

    this.connected = false;
    console.error("[proxy] Disconnected from kubectl-mcp-server");
  }

  isConnected(): boolean {
    return this.connected;
  }
}

let defaultProxy: KubectlMcpProxy | null = null;

export function getDefaultProxy(
  config?: KubectlMcpServerConfig
): KubectlMcpProxy {
  if (!defaultProxy) {
    defaultProxy = new KubectlMcpProxy(config);
  }
  return defaultProxy;
}

export async function callKubectlTool(
  name: string,
  args: Record<string, unknown> = {}
): Promise<ToolCallResult> {
  return getDefaultProxy().callTool(name, args);
}
