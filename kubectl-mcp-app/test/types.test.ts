import { describe, it, expect } from "vitest";
import type {
  Pod,
  PodStatus,
  Deployment,
  HelmRelease,
  Node,
  Event,
  CostRecommendation,
  ClusterInfo,
  ToolCallResult,
  KubectlMcpServerConfig,
} from "../src/types.js";

describe("Types", () => {
  describe("Pod", () => {
    it("should accept valid pod data", () => {
      const pod: Pod = {
        name: "nginx-abc123",
        namespace: "default",
        status: "Running",
        phase: "Running",
        containers: [
          {
            name: "nginx",
            image: "nginx:latest",
            ready: true,
            restartCount: 0,
            state: "running",
          },
        ],
        restarts: 0,
        age: "2d",
        nodeName: "node-1",
        ip: "10.244.0.5",
      };

      expect(pod.name).toBe("nginx-abc123");
      expect(pod.status).toBe("Running");
    });
  });

  describe("PodStatus", () => {
    it("should include all valid statuses", () => {
      const statuses: PodStatus[] = [
        "Running",
        "Pending",
        "Succeeded",
        "Failed",
        "Unknown",
        "Terminating",
        "CrashLoopBackOff",
        "ImagePullBackOff",
        "ContainerCreating",
      ];

      expect(statuses).toHaveLength(9);
    });
  });

  describe("Deployment", () => {
    it("should accept valid deployment data", () => {
      const deployment: Deployment = {
        name: "nginx-deployment",
        namespace: "default",
        replicas: 3,
        readyReplicas: 3,
        updatedReplicas: 3,
        availableReplicas: 3,
        strategy: "RollingUpdate",
        age: "5d",
        image: "nginx:1.21",
      };

      expect(deployment.replicas).toBe(3);
      expect(deployment.strategy).toBe("RollingUpdate");
    });
  });

  describe("HelmRelease", () => {
    it("should accept valid helm release data", () => {
      const release: HelmRelease = {
        name: "nginx-ingress",
        namespace: "ingress-nginx",
        revision: 5,
        status: "deployed",
        chart: "ingress-nginx",
        chartVersion: "4.7.1",
        appVersion: "1.8.1",
        updated: "2024-01-15T10:00:00Z",
      };

      expect(release.status).toBe("deployed");
      expect(release.revision).toBe(5);
    });
  });

  describe("Node", () => {
    it("should accept valid node data", () => {
      const node: Node = {
        name: "node-1",
        status: "Ready",
        roles: ["control-plane", "master"],
        age: "30d",
        version: "v1.28.4",
        internalIP: "192.168.1.10",
        os: "linux",
        architecture: "amd64",
        cpu: { capacity: "8", allocatable: "7.5" },
        memory: { capacity: "32Gi", allocatable: "30Gi" },
        pods: { capacity: "110", allocatable: "110" },
      };

      expect(node.status).toBe("Ready");
      expect(node.roles).toContain("control-plane");
    });
  });

  describe("Event", () => {
    it("should accept valid event data", () => {
      const event: Event = {
        type: "Warning",
        reason: "FailedScheduling",
        message: "0/3 nodes are available",
        object: "pending-pod-abc",
        objectKind: "Pod",
        namespace: "production",
        count: 5,
        firstTimestamp: "2024-01-15T09:00:00Z",
        lastTimestamp: "2024-01-15T10:00:00Z",
      };

      expect(event.type).toBe("Warning");
      expect(event.count).toBe(5);
    });
  });

  describe("CostRecommendation", () => {
    it("should accept valid cost recommendation data", () => {
      const recommendation: CostRecommendation = {
        resourceType: "Deployment",
        name: "api-server",
        namespace: "production",
        recommendation: "Reduce CPU request",
        currentCpu: "2000m",
        suggestedCpu: "500m",
        currentMemory: "4Gi",
        suggestedMemory: "2Gi",
        savingsEstimate: "$120/mo",
        confidence: "high",
      };

      expect(recommendation.confidence).toBe("high");
      expect(recommendation.savingsEstimate).toBe("$120/mo");
    });
  });

  describe("ClusterInfo", () => {
    it("should accept valid cluster info data", () => {
      const cluster: ClusterInfo = {
        name: "production-cluster",
        context: "prod-ctx",
        server: "https://k8s.example.com:6443",
        version: "v1.28.4",
        nodeCount: 4,
        namespaceCount: 12,
        podCount: 87,
        cpuCapacity: "32 cores",
        memoryCapacity: "128 Gi",
      };

      expect(cluster.nodeCount).toBe(4);
      expect(cluster.version).toBe("v1.28.4");
    });
  });

  describe("ToolCallResult", () => {
    it("should accept valid tool call result", () => {
      const result: ToolCallResult = {
        content: [{ type: "text", text: '{"pods": []}' }],
        isError: false,
      };

      expect(result.content).toHaveLength(1);
      expect(result.isError).toBe(false);
    });
  });

  describe("KubectlMcpServerConfig", () => {
    it("should accept valid configuration", () => {
      const config: KubectlMcpServerConfig = {
        backend: "http://localhost:8000/mcp",
        context: "production",
        namespace: "default",
      };

      expect(config.backend).toBe("http://localhost:8000/mcp");
    });

    it("should accept empty configuration", () => {
      const config: KubectlMcpServerConfig = {};
      expect(config).toEqual({});
    });
  });
});
