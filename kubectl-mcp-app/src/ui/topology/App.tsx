import React, { useState, useRef, useCallback } from 'react';
import { ClusterScene } from './components/ClusterScene';
import type { ClusterSceneHandle } from './components/ClusterScene';
import { InspectorSidebar } from './components/InspectorSidebar';
import { FilterBar } from './components/FilterBar';
import { Minimap } from './components/Minimap';
import { useClusterData } from './hooks/useClusterData';
import { baseStyles, getTheme, setTheme as saveTheme, type Theme } from '@shared/theme';

export function TopologyApp(): React.ReactElement {
  const [theme, setThemeState] = useState<Theme>(getTheme());
  const [selectedNamespace, setSelectedNamespace] = useState('');
  const [selectedKinds, setSelectedKinds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [describeOutput, setDescribeOutput] = useState<string | null>(null);
  const [describeLoading, setDescribeLoading] = useState(false);
  const [dismissedError, setDismissedError] = useState(false);
  const sceneRef = useRef<ClusterSceneHandle>(null);

  const { nodes, edges, resources, namespaces, kinds, loading, error, refresh, describeResource } = useClusterData(selectedNamespace, selectedKinds, searchQuery);

  const selectedResource = selectedId ? resources.get(selectedId) || null : null;

  const toggleTheme = useCallback(() => {
    const next = theme === 'dark' ? 'light' : 'dark';
    saveTheme(next);
    setThemeState(next);
  }, [theme]);

  const handleKindToggle = useCallback((kind: string) => {
    setSelectedKinds(prev => {
      const next = new Set(prev);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      return next;
    });
  }, []);

  const handleSelect = useCallback((id: string | null) => {
    setSelectedId(id);
    setDescribeOutput(null);
  }, []);

  const handleDescribe = useCallback(async (resource: { id: string; kind: string; name: string; namespace: string }) => {
    setDescribeLoading(true);
    try {
      const output = await describeResource(resource as Parameters<typeof describeResource>[0]);
      setDescribeOutput(output);
    } catch (err) {
      setDescribeOutput(err instanceof Error ? err.message : 'Failed to describe resource');
    } finally {
      setDescribeLoading(false);
    }
  }, [describeResource]);

  return (
    <div className="app" data-theme={theme}>
      <style>{baseStyles}</style>
      <style>{appStyles}</style>

      <header className="top-bar">
        <div className="top-bar-left">
          <h1>3D Cluster Topology</h1>
        </div>
        <div className="top-bar-right">
          <button className="btn-icon" onClick={() => { setDismissedError(false); refresh(); }} title="Refresh">{'\u21BB'}</button>
          <button className="btn-icon" onClick={() => sceneRef.current?.resetCamera()} title="Reset Camera">{'\u2302'}</button>
          <button className="btn-icon" onClick={toggleTheme} title="Toggle Theme">
            {theme === 'dark' ? '\u2600' : '\u263D'}
          </button>
        </div>
      </header>

      <FilterBar
        namespaces={namespaces}
        selectedNamespace={selectedNamespace}
        onNamespaceChange={setSelectedNamespace}
        kinds={kinds}
        selectedKinds={selectedKinds}
        onKindToggle={handleKindToggle}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        resourceCount={nodes.length}
        edgeCount={edges.length}
      />

      {error && !dismissedError && (
        <div className="error-banner">
          {error}
          <button onClick={() => setDismissedError(true)} title="Dismiss">{'\u2715'}</button>
          <button onClick={() => { setDismissedError(false); refresh(); }} title="Retry">{'\u21BB'}</button>
        </div>
      )}

      <main className="main-content">
        {loading ? (
          <div className="loading-state">Loading cluster topology...</div>
        ) : (
          <>
            <div className="scene-container">
              <ClusterScene
                ref={sceneRef}
                nodes={nodes}
                edges={edges}
                selectedId={selectedId}
                onSelect={handleSelect}
                onHover={() => {}}
                theme={theme}
              />
              <Minimap nodes={nodes} edges={edges} selectedId={selectedId} />
            </div>
            <div className="inspector-panel">
              <InspectorSidebar
                resource={selectedResource ?? null}
                onDescribe={handleDescribe}
                describeOutput={describeOutput}
                describeLoading={describeLoading}
              />
            </div>
          </>
        )}
      </main>
    </div>
  );
}

const appStyles = `
  .app { min-height: 100vh; display: flex; flex-direction: column; }
  .top-bar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 20px; background: var(--bg-secondary); border-bottom: 1px solid var(--border);
  }
  .top-bar-left { display: flex; align-items: center; gap: 12px; }
  .top-bar-left h1 { font-size: 18px; font-weight: 600; }
  .top-bar-right { display: flex; gap: 8px; }
  .btn-icon {
    width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;
    background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 6px;
    cursor: pointer; font-size: 16px; color: var(--text);
  }
  .btn-icon:hover { background: var(--border); }
  .error-banner {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 20px; background: var(--error-bg); color: var(--error);
  }
  .error-banner button { background: none; border: none; color: var(--error); cursor: pointer; font-size: 16px; }
  .main-content { flex: 1; display: flex; overflow: hidden; }
  .loading-state {
    display: flex; align-items: center; justify-content: center;
    flex: 1; color: var(--text-muted);
  }
  .scene-container { flex: 1; position: relative; overflow: hidden; }
  .inspector-panel {
    width: 340px; background: var(--bg-secondary); border-left: 1px solid var(--border);
    overflow-y: auto;
  }
  @media (max-width: 900px) {
    .main-content { flex-direction: column; }
    .inspector-panel { width: 100%; max-height: 300px; border-left: none; border-top: 1px solid var(--border); }
  }
`;

export default TopologyApp;
