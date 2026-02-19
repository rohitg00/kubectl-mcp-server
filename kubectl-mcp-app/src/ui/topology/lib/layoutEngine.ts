import type { GraphNode, GraphEdge } from './types';

const REPULSION = 5000;
const ATTRACTION = 0.05;
const DAMPING = 0.9;
const CENTER_PULL = 0.01;
const ITERATIONS = 100;
const IDEAL_DISTANCE = 4;
const NAMESPACE_SPACING = 12;

export function layoutGraph(nodes: GraphNode[], edges: GraphEdge[]): void {
  if (nodes.length === 0) return;

  const namespaces = new Map<string, GraphNode[]>();
  for (const node of nodes) {
    const ns = node.namespace || 'cluster';
    if (!namespaces.has(ns)) namespaces.set(ns, []);
    namespaces.get(ns)!.push(node);
  }

  let nsIndex = 0;
  const nsCount = namespaces.size;
  for (const [, nsNodes] of namespaces) {
    const nsAngle = (2 * Math.PI * nsIndex) / Math.max(nsCount, 1);
    const nsRadius = nsCount > 1 ? NAMESPACE_SPACING : 0;
    const nsCenterX = Math.cos(nsAngle) * nsRadius;
    const nsCenterZ = Math.sin(nsAngle) * nsRadius;

    for (let i = 0; i < nsNodes.length; i++) {
      const angle = (2 * Math.PI * i) / nsNodes.length;
      const radius = Math.min(nsNodes.length * 1.5, 8);
      nsNodes[i].x = nsCenterX + Math.cos(angle) * radius;
      nsNodes[i].y = 0;
      nsNodes[i].z = nsCenterZ + Math.sin(angle) * radius;
      nsNodes[i].vx = 0;
      nsNodes[i].vy = 0;
      nsNodes[i].vz = 0;
    }
    nsIndex++;
  }

  for (let iter = 0; iter < ITERATIONS; iter++) {
    const cooling = 1 - iter / ITERATIONS;

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const a = nodes[i];
        const b = nodes[j];
        const dx = a.x - b.x;
        const dz = a.z - b.z;
        const distSq = dx * dx + dz * dz;
        const dist = Math.sqrt(distSq) || 0.01;
        const force = (REPULSION / distSq) * cooling;
        const fx = (dx / dist) * force;
        const fz = (dz / dist) * force;
        a.vx += fx;
        a.vz += fz;
        b.vx -= fx;
        b.vz -= fz;
      }
    }

    for (const edge of edges) {
      const a = nodes.find(n => n.id === edge.source);
      const b = nodes.find(n => n.id === edge.target);
      if (!a || !b) continue;
      const dx = b.x - a.x;
      const dz = b.z - a.z;
      const dist = Math.sqrt(dx * dx + dz * dz) || 0.01;
      const force = (dist - IDEAL_DISTANCE) * ATTRACTION * cooling;
      const fx = (dx / dist) * force;
      const fz = (dz / dist) * force;
      a.vx += fx;
      a.vz += fz;
      b.vx -= fx;
      b.vz -= fz;
    }

    for (const node of nodes) {
      node.vx -= node.x * CENTER_PULL;
      node.vz -= node.z * CENTER_PULL;
    }

    for (const node of nodes) {
      node.vx *= DAMPING;
      node.vz *= DAMPING;
      node.x += node.vx;
      node.z += node.vz;
    }
  }

  for (const node of nodes) {
    if (node.kind === 'Node') {
      node.y = -0.2;
    }
  }
}
