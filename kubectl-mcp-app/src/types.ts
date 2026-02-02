export interface Pod {
  name: string;
  namespace: string;
  status: PodStatus;
  phase: string;
  containers: ContainerInfo[];
  restarts: number;
  age: string;
  nodeName: string;
  ip: string;
  cpu?: ResourceUsage;
  memory?: ResourceUsage;
  labels?: Record<string, string>;
  annotations?: Record<string, string>;
}

export type PodStatus =
  | "Running"
  | "Pending"
  | "Succeeded"
  | "Failed"
  | "Unknown"
  | "Terminating"
  | "CrashLoopBackOff"
  | "ImagePullBackOff"
  | "ContainerCreating";

export interface ContainerInfo {
  name: string;
  image: string;
  ready: boolean;
  restartCount: number;
  state: "running" | "waiting" | "terminated";
  reason?: string;
}

export interface ResourceUsage {
  current: string;
  requested: string;
  limit: string;
  percentage?: number;
}

export interface Deployment {
  name: string;
  namespace: string;
  replicas: number;
  readyReplicas: number;
  updatedReplicas: number;
  availableReplicas: number;
  strategy: "RollingUpdate" | "Recreate";
  age: string;
  image: string;
  labels?: Record<string, string>;
  conditions?: DeploymentCondition[];
}

export interface DeploymentCondition {
  type: string;
  status: "True" | "False" | "Unknown";
  reason?: string;
  message?: string;
  lastUpdateTime?: string;
}

export interface HelmRelease {
  name: string;
  namespace: string;
  revision: number;
  status: HelmStatus;
  chart: string;
  chartVersion: string;
  appVersion: string;
  updated: string;
  notes?: string;
}

export type HelmStatus =
  | "deployed"
  | "failed"
  | "pending"
  | "pending-install"
  | "pending-upgrade"
  | "pending-rollback"
  | "uninstalling"
  | "superseded"
  | "uninstalled";

export interface Node {
  name: string;
  status: "Ready" | "NotReady" | "SchedulingDisabled";
  roles: string[];
  age: string;
  version: string;
  internalIP: string;
  externalIP?: string;
  os: string;
  architecture: string;
  cpu: NodeResource;
  memory: NodeResource;
  pods: NodeResource;
  conditions?: NodeCondition[];
}

export interface NodeResource {
  capacity: string;
  allocatable: string;
  used?: string;
  percentage?: number;
}

export interface NodeCondition {
  type: string;
  status: "True" | "False" | "Unknown";
  reason?: string;
  message?: string;
}

export interface Namespace {
  name: string;
  status: "Active" | "Terminating";
  age: string;
  labels?: Record<string, string>;
  resourceQuota?: ResourceQuota;
}

export interface ResourceQuota {
  cpu?: QuotaValue;
  memory?: QuotaValue;
  pods?: QuotaValue;
  services?: QuotaValue;
  secrets?: QuotaValue;
  configmaps?: QuotaValue;
  pvcs?: QuotaValue;
}

export interface QuotaValue {
  used: string;
  hard: string;
}

export interface Service {
  name: string;
  namespace: string;
  type: "ClusterIP" | "NodePort" | "LoadBalancer" | "ExternalName";
  clusterIP: string;
  externalIP?: string;
  ports: ServicePort[];
  selector?: Record<string, string>;
  age: string;
}

export interface ServicePort {
  name?: string;
  port: number;
  targetPort: number | string;
  nodePort?: number;
  protocol: "TCP" | "UDP" | "SCTP";
}

export interface Ingress {
  name: string;
  namespace: string;
  class?: string;
  hosts: string[];
  address?: string;
  ports: string;
  age: string;
  rules?: IngressRule[];
}

export interface IngressRule {
  host: string;
  paths: IngressPath[];
}

export interface IngressPath {
  path: string;
  pathType: "Prefix" | "Exact" | "ImplementationSpecific";
  backend: {
    service: string;
    port: number | string;
  };
}

export interface Event {
  type: "Normal" | "Warning";
  reason: string;
  message: string;
  object: string;
  objectKind: string;
  namespace?: string;
  count: number;
  firstTimestamp: string;
  lastTimestamp: string;
  source?: string;
}

export interface CostRecommendation {
  resourceType: "Pod" | "Deployment" | "StatefulSet" | "DaemonSet";
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

export interface ClusterInfo {
  name: string;
  context: string;
  server: string;
  version: string;
  platform?: string;
  nodeCount: number;
  namespaceCount: number;
  podCount: number;
  cpuCapacity: string;
  memoryCapacity: string;
  cpuUsed?: string;
  memoryUsed?: string;
}

export interface LogEntry {
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR" | "DEBUG" | "TRACE";
  message: string;
  container?: string;
  raw: string;
}

export interface NetworkNode {
  id: string;
  type: "Pod" | "Service" | "Ingress" | "Endpoint";
  name: string;
  namespace: string;
  labels?: Record<string, string>;
}

export interface NetworkEdge {
  source: string;
  target: string;
  port?: number;
  protocol?: string;
}

export interface NetworkTopology {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

export interface ToolCallResult {
  content: Array<{
    type: "text";
    text: string;
  }>;
  isError?: boolean;
}

export interface KubectlMcpServerConfig {
  backend?: string;
  context?: string;
  namespace?: string;
}
