import React, { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { MeshFactory } from '../lib/meshFactory';
import type { GraphNode, GraphEdge } from '../lib/types';

const BACKGROUND_DARK = 0x0d1117;
const BACKGROUND_LIGHT = 0xffffff;
const K8S_BLUE = 0x326ce5;
const GRID_SIZE = 40;
const GRID_DIVISIONS = 20;
const SELECT_COLOR = 0xffa657;

export interface ClusterSceneHandle {
  focusResource: (id: string) => void;
  resetCamera: () => void;
}

interface ClusterSceneProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  onHover: (id: string | null) => void;
  theme: 'dark' | 'light';
}

export const ClusterScene = forwardRef<ClusterSceneHandle, ClusterSceneProps>(function ClusterScene(
  { nodes, edges, selectedId, onSelect, onHover, theme },
  ref
) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<{
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    renderer: THREE.WebGLRenderer;
    controls: OrbitControls;
    raycaster: THREE.Raycaster;
    mouse: THREE.Vector2;
    meshFactory: MeshFactory;
    resourceMeshes: Map<string, THREE.Group>;
    connectionLines: Map<string, THREE.Line>;
    lineGroup: THREE.Group;
    pickableObjects: THREE.Object3D[];
    groundPlane: THREE.Plane;
    frameId: number | null;
    lastTime: number;
    hoveredId: string | null;
    dragging: { id: string; startMouse: THREE.Vector2 } | null;
    didDrag: boolean;
    ambientLight: THREE.AmbientLight;
    gridGroup: THREE.Group;
  } | null>(null);

  const onSelectRef = useRef(onSelect);
  const onHoverRef = useRef(onHover);

  onSelectRef.current = onSelect;
  onHoverRef.current = onHover;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(theme === 'dark' ? BACKGROUND_DARK : BACKGROUND_LIGHT);
    scene.fog = new THREE.FogExp2(theme === 'dark' ? BACKGROUND_DARK : BACKGROUND_LIGHT, 0.006);

    const camera = new THREE.PerspectiveCamera(45, canvas.clientWidth / canvas.clientHeight, 0.1, 500);
    camera.position.set(18, 14, 18);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;

    const controls = new OrbitControls(camera, canvas);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.8;
    controls.zoomSpeed = 1.2;
    controls.panSpeed = 0.8;
    controls.minDistance = 5;
    controls.maxDistance = 80;
    controls.maxPolarAngle = Math.PI / 2.1;
    controls.minPolarAngle = 0.1;
    controls.target.set(0, 0, 0);
    controls.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN };

    const ambientLight = new THREE.AmbientLight(0x8899bb, 0.7);
    scene.add(ambientLight);
    scene.add(new THREE.HemisphereLight(0x88aaff, 0x222244, 0.4));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
    dirLight.position.set(20, 40, 20);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.set(2048, 2048);
    dirLight.shadow.camera.left = -40;
    dirLight.shadow.camera.right = 40;
    dirLight.shadow.camera.top = 40;
    dirLight.shadow.camera.bottom = -40;
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far = 100;
    dirLight.shadow.bias = -0.001;
    scene.add(dirLight);
    scene.add(new THREE.DirectionalLight(K8S_BLUE, 0.4).translateX(-15).translateY(10).translateZ(-15));
    scene.add(new THREE.DirectionalLight(0x446688, 0.3).translateX(-10).translateY(5).translateZ(20));

    const gridGroup = new THREE.Group();
    const gridMat = new THREE.LineBasicMaterial({ color: K8S_BLUE, transparent: true, opacity: 0.1 });
    const halfSize = GRID_SIZE / 2;
    const step = GRID_SIZE / GRID_DIVISIONS;
    const verts: number[] = [];
    for (let i = -halfSize; i <= halfSize; i += step) {
      verts.push(i, 0, -halfSize, i, 0, halfSize);
      verts.push(-halfSize, 0, i, halfSize, 0, i);
    }
    const gridGeom = new THREE.BufferGeometry();
    gridGeom.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
    gridGroup.add(new THREE.LineSegments(gridGeom, gridMat));

    const axesMat = new THREE.LineBasicMaterial({ color: K8S_BLUE, transparent: true, opacity: 0.25 });
    const axesGeom = new THREE.BufferGeometry();
    axesGeom.setAttribute('position', new THREE.Float32BufferAttribute([-halfSize, 0, 0, halfSize, 0, 0, 0, 0, -halfSize, 0, 0, halfSize], 3));
    gridGroup.add(new THREE.LineSegments(axesGeom, axesMat));

    const groundGeom = new THREE.PlaneGeometry(GRID_SIZE * 1.5, GRID_SIZE * 1.5);
    const groundMat = new THREE.MeshStandardMaterial({ color: 0x0a0e14, metalness: 0.9, roughness: 0.2, transparent: true, opacity: 0.15 });
    const ground = new THREE.Mesh(groundGeom, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.1;
    ground.receiveShadow = true;
    gridGroup.add(ground);
    scene.add(gridGroup);

    const lineGroup = new THREE.Group();
    scene.add(lineGroup);

    const state = {
      scene, camera, renderer, controls,
      raycaster: new THREE.Raycaster(),
      mouse: new THREE.Vector2(-999, -999),
      meshFactory: new MeshFactory(),
      resourceMeshes: new Map<string, THREE.Group>(),
      connectionLines: new Map<string, THREE.Line>(),
      lineGroup,
      pickableObjects: [] as THREE.Object3D[],
      groundPlane: new THREE.Plane(new THREE.Vector3(0, 1, 0), 0),
      frameId: null as number | null,
      lastTime: performance.now(),
      hoveredId: null as string | null,
      dragging: null as { id: string; startMouse: THREE.Vector2 } | null,
      didDrag: false,
      ambientLight,
      gridGroup,
    };

    sceneRef.current = state;

    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      state.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      state.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
      if (state.dragging) {
        state.raycaster.setFromCamera(state.mouse, state.camera);
        const intersection = new THREE.Vector3();
        if (state.raycaster.ray.intersectPlane(state.groundPlane, intersection)) {
          const group = state.resourceMeshes.get(state.dragging.id);
          if (group) {
            group.position.x = intersection.x;
            group.position.z = intersection.z;
          }
        }
      }
      const dx = e.clientX - (state.dragging?.startMouse.x ?? e.clientX);
      const dy = e.clientY - (state.dragging?.startMouse.y ?? e.clientY);
      if (Math.sqrt(dx * dx + dy * dy) > 4) state.didDrag = true;
    };

    const onMouseDown = (e: MouseEvent) => {
      if (e.button !== 0) return;
      state.didDrag = false;
      state.raycaster.setFromCamera(state.mouse, state.camera);
      const hits = state.raycaster.intersectObjects(state.pickableObjects, true);
      if (hits.length > 0) {
        let target: THREE.Object3D = hits[0].object;
        while (target.parent && !target.userData.resourceId) target = target.parent;
        if (target.userData.resourceId) {
          state.dragging = { id: target.userData.resourceId, startMouse: new THREE.Vector2(e.clientX, e.clientY) };
          state.controls.enabled = false;
          canvas.style.cursor = 'grabbing';
        }
      }
    };

    const onMouseUp = (e: MouseEvent) => {
      if (state.dragging) {
        state.controls.enabled = true;
        canvas.style.cursor = 'default';
        state.dragging = null;
        state.didDrag = false;
        return;
      }
      if (e.button === 0 && !state.didDrag) {
        state.raycaster.setFromCamera(state.mouse, state.camera);
        const hits = state.raycaster.intersectObjects(state.pickableObjects, true);
        if (hits.length > 0) {
          let target: THREE.Object3D = hits[0].object;
          while (target.parent && !target.userData.resourceId) target = target.parent;
          if (target.userData.resourceId) {
            onSelectRef.current(target.userData.resourceId);
            return;
          }
        }
        onSelectRef.current(null);
      }
      state.didDrag = false;
    };

    const onResize = () => {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      state.renderer.setSize(w, h);
      state.camera.aspect = w / h;
      state.camera.updateProjectionMatrix();
    };

    const onContextMenu = (e: MouseEvent) => e.preventDefault();

    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('mousedown', onMouseDown);
    canvas.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('contextmenu', onContextMenu);
    window.addEventListener('resize', onResize);

    const animate = () => {
      state.frameId = requestAnimationFrame(animate);
      const now = performance.now();
      const delta = (now - state.lastTime) / 1000;
      state.lastTime = now;
      state.controls.update();

      if (!state.didDrag && !state.dragging) {
        state.raycaster.setFromCamera(state.mouse, state.camera);
        const hits = state.raycaster.intersectObjects(state.pickableObjects, true);
        let newHover: string | null = null;
        if (hits.length > 0) {
          let target: THREE.Object3D = hits[0].object;
          while (target.parent && !target.userData.resourceId) target = target.parent;
          if (target.userData.resourceId) newHover = target.userData.resourceId;
        }
        if (newHover !== state.hoveredId) {
          state.hoveredId = newHover;
          canvas.style.cursor = newHover ? 'pointer' : 'default';
          onHoverRef.current(newHover);
        }
      }

      for (const line of state.connectionLines.values()) {
        line.userData.flowOffset = (line.userData.flowOffset || 0) + (line.userData.flowSpeed || 2) * delta;
        const distances = line.geometry.attributes.lineDistance;
        if (distances) {
          const arr = distances.array as Float32Array;
          const total = arr[arr.length - 1];
          const offset = line.userData.flowOffset;
          for (let i = 0; i < arr.length; i++) {
            arr[i] = ((arr[i] / total) * total + offset) % (total + 0.45);
          }
          (distances as THREE.BufferAttribute).needsUpdate = true;
        }
      }

      const time = performance.now() * 0.001;
      for (const [id, group] of state.resourceMeshes) {
        if (group.userData.resourceType === 'Pod') {
          group.position.y = (group.userData.baseY || 0) + Math.sin(time * 2 + id.charCodeAt(0)) * 0.08;
        }
        if (group.userData.animate) {
          group.userData.animate(time, delta);
        }
      }

      state.renderer.render(state.scene, state.camera);
    };
    animate();

    return () => {
      if (state.frameId) cancelAnimationFrame(state.frameId);
      canvas.removeEventListener('mousemove', onMouseMove);
      canvas.removeEventListener('mousedown', onMouseDown);
      canvas.removeEventListener('mouseup', onMouseUp);
      canvas.removeEventListener('contextmenu', onContextMenu);
      window.removeEventListener('resize', onResize);
      state.controls.dispose();
      for (const group of state.resourceMeshes.values()) {
        state.meshFactory.dispose(group);
        state.scene.remove(group);
      }
      for (const line of state.connectionLines.values()) {
        line.geometry.dispose();
        (line.material as THREE.Material).dispose();
      }
      state.renderer.dispose();
    };
  }, []);

  useEffect(() => {
    const s = sceneRef.current;
    if (!s) return;
    const bg = theme === 'dark' ? BACKGROUND_DARK : BACKGROUND_LIGHT;
    s.scene.background = new THREE.Color(bg);
    if (s.scene.fog instanceof THREE.FogExp2) s.scene.fog.color.set(bg);
  }, [theme]);

  useEffect(() => {
    const s = sceneRef.current;
    if (!s) return;

    const currentIds = new Set(s.resourceMeshes.keys());
    const newIds = new Set(nodes.map(n => n.id));

    for (const node of nodes) {
      if (currentIds.has(node.id)) {
        const group = s.resourceMeshes.get(node.id)!;
        group.position.x = node.x;
        group.position.z = node.z;
        if (node.kind !== 'Pod') group.position.y = node.y;
        s.meshFactory.updateStatus(group, node.status);
      } else {
        const group = s.meshFactory.create({ name: node.name, status: node.status, kind: node.kind, replicas: node.resource.replicas, currentUtilization: node.resource.currentUtilization, y: node.y });
        if (!group) continue;
        group.userData.resourceId = node.id;
        group.userData.resourceType = node.kind;
        group.userData.baseY = node.y;
        group.position.set(node.x, node.y, node.z);
        group.traverse((child: THREE.Object3D) => {
          if ((child as THREE.Mesh).isMesh) {
            child.userData.resourceId = node.id;
            child.userData.originalScale = (child as THREE.Mesh).scale.clone();
            (child as THREE.Mesh).castShadow = true;
            const mat = (child as THREE.Mesh).material as THREE.MeshStandardMaterial;
            if (mat?.emissive) {
              child.userData.baseEmissive = mat.emissive.clone();
              child.userData.baseEmissiveIntensity = mat.emissiveIntensity;
            }
          }
        });
        s.scene.add(group);
        s.resourceMeshes.set(node.id, group);
      }
    }

    for (const id of currentIds) {
      if (!newIds.has(id)) {
        const group = s.resourceMeshes.get(id)!;
        s.scene.remove(group);
        s.meshFactory.dispose(group);
        s.resourceMeshes.delete(id);
      }
    }

    s.pickableObjects = [];
    for (const group of s.resourceMeshes.values()) {
      group.traverse((child: THREE.Object3D) => {
        if ((child as THREE.Mesh).isMesh && !child.userData.isLabel) {
          s.pickableObjects.push(child);
        }
      });
    }
  }, [nodes]);

  useEffect(() => {
    const s = sceneRef.current;
    if (!s) return;

    const RELATIONSHIP_COLORS: Record<string, number> = {
      ownership: 0xc9d1d9,
      network: 0x58a6ff,
      storage: 0x8b949e,
      config: 0xd29922,
    };

    const newEdgeIds = new Set(edges.map(e => e.id));

    for (const [id, line] of s.connectionLines) {
      if (!newEdgeIds.has(id)) {
        s.lineGroup.remove(line);
        line.geometry.dispose();
        (line.material as THREE.Material).dispose();
        s.connectionLines.delete(id);
      }
    }

    for (const edge of edges) {
      if (s.connectionLines.has(edge.id)) continue;

      const sourceGroup = s.resourceMeshes.get(edge.source);
      const targetGroup = s.resourceMeshes.get(edge.target);
      if (!sourceGroup || !targetGroup) continue;

      const sourcePos = sourceGroup.position.clone();
      const targetPos = targetGroup.position.clone();
      const midpoint = new THREE.Vector3().lerpVectors(sourcePos, targetPos, 0.5);
      const dist = sourcePos.distanceTo(targetPos);
      midpoint.y += Math.min(dist * 0.3, 3);

      const curve = new THREE.QuadraticBezierCurve3(sourcePos, midpoint, targetPos);
      const points = curve.getPoints(32);
      const geometry = new THREE.BufferGeometry().setFromPoints(points);

      const color = RELATIONSHIP_COLORS[edge.type] || 0x6e7681;
      const material = new THREE.LineDashedMaterial({
        color,
        dashSize: 0.3,
        gapSize: 0.15,
        transparent: true,
        opacity: 0.4,
      });

      const line = new THREE.Line(geometry, material);
      line.computeLineDistances();
      line.userData.flowOffset = 0;
      line.userData.flowSpeed = 2.0 * (0.5 + Math.random() * 0.5);
      s.lineGroup.add(line);
      s.connectionLines.set(edge.id, line);
    }
  }, [edges]);

  useEffect(() => {
    const s = sceneRef.current;
    if (!s) return;
    for (const [id, group] of s.resourceMeshes) {
      const isSelected = id === selectedId;
      group.traverse((child: THREE.Object3D) => {
        if (!(child as THREE.Mesh).isMesh || child.userData.isLabel) return;
        const mat = (child as THREE.Mesh).material as THREE.MeshStandardMaterial;
        if (!mat) return;
        if (isSelected) {
          if (mat.emissive) { mat.emissive.set(SELECT_COLOR); mat.emissiveIntensity = 0.5; }
        } else {
          if (child.userData.baseEmissive) {
            mat.emissive.copy(child.userData.baseEmissive);
            mat.emissiveIntensity = child.userData.baseEmissiveIntensity || 0.15;
          }
        }
      });
    }
  }, [selectedId]);

  useImperativeHandle(ref, () => ({
    focusResource(id: string) {
      const s = sceneRef.current;
      if (!s) return;
      const group = s.resourceMeshes.get(id);
      if (group) { s.controls.target.copy(group.position); s.controls.update(); }
    },
    resetCamera() {
      const s = sceneRef.current;
      if (!s) return;
      s.camera.position.set(18, 14, 18);
      s.controls.target.set(0, 0, 0);
      s.controls.update();
    },
  }));

  return <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />;
});
