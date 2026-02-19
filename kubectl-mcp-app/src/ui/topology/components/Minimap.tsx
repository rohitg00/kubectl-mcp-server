import React, { useMemo } from 'react';
import type { GraphNode, GraphEdge } from '../lib/types';

interface MinimapProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedId: string | null;
  width?: number;
  height?: number;
}

const KIND_COLORS: Record<string, string> = {
  Pod: '#326CE5', Deployment: '#f97316', ReplicaSet: '#eab308', StatefulSet: '#a855f7',
  DaemonSet: '#06b6d4', Service: '#326CE5', Ingress: '#8b5cf6', ConfigMap: '#92400e',
  Secret: '#991b1b', Node: '#374151',
};

export function Minimap({ nodes, edges, selectedId, width = 200, height = 150 }: MinimapProps): React.ReactElement {
  const { viewBox, scaledNodes, scaledEdges } = useMemo(() => {
    if (nodes.length === 0) return { viewBox: '0 0 200 150', scaledNodes: [], scaledEdges: [] };

    let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
    for (const n of nodes) {
      minX = Math.min(minX, n.x);
      maxX = Math.max(maxX, n.x);
      minZ = Math.min(minZ, n.z);
      maxZ = Math.max(maxZ, n.z);
    }

    const padding = 3;
    minX -= padding; maxX += padding; minZ -= padding; maxZ += padding;
    const rangeX = maxX - minX || 1;
    const rangeZ = maxZ - minZ || 1;

    const scaleX = (x: number) => ((x - minX) / rangeX) * (width - 20) + 10;
    const scaleZ = (z: number) => ((z - minZ) / rangeZ) * (height - 20) + 10;

    const sn = nodes.map(n => ({
      id: n.id,
      x: scaleX(n.x),
      y: scaleZ(n.z),
      kind: n.kind,
      selected: n.id === selectedId,
    }));

    const nodeMap = new Map(nodes.map(n => [n.id, n]));
    const se = edges.map(e => {
      const s = nodeMap.get(e.source);
      const t = nodeMap.get(e.target);
      if (!s || !t) return null;
      return { x1: scaleX(s.x), y1: scaleZ(s.z), x2: scaleX(t.x), y2: scaleZ(t.z) };
    }).filter(Boolean);

    return { viewBox: `0 0 ${width} ${height}`, scaledNodes: sn, scaledEdges: se as Array<{ x1: number; y1: number; x2: number; y2: number }> };
  }, [nodes, edges, selectedId, width, height]);

  return (
    <div style={styles.container}>
      <svg width={width} height={height} viewBox={viewBox} style={styles.svg}>
        {scaledEdges.map((e, i) => (
          <line key={i} x1={e.x1} y1={e.y1} x2={e.x2} y2={e.y2} stroke="rgba(88,166,255,0.2)" strokeWidth={0.5} />
        ))}
        {scaledNodes.map(n => (
          <circle key={n.id} cx={n.x} cy={n.y} r={n.selected ? 4 : 2.5}
            fill={KIND_COLORS[n.kind] || '#6e7681'}
            stroke={n.selected ? '#ffa657' : 'none'}
            strokeWidth={n.selected ? 1.5 : 0}
          />
        ))}
      </svg>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { position: 'absolute', bottom: 16, right: 16, background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 8, padding: 4, opacity: 0.9 },
  svg: { display: 'block' },
};
