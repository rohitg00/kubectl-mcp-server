import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@modelcontextprotocol/sdk/server/mcp.js", () => ({
  McpServer: vi.fn().mockImplementation(() => ({
    tool: vi.fn(),
    resource: vi.fn(),
    connect: vi.fn().mockResolvedValue(undefined),
  })),
}));

vi.mock("@modelcontextprotocol/sdk/server/stdio.js", () => ({
  StdioServerTransport: vi.fn(),
}));

vi.mock("../src/proxy.js", () => ({
  KubectlMcpProxy: vi.fn().mockImplementation(() => ({
    callTool: vi.fn().mockResolvedValue({
      content: [{ type: "text", text: '{"pods": []}' }],
      isError: false,
    }),
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn().mockResolvedValue(undefined),
    isConnected: vi.fn().mockReturnValue(true),
  })),
}));

import { createServer, startServer } from "../src/server.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

describe("Server", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("createServer", () => {
    it("should create an MCP server instance", () => {
      const server = createServer();
      expect(server).toBeDefined();
      expect(McpServer).toHaveBeenCalledWith({
        name: "kubectl-mcp-app",
        version: "1.0.0",
      });
    });

    it("should accept configuration options", () => {
      const config = {
        backend: "http://localhost:8000/mcp",
        context: "production",
        namespace: "default",
      };
      const server = createServer(config);
      expect(server).toBeDefined();
    });

    it("should register all 8 UI tools", () => {
      const server = createServer();
      const mockServer = (McpServer as unknown as ReturnType<typeof vi.fn>).mock
        .results[0].value;

      const toolCalls = mockServer.tool.mock.calls;
      const toolNames = toolCalls.map(
        (call: [string, ...unknown[]]) => call[0]
      );

      expect(toolNames).toContain("k8s-pods");
      expect(toolNames).toContain("k8s-logs");
      expect(toolNames).toContain("k8s-deploy");
      expect(toolNames).toContain("k8s-helm");
      expect(toolNames).toContain("k8s-cluster");
      expect(toolNames).toContain("k8s-cost");
      expect(toolNames).toContain("k8s-events");
      expect(toolNames).toContain("k8s-network");
      expect(toolNames).toContain("k8s-proxy");
    });

    it("should register all 8 UI resources", () => {
      const server = createServer();
      const mockServer = (McpServer as unknown as ReturnType<typeof vi.fn>).mock
        .results[0].value;

      const resourceCalls = mockServer.resource.mock.calls;
      const resourceUris = resourceCalls.map(
        (call: [string, ...unknown[]]) => call[0]
      );

      expect(resourceUris).toContain("ui://k8s/pods.html");
      expect(resourceUris).toContain("ui://k8s/logs.html");
      expect(resourceUris).toContain("ui://k8s/deployments.html");
      expect(resourceUris).toContain("ui://k8s/helm.html");
      expect(resourceUris).toContain("ui://k8s/cluster.html");
      expect(resourceUris).toContain("ui://k8s/cost.html");
      expect(resourceUris).toContain("ui://k8s/events.html");
      expect(resourceUris).toContain("ui://k8s/network.html");
    });
  });

  describe("startServer", () => {
    it("should start the server with stdio transport", async () => {
      await startServer();
      const mockServer = (McpServer as unknown as ReturnType<typeof vi.fn>).mock
        .results[0].value;
      expect(mockServer.connect).toHaveBeenCalled();
    });

    it("should accept configuration options", async () => {
      const config = { context: "test-cluster" };
      await startServer(config);
      expect(McpServer).toHaveBeenCalled();
    });
  });
});
