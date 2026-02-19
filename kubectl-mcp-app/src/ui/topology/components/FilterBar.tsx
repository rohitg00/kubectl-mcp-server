import React from 'react';

interface FilterBarProps {
  namespaces: string[];
  selectedNamespace: string;
  onNamespaceChange: (ns: string) => void;
  kinds: string[];
  selectedKinds: Set<string>;
  onKindToggle: (kind: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  resourceCount: number;
  edgeCount: number;
}

const KIND_COLORS: Record<string, string> = {
  Pod: '#326CE5', Deployment: '#f97316', ReplicaSet: '#eab308', StatefulSet: '#a855f7',
  DaemonSet: '#06b6d4', Service: '#326CE5', Ingress: '#8b5cf6', ConfigMap: '#92400e',
  Secret: '#991b1b', PersistentVolumeClaim: '#6b7280', Node: '#374151', Namespace: '#326CE5',
  HPA: '#14b8a6', NetworkPolicy: '#ef4444', Job: '#22c55e', CronJob: '#8b5cf6',
};

export function FilterBar({
  namespaces, selectedNamespace, onNamespaceChange,
  kinds, selectedKinds, onKindToggle,
  searchQuery, onSearchChange,
  resourceCount, edgeCount,
}: FilterBarProps): React.ReactElement {
  return (
    <div style={styles.bar}>
      <div style={styles.left}>
        <select value={selectedNamespace} onChange={e => onNamespaceChange(e.target.value)} style={styles.select}>
          <option value="">All Namespaces</option>
          {namespaces.map(ns => <option key={ns} value={ns}>{ns}</option>)}
        </select>
        <input
          type="text"
          placeholder="Search resources..."
          value={searchQuery}
          onChange={e => onSearchChange(e.target.value)}
          style={styles.search}
        />
      </div>
      <div style={styles.kinds}>
        {kinds.map(kind => (
          <button
            key={kind}
            onClick={() => onKindToggle(kind)}
            style={{
              ...styles.kindChip,
              borderColor: selectedKinds.has(kind) ? KIND_COLORS[kind] || 'var(--border)' : 'transparent',
              opacity: selectedKinds.has(kind) ? 1 : 0.5,
            }}
          >
            <span style={{ ...styles.kindDot, background: KIND_COLORS[kind] || 'var(--text-muted)' }} />
            {kind}
          </button>
        ))}
      </div>
      <div style={styles.stats}>
        <span>{resourceCount} resources</span>
        <span>{edgeCount} connections</span>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  bar: { display: 'flex', alignItems: 'center', gap: 16, padding: '10px 16px', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)', flexWrap: 'wrap' as const },
  left: { display: 'flex', gap: 8 },
  select: { padding: '6px 10px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)', fontSize: 13 },
  search: { padding: '6px 10px', background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)', fontSize: 13, width: 200 },
  kinds: { display: 'flex', gap: 4, flexWrap: 'wrap' as const },
  kindChip: { display: 'flex', alignItems: 'center', gap: 4, padding: '3px 8px', background: 'var(--bg-tertiary)', border: '1px solid', borderRadius: 12, color: 'var(--text)', fontSize: 11, cursor: 'pointer' },
  kindDot: { width: 8, height: 8, borderRadius: '50%', display: 'inline-block' },
  stats: { display: 'flex', gap: 12, marginLeft: 'auto', fontSize: 12, color: 'var(--text-secondary)' },
};
