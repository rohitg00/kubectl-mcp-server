export interface K8sResource {
  id: string;
  kind: string;
  name: string;
  namespace: string;
  status: string;
  labels?: Record<string, string>;
  ownerReferences?: OwnerReference[];
  creationTimestamp?: string;
  nodeName?: string;
  containerStatuses?: ContainerStatus[];
  replicas?: number;
  readyReplicas?: number;
  selector?: Record<string, string>;
  ports?: ServicePort[];
  clusterIP?: string;
  type?: string;
  rules?: IngressRule[];
  volumeName?: string;
  storageClass?: string;
  currentUtilization?: number;
  targetUtilization?: number;
  raw?: unknown;
}

export interface OwnerReference {
  apiVersion: string;
  kind: string;
  name: string;
  uid: string;
}

export interface ContainerStatus {
  name: string;
  ready: boolean;
  restartCount: number;
  state: string;
  image: string;
}

export interface ServicePort {
  name?: string;
  port: number;
  targetPort: number | string;
  protocol: string;
  nodePort?: number;
}

export interface IngressRule {
  host?: string;
  paths: Array<{ path: string; serviceName: string; servicePort: number }>;
}

export interface GraphNode {
  id: string;
  kind: string;
  name: string;
  namespace: string;
  status: string;
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  resource: K8sResource;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: RelationshipType;
  label?: string;
}

export type RelationshipType = 'ownership' | 'network' | 'storage' | 'config';

export interface ClusterState {
  resources: Map<string, K8sResource>;
  nodes: Map<string, GraphNode>;
  edges: Map<string, GraphEdge>;
}

export type WatchEventType = 'ADDED' | 'MODIFIED' | 'DELETED' | 'SNAPSHOT';
