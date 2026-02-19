import type { K8sResource, GraphEdge } from './types';

export function buildRelationships(resources: Map<string, K8sResource>): GraphEdge[] {
  const edges: GraphEdge[] = [];
  const resourceArray = Array.from(resources.values());

  for (const resource of resourceArray) {
    if (!resource.ownerReferences) continue;
    for (const ref of resource.ownerReferences) {
      const owner = resourceArray.find(r => r.name === ref.name && r.kind === ref.kind && r.namespace === resource.namespace);
      if (owner) {
        edges.push({
          id: `owner-${owner.id}-${resource.id}`,
          source: owner.id,
          target: resource.id,
          type: 'ownership',
          label: 'owns',
        });
      }
    }
  }

  const services = resourceArray.filter(r => r.kind === 'Service');
  const pods = resourceArray.filter(r => r.kind === 'Pod');
  for (const svc of services) {
    if (!svc.selector) continue;
    for (const pod of pods) {
      if (!pod.labels || pod.namespace !== svc.namespace) continue;
      const matches = Object.entries(svc.selector).every(([k, v]) => pod.labels?.[k] === v);
      if (matches) {
        edges.push({
          id: `svc-pod-${svc.id}-${pod.id}`,
          source: svc.id,
          target: pod.id,
          type: 'network',
          label: svc.ports?.[0] ? `${svc.ports[0].port}→${svc.ports[0].targetPort}` : 'selects',
        });
      }
    }
  }

  const ingresses = resourceArray.filter(r => r.kind === 'Ingress');
  for (const ing of ingresses) {
    if (!ing.rules) continue;
    for (const rule of ing.rules) {
      for (const path of rule.paths) {
        const targetSvc = services.find(s => s.name === path.serviceName && s.namespace === ing.namespace);
        if (targetSvc) {
          edges.push({
            id: `ing-svc-${ing.id}-${targetSvc.id}`,
            source: ing.id,
            target: targetSvc.id,
            type: 'network',
            label: path.path || '/',
          });
        }
      }
    }
  }

  const pvcs = resourceArray.filter(r => r.kind === 'PersistentVolumeClaim' || r.kind === 'PVC');
  const pvs = resourceArray.filter(r => r.kind === 'PersistentVolume');
  for (const pvc of pvcs) {
    if (!pvc.volumeName) continue;
    const pv = pvs.find(p => p.name === pvc.volumeName);
    if (pv) {
      edges.push({
        id: `pvc-pv-${pvc.id}-${pv.id}`,
        source: pvc.id,
        target: pv.id,
        type: 'storage',
        label: 'bound',
      });
    }
  }

  const nodes = resourceArray.filter(r => r.kind === 'Node');
  for (const pod of pods) {
    if (!pod.nodeName) continue;
    const node = nodes.find(n => n.name === pod.nodeName);
    if (node) {
      edges.push({
        id: `pod-node-${pod.id}-${node.id}`,
        source: node.id,
        target: pod.id,
        type: 'ownership',
        label: 'runs',
      });
    }
  }

  return edges;
}
