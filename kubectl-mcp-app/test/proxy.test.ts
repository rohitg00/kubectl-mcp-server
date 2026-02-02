import { describe, it, expect, vi, beforeEach } from "vitest";

const mockConnect = vi.fn().mockResolvedValue(undefined);
const mockClose = vi.fn().mockResolvedValue(undefined);
const mockCallTool = vi.fn().mockResolvedValue({
  content: [{ type: "text", text: '{"result": "success"}' }],
  isError: false,
});
const mockListTools = vi.fn().mockResolvedValue({
  tools: [
    { name: "get_pods", description: "Get pods" },
    { name: "get_deployments", description: "Get deployments" },
  ],
});

vi.mock("@modelcontextprotocol/sdk/client/index.js", () => ({
  Client: vi.fn().mockImplementation(() => ({
    connect: mockConnect,
    close: mockClose,
    callTool: mockCallTool,
    listTools: mockListTools,
  })),
}));

vi.mock("@modelcontextprotocol/sdk/client/stdio.js", () => ({
  StdioClientTransport: vi.fn().mockImplementation(() => ({})),
}));

import {
  KubectlMcpProxy,
  getDefaultProxy,
  callKubectlTool,
} from "../src/proxy.js";

describe("KubectlMcpProxy", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("constructor", () => {
    it("should create a proxy instance with default config", () => {
      const proxy = new KubectlMcpProxy();
      expect(proxy).toBeDefined();
      expect(proxy.isConnected()).toBe(false);
    });

    it("should create a proxy instance with custom config", () => {
      const config = {
        backend: "http://localhost:8000/mcp",
        context: "production",
      };
      const proxy = new KubectlMcpProxy(config);
      expect(proxy).toBeDefined();
    });
  });

  describe("connect", () => {
    it("should connect to kubectl-mcp-server", async () => {
      const proxy = new KubectlMcpProxy();
      await proxy.connect();
      expect(mockConnect).toHaveBeenCalled();
    });

    it("should not reconnect if already connected", async () => {
      const proxy = new KubectlMcpProxy();
      await proxy.connect();
      await proxy.connect();
      expect(mockConnect).toHaveBeenCalledTimes(1);
    });
  });

  describe("callTool", () => {
    it("should call a tool and return results", async () => {
      const proxy = new KubectlMcpProxy();
      const result = await proxy.callTool("get_pods", { namespace: "default" });

      expect(result).toEqual({
        content: [{ type: "text", text: '{"result": "success"}' }],
        isError: false,
      });
      expect(mockCallTool).toHaveBeenCalledWith({
        name: "get_pods",
        arguments: { namespace: "default" },
      });
    });

    it("should handle tool call errors gracefully", async () => {
      mockCallTool.mockRejectedValueOnce(new Error("Connection failed"));
      const proxy = new KubectlMcpProxy();
      const result = await proxy.callTool("get_pods", {});

      expect(result.isError).toBe(true);
      expect(result.content[0].text).toContain("Connection failed");
    });
  });

  describe("listTools", () => {
    it("should list available tools", async () => {
      const proxy = new KubectlMcpProxy();
      const tools = await proxy.listTools();

      expect(tools).toHaveLength(2);
      expect(tools[0].name).toBe("get_pods");
      expect(tools[1].name).toBe("get_deployments");
    });
  });

  describe("disconnect", () => {
    it("should disconnect from server", async () => {
      const proxy = new KubectlMcpProxy();
      await proxy.connect();
      await proxy.disconnect();

      expect(mockClose).toHaveBeenCalled();
      expect(proxy.isConnected()).toBe(false);
    });
  });
});

describe("Helper functions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getDefaultProxy", () => {
    it("should return a singleton proxy instance", () => {
      const proxy1 = getDefaultProxy();
      const proxy2 = getDefaultProxy();
      expect(proxy1).toBe(proxy2);
    });
  });

  describe("callKubectlTool", () => {
    it("should call tool using default proxy", async () => {
      const result = await callKubectlTool("get_pods", { namespace: "default" });
      expect(result).toBeDefined();
    });
  });
});
