import React, { useRef, useEffect, useState, useCallback } from "react";

export interface GraphNode {
  id: string;
  type: "Pod" | "Service" | "Ingress" | "Endpoint" | "Deployment";
  label: string;
  namespace?: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}

export interface ResourceGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  width?: number;
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
  selectedNodeId?: string;
}

const NODE_COLORS: Record<string, string> = {
  Pod: "#3fb950",
  Service: "#2f81f7",
  Ingress: "#a371f7",
  Endpoint: "#8b949e",
  Deployment: "#f0883e",
};

const NODE_ICONS: Record<string, string> = {
  Pod: "⬢",
  Service: "◉",
  Ingress: "⬡",
  Endpoint: "○",
  Deployment: "▣",
};

export function ResourceGraph({
  nodes,
  edges,
  width = 800,
  height = 600,
  onNodeClick,
  selectedNodeId,
}: ResourceGraphProps): React.ReactElement {
  const svgRef = useRef<SVGSVGElement>(null);
  const [simulatedNodes, setSimulatedNodes] = useState<GraphNode[]>([]);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [dragging, setDragging] = useState<string | null>(null);
  const [panning, setPanning] = useState(false);
  const [lastPan, setLastPan] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const initialNodes = nodes.map((node, i) => ({
      ...node,
      x: node.x ?? width / 2 + Math.cos((i / nodes.length) * 2 * Math.PI) * 150,
      y: node.y ?? height / 2 + Math.sin((i / nodes.length) * 2 * Math.PI) * 150,
      vx: 0,
      vy: 0,
    }));

    const simulate = () => {
      const updatedNodes = [...initialNodes];
      const iterations = 100;

      for (let iter = 0; iter < iterations; iter++) {
        for (let i = 0; i < updatedNodes.length; i++) {
          for (let j = i + 1; j < updatedNodes.length; j++) {
            const dx = updatedNodes[j].x! - updatedNodes[i].x!;
            const dy = updatedNodes[j].y! - updatedNodes[i].y!;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = 5000 / (dist * dist);

            updatedNodes[i].vx! -= (dx / dist) * force;
            updatedNodes[i].vy! -= (dy / dist) * force;
            updatedNodes[j].vx! += (dx / dist) * force;
            updatedNodes[j].vy! += (dy / dist) * force;
          }
        }

        for (const edge of edges) {
          const source = updatedNodes.find((n) => n.id === edge.source);
          const target = updatedNodes.find((n) => n.id === edge.target);
          if (!source || !target) continue;

          const dx = target.x! - source.x!;
          const dy = target.y! - source.y!;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (dist - 100) * 0.05;

          source.vx! += (dx / dist) * force;
          source.vy! += (dy / dist) * force;
          target.vx! -= (dx / dist) * force;
          target.vy! -= (dy / dist) * force;
        }

        for (const node of updatedNodes) {
          const cx = width / 2;
          const cy = height / 2;
          node.vx! += (cx - node.x!) * 0.01;
          node.vy! += (cy - node.y!) * 0.01;
        }

        for (const node of updatedNodes) {
          node.vx! *= 0.9;
          node.vy! *= 0.9;
          node.x! += node.vx!;
          node.y! += node.vy!;

          node.x = Math.max(50, Math.min(width - 50, node.x!));
          node.y = Math.max(50, Math.min(height - 50, node.y!));
        }
      }

      setSimulatedNodes(updatedNodes);
    };

    simulate();
  }, [nodes, edges, width, height]);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent, nodeId?: string) => {
      if (nodeId) {
        setDragging(nodeId);
      } else {
        setPanning(true);
        setLastPan({ x: e.clientX, y: e.clientY });
      }
    },
    []
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (dragging) {
        const svg = svgRef.current;
        if (!svg) return;

        const rect = svg.getBoundingClientRect();
        const x = (e.clientX - rect.left - transform.x) / transform.scale;
        const y = (e.clientY - rect.top - transform.y) / transform.scale;

        setSimulatedNodes((prev) =>
          prev.map((node) =>
            node.id === dragging ? { ...node, x, y } : node
          )
        );
      } else if (panning) {
        const dx = e.clientX - lastPan.x;
        const dy = e.clientY - lastPan.y;
        setTransform((prev) => ({ ...prev, x: prev.x + dx, y: prev.y + dy }));
        setLastPan({ x: e.clientX, y: e.clientY });
      }
    },
    [dragging, panning, lastPan, transform]
  );

  const handleMouseUp = useCallback(() => {
    setDragging(null);
    setPanning(false);
  }, []);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const scaleFactor = e.deltaY > 0 ? 0.9 : 1.1;
    setTransform((prev) => ({
      ...prev,
      scale: Math.max(0.5, Math.min(2, prev.scale * scaleFactor)),
    }));
  }, []);

  const getEdgePath = (edge: GraphEdge): string => {
    const source = simulatedNodes.find((n) => n.id === edge.source);
    const target = simulatedNodes.find((n) => n.id === edge.target);
    if (!source || !target) return "";

    return `M ${source.x} ${source.y} L ${target.x} ${target.y}`;
  };

  return (
    <div className="resource-graph">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        onMouseDown={(e) => handleMouseDown(e)}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.scale})`}>
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="var(--border)" />
            </marker>
          </defs>

          {edges.map((edge, i) => (
            <g key={`edge-${i}`}>
              <path
                d={getEdgePath(edge)}
                fill="none"
                stroke="var(--border)"
                strokeWidth={1.5}
                markerEnd="url(#arrowhead)"
              />
              {edge.label && (
                <text
                  x={
                    ((simulatedNodes.find((n) => n.id === edge.source)?.x || 0) +
                      (simulatedNodes.find((n) => n.id === edge.target)?.x || 0)) /
                    2
                  }
                  y={
                    ((simulatedNodes.find((n) => n.id === edge.source)?.y || 0) +
                      (simulatedNodes.find((n) => n.id === edge.target)?.y || 0)) /
                      2 -
                    8
                  }
                  textAnchor="middle"
                  fill="var(--text-muted)"
                  fontSize={10}
                >
                  {edge.label}
                </text>
              )}
            </g>
          ))}

          {simulatedNodes.map((node) => (
            <g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              onMouseDown={(e) => {
                e.stopPropagation();
                handleMouseDown(e, node.id);
              }}
              onClick={() => onNodeClick?.(node)}
              style={{ cursor: "pointer" }}
            >
              <circle
                r={30}
                fill={NODE_COLORS[node.type]}
                opacity={selectedNodeId === node.id ? 1 : 0.8}
                stroke={selectedNodeId === node.id ? "#fff" : "none"}
                strokeWidth={2}
              />
              <text
                textAnchor="middle"
                dominantBaseline="central"
                fill="#fff"
                fontSize={18}
                fontWeight="bold"
              >
                {NODE_ICONS[node.type]}
              </text>
              <text
                y={45}
                textAnchor="middle"
                fill="var(--text)"
                fontSize={11}
                fontWeight={500}
              >
                {node.label}
              </text>
              <text
                y={58}
                textAnchor="middle"
                fill="var(--text-muted)"
                fontSize={9}
              >
                {node.type}
              </text>
            </g>
          ))}
        </g>
      </svg>

      <div className="graph-legend">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <div key={type} className="legend-item">
            <span
              className="legend-color"
              style={{ backgroundColor: color }}
            />
            <span>{type}</span>
          </div>
        ))}
      </div>

      <div className="graph-controls">
        <button onClick={() => setTransform({ x: 0, y: 0, scale: 1 })}>
          Reset
        </button>
        <button
          onClick={() =>
            setTransform((prev) => ({ ...prev, scale: prev.scale * 1.2 }))
          }
        >
          +
        </button>
        <button
          onClick={() =>
            setTransform((prev) => ({ ...prev, scale: prev.scale * 0.8 }))
          }
        >
          −
        </button>
      </div>

      <style>{`
        .resource-graph {
          position: relative;
          background: var(--bg);
          border: 1px solid var(--border);
          border-radius: 8px;
          overflow: hidden;
        }

        .resource-graph svg {
          display: block;
        }

        .graph-legend {
          position: absolute;
          bottom: 12px;
          left: 12px;
          display: flex;
          gap: 16px;
          padding: 8px 12px;
          background: var(--bg-secondary);
          border-radius: 6px;
          font-size: 11px;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
          color: var(--text-secondary);
        }

        .legend-color {
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }

        .graph-controls {
          position: absolute;
          top: 12px;
          right: 12px;
          display: flex;
          gap: 4px;
        }

        .graph-controls button {
          width: 32px;
          height: 32px;
          background: var(--bg-secondary);
          border: 1px solid var(--border);
          border-radius: 6px;
          color: var(--text);
          font-size: 14px;
          cursor: pointer;
        }

        .graph-controls button:hover {
          background: var(--bg-tertiary);
        }
      `}</style>
    </div>
  );
}
