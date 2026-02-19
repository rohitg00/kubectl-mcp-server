import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import type { K8sResource, GraphNode, GraphEdge } from '../lib/types';
import { buildRelationships } from '../lib/k8sRelationships';
import { layoutGraph } from '../lib/layoutEngine';

declare global {
  interface Window {
    callServerTool?: (request: { name: string; arguments?: Record<string, unknown> }) => Promise<{ content: Array<{ type: string; text: string }> }>;
    initialArgs?: { namespace?: string; context?: string };
  }
}

async function callTool(name: string, args: Record<string, unknown> = {}): Promise<unknown> {
  if (!window.callServerTool) return null;
  const result = await window.callServerTool({ name, arguments: args });
  const text = result.content[0]?.text;
  return text ? JSON.parse(text) : null;
}

function deriveStatus(status: Record<string, unknown>, objStatus: unknown): string {
  if (typeof status.phase === 'string' && status.phase) return status.phase;
  if (typeof status.status === 'string' && status.status) return status.status;
  if (typeof objStatus === 'string' && objStatus) return objStatus;
  if (status.conditions && Array.isArray(status.conditions)) {
    for (const cond of status.conditions as Array<Record<string, unknown>>) {
      if (cond.type === 'Available' && cond.status === 'True') return 'Available';
      if (cond.type === 'Progressing' && cond.status === 'True') return 'Progressing';
    }
    const first = status.conditions[0] as Record<string, unknown> | undefined;
    if (first?.reason && typeof first.reason === 'string') return first.reason;
  }
  if (typeof objStatus === 'object' && objStatus !== null) return 'Active';
  return 'Unknown';
}

function parseResources(data: unknown, kind: string): K8sResource[] {
  if (!data || typeof data !== 'object') return [];
  const items = (data as Record<string, unknown>)[kind.toLowerCase() + 's'] as unknown[] ||
                (data as Record<string, unknown>).items as unknown[] || [];
  if (!Array.isArray(items)) return [];
  return items.map((item: unknown) => {
    const obj = item as Record<string, unknown>;
    const metadata = (obj.metadata || obj) as Record<string, unknown>;
    const status = (obj.status || obj) as Record<string, unknown>;
    const spec = (obj.spec || obj) as Record<string, unknown>;
    return {
      id: `${kind}-${metadata.namespace || 'cluster'}-${metadata.name}`,
      kind,
      name: String(metadata.name || ''),
      namespace: String(metadata.namespace || 'cluster'),
      status: deriveStatus(status, obj.status),
      labels: (metadata.labels || obj.labels) as Record<string, string> | undefined,
      ownerReferences: metadata.ownerReferences as K8sResource['ownerReferences'],
      creationTimestamp: String(metadata.creationTimestamp || ''),
      nodeName: String(spec.nodeName || status.nodeName || obj.nodeName || ''),
      replicas: Number(spec.replicas || obj.replicas || 0) || undefined,
      readyReplicas: Number(status.readyReplicas || obj.readyReplicas || 0) || undefined,
      selector: (spec.selector?.matchLabels || spec.selector || obj.selector) as Record<string, string> | undefined,
      ports: (spec.ports || obj.ports) as K8sResource['ports'],
      clusterIP: String(spec.clusterIP || obj.clusterIP || ''),
      type: String(spec.type || obj.type || ''),
      containerStatuses: (status.containerStatuses || obj.containerStatuses) as K8sResource['containerStatuses'],
      raw: item,
    } as K8sResource;
  });
}

export interface UseClusterDataResult {
  nodes: GraphNode[];
  edges: GraphEdge[];
  resources: Map<string, K8sResource>;
  namespaces: string[];
  kinds: string[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  describeResource: (resource: K8sResource) => Promise<string>;
}

export function useClusterData(namespace: string, selectedKinds: Set<string>, searchQuery: string): UseClusterDataResult {
  const [resources, setResources] = useState<Map<string, K8sResource>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const layoutCacheRef = useRef<Map<string, { x: number; z: number }>>(new Map());

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    const context = window.initialArgs?.context || '';
    const ns = namespace || window.initialArgs?.namespace || '';
    const args = { namespace: ns, context };

    try {
      const [podsData, deploymentsData, servicesData, ingressesData] = await Promise.all([
        callTool('get_pods', args),
        callTool('get_deployments', args),
        callTool('get_services', args),
        callTool('get_ingresses', args),
      ]);

      const allResources = new Map<string, K8sResource>();
      for (const r of parseResources(podsData, 'Pod')) allResources.set(r.id, r);
      for (const r of parseResources(deploymentsData, 'Deployment')) allResources.set(r.id, r);
      for (const r of parseResources(servicesData, 'Service')) allResources.set(r.id, r);
      for (const r of parseResources(ingressesData, 'Ingress')) allResources.set(r.id, r);

      setResources(allResources);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch cluster data');
      setResources(getMockResources());
      setLoading(false);
    }
  }, [namespace]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const describeResource = useCallback(async (resource: K8sResource): Promise<string> => {
    try {
      const result = await callTool('describe_resource', {
        resource_type: resource.kind.toLowerCase(),
        resource_name: resource.name,
        namespace: resource.namespace,
      });
      if (result && typeof result === 'object') {
        const obj = result as Record<string, unknown>;
        return String(obj.description || obj.output || JSON.stringify(result, null, 2));
      }
      return String(result || 'No output');
    } catch {
      return 'Failed to describe resource';
    }
  }, []);

  const filteredResources = new Map<string, K8sResource>();
  for (const [id, r] of resources) {
    if (selectedKinds.size > 0 && !selectedKinds.has(r.kind)) continue;
    if (searchQuery && !r.name.toLowerCase().includes(searchQuery.toLowerCase())) continue;
    filteredResources.set(id, r);
  }

  const edges = buildRelationships(filteredResources);
  const graphNodes: GraphNode[] = Array.from(filteredResources.values()).map(r => {
    const cached = layoutCacheRef.current.get(r.id);
    return {
      id: r.id,
      kind: r.kind,
      name: r.name,
      namespace: r.namespace,
      status: r.status,
      x: cached?.x ?? 0,
      y: 0,
      z: cached?.z ?? 0,
      vx: 0, vy: 0, vz: 0,
      resource: r,
    };
  });

  const edgeObjects: GraphEdge[] = edges.map(e => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: e.type,
    label: e.label,
  }));

  const currentNodeIds = new Set(graphNodes.map(n => n.id));
  const cachedNodeIds = new Set(layoutCacheRef.current.keys());
  const idsChanged = currentNodeIds.size !== cachedNodeIds.size ||
    [...currentNodeIds].some(id => !cachedNodeIds.has(id));

  if (idsChanged) {
    layoutGraph(graphNodes, edgeObjects);
    layoutCacheRef.current = new Map(graphNodes.map(n => [n.id, { x: n.x, z: n.z }]));
  }

  const namespaces = [...new Set(Array.from(resources.values()).map(r => r.namespace))].sort();
  const kinds = [...new Set(Array.from(resources.values()).map(r => r.kind))].sort();

  const stableEdges = useMemo(() => edgeObjects, [edges.map(e => e.id).join(',')]);

  return { nodes: graphNodes, edges: stableEdges, resources, namespaces, kinds, loading, error, refresh: fetchData, describeResource };
}

function getMockResources(): Map<string, K8sResource> {
  const resources = new Map<string, K8sResource>();
  const mocks: K8sResource[] = [
    { id: 'Deployment-default-nginx', kind: 'Deployment', name: 'nginx', namespace: 'default', status: 'Available', replicas: 3, readyReplicas: 3, selector: { app: 'nginx' } },
    { id: 'Pod-default-nginx-abc', kind: 'Pod', name: 'nginx-abc', namespace: 'default', status: 'Running', labels: { app: 'nginx' }, nodeName: 'node-1' },
    { id: 'Pod-default-nginx-def', kind: 'Pod', name: 'nginx-def', namespace: 'default', status: 'Running', labels: { app: 'nginx' }, nodeName: 'node-1' },
    { id: 'Pod-default-nginx-ghi', kind: 'Pod', name: 'nginx-ghi', namespace: 'default', status: 'Pending', labels: { app: 'nginx' }, nodeName: 'node-2' },
    { id: 'Service-default-nginx-svc', kind: 'Service', name: 'nginx-svc', namespace: 'default', status: 'Active', selector: { app: 'nginx' }, ports: [{ port: 80, targetPort: 80, protocol: 'TCP' }], clusterIP: '10.96.0.100', type: 'ClusterIP' },
    { id: 'Ingress-default-main-ingress', kind: 'Ingress', name: 'main-ingress', namespace: 'default', status: 'Active', rules: [{ host: 'app.example.com', paths: [{ path: '/', serviceName: 'nginx-svc', servicePort: 80 }] }] },
    { id: 'Deployment-default-api', kind: 'Deployment', name: 'api', namespace: 'default', status: 'Available', replicas: 2, readyReplicas: 2, selector: { app: 'api' } },
    { id: 'Pod-default-api-123', kind: 'Pod', name: 'api-123', namespace: 'default', status: 'Running', labels: { app: 'api' } },
    { id: 'Pod-default-api-456', kind: 'Pod', name: 'api-456', namespace: 'default', status: 'Running', labels: { app: 'api' } },
    { id: 'Service-default-api-svc', kind: 'Service', name: 'api-svc', namespace: 'default', status: 'Active', selector: { app: 'api' }, ports: [{ port: 8080, targetPort: 8080, protocol: 'TCP' }], clusterIP: '10.96.0.101', type: 'ClusterIP' },
    { id: 'Service-default-redis', kind: 'Service', name: 'redis', namespace: 'default', status: 'Active', selector: { app: 'redis' }, ports: [{ port: 6379, targetPort: 6379, protocol: 'TCP' }], clusterIP: '10.96.0.102' },
    { id: 'Pod-default-redis-0', kind: 'Pod', name: 'redis-0', namespace: 'default', status: 'Running', labels: { app: 'redis' } },
  ];
  for (const m of mocks) resources.set(m.id, m);
  return resources;
}
