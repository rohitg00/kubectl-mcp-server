import React from 'react';
import type { K8sResource } from '../lib/types';

interface InspectorSidebarProps {
  resource: K8sResource | null;
  onDescribe: (resource: K8sResource) => void;
  describeOutput: string | null;
  describeLoading: boolean;
}

const KIND_ICONS: Record<string, string> = {
  Pod: '\u2B22', Deployment: '\u25A3', ReplicaSet: '\u25A4', StatefulSet: '\u2B23',
  DaemonSet: '\u2605', Service: '\u25CF', Ingress: '\u25C7', ConfigMap: '\u25A6',
  Secret: '\u26BF', PersistentVolumeClaim: '\u25AE', HPA: '\u25D4', Node: '\u25A1',
  Namespace: '\u25AD', Job: '\u231B', CronJob: '\u231A', NetworkPolicy: '\u26E8',
};

const STATUS_COLORS: Record<string, string> = {
  Running: 'var(--success)', Pending: 'var(--warning)', Failed: 'var(--error)',
  CrashLoopBackOff: 'var(--error)', Succeeded: 'var(--success)', Active: 'var(--info)',
  Available: 'var(--success)', Progressing: 'var(--info)', Bound: 'var(--success)',
  Terminating: 'var(--text-muted)', Unknown: 'var(--text-muted)',
};

export function InspectorSidebar({ resource, onDescribe, describeOutput, describeLoading }: InspectorSidebarProps): React.ReactElement {
  if (!resource) {
    return (
      <div style={styles.empty}>
        <div style={styles.emptyIcon}>{'\u25CE'}</div>
        <p>Click on a resource to inspect</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.kindIcon}>{KIND_ICONS[resource.kind] || '\u25A0'}</span>
        <div>
          <h2 style={styles.name}>{resource.name}</h2>
          <span style={styles.kind}>{resource.kind}</span>
        </div>
      </div>

      <div style={styles.statusRow}>
        <span style={styles.label}>Status</span>
        <span style={{ ...styles.statusBadge, color: STATUS_COLORS[resource.status] || 'var(--text)' }}>{resource.status}</span>
      </div>

      <div style={styles.row}><span style={styles.label}>Namespace</span><span style={styles.value}>{resource.namespace}</span></div>

      {resource.clusterIP && <div style={styles.row}><span style={styles.label}>Cluster IP</span><span style={styles.mono}>{resource.clusterIP}</span></div>}
      {resource.type && <div style={styles.row}><span style={styles.label}>Type</span><span style={styles.value}>{resource.type}</span></div>}
      {resource.nodeName && <div style={styles.row}><span style={styles.label}>Node</span><span style={styles.value}>{resource.nodeName}</span></div>}
      {resource.replicas !== undefined && <div style={styles.row}><span style={styles.label}>Replicas</span><span style={styles.value}>{resource.readyReplicas ?? 0}/{resource.replicas}</span></div>}

      {resource.ports && resource.ports.length > 0 && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Ports</h3>
          {resource.ports.map((p, i) => (
            <div key={i} style={styles.portItem}>{p.port} {'\u2192'} {p.targetPort}/{p.protocol}</div>
          ))}
        </div>
      )}

      {resource.labels && Object.keys(resource.labels).length > 0 && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Labels</h3>
          <div style={styles.labelList}>
            {Object.entries(resource.labels).slice(0, 8).map(([k, v]) => (
              <div key={k} style={styles.labelItem}><span style={styles.labelKey}>{k}</span><span style={styles.labelVal}>{v}</span></div>
            ))}
          </div>
        </div>
      )}

      {resource.containerStatuses && resource.containerStatuses.length > 0 && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Containers</h3>
          {resource.containerStatuses.map((c, i) => (
            <div key={i} style={styles.containerItem}>
              <span style={{ color: c.ready ? 'var(--success)' : 'var(--error)' }}>{c.ready ? '\u2713' : '\u2717'}</span>
              <span>{c.name}</span>
              {c.restartCount > 0 && <span style={styles.restarts}>{c.restartCount} restarts</span>}
            </div>
          ))}
        </div>
      )}

      <button style={styles.describeBtn} onClick={() => onDescribe(resource)} disabled={describeLoading}>
        {describeLoading ? 'Loading...' : 'kubectl describe'}
      </button>

      {describeOutput && (
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>Describe Output</h3>
          <pre style={styles.describeOutput}>{describeOutput}</pre>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { padding: 20, overflowY: 'auto', height: '100%', display: 'flex', flexDirection: 'column', gap: 12 },
  empty: { display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', gap: 12 },
  emptyIcon: { fontSize: 48, opacity: 0.3 },
  header: { display: 'flex', alignItems: 'center', gap: 12, paddingBottom: 12, borderBottom: '1px solid var(--border)' },
  kindIcon: { fontSize: 28, color: 'var(--primary)' },
  name: { fontSize: 16, fontWeight: 600, wordBreak: 'break-word' as const },
  kind: { fontSize: 12, color: 'var(--text-secondary)' },
  statusRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  statusBadge: { fontWeight: 600, fontSize: 13 },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  label: { fontSize: 12, color: 'var(--text-secondary)' },
  value: { fontSize: 13 },
  mono: { fontSize: 12, fontFamily: 'monospace' },
  section: { marginTop: 8 },
  sectionTitle: { fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' as const, letterSpacing: 0.5, marginBottom: 6 },
  portItem: { padding: '4px 8px', background: 'var(--bg-tertiary)', borderRadius: 4, fontSize: 12, fontFamily: 'monospace', marginBottom: 4 },
  labelList: { display: 'flex', flexDirection: 'column', gap: 4 },
  labelItem: { display: 'flex', gap: 0 },
  labelKey: { padding: '2px 6px', background: 'var(--primary)', color: '#fff', borderRadius: '4px 0 0 4px', fontSize: 11, fontFamily: 'monospace' },
  labelVal: { padding: '2px 6px', background: 'var(--bg-tertiary)', borderRadius: '0 4px 4px 0', fontSize: 11, fontFamily: 'monospace' },
  containerItem: { display: 'flex', gap: 8, alignItems: 'center', padding: '4px 8px', background: 'var(--bg-tertiary)', borderRadius: 4, fontSize: 12, marginBottom: 4 },
  restarts: { marginLeft: 'auto', color: 'var(--warning)', fontSize: 11 },
  describeBtn: { padding: '8px 16px', background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 6, color: 'var(--text)', cursor: 'pointer', fontSize: 13, fontFamily: 'monospace' },
  describeOutput: { padding: 12, background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 11, fontFamily: 'monospace', maxHeight: 300, overflow: 'auto', whiteSpace: 'pre-wrap' as const, lineHeight: 1.4 },
};
