import React, { useEffect, useRef, useCallback, useMemo, useState } from 'react';
import Graph from 'graphology';
import Sigma from 'sigma';
import { EdgeCurvedArrowProgram } from '@sigma/edge-curve';
import dagre from 'dagre';
import { Zap, RefreshCw, Maximize2, FolderOpen, FolderClosed, Layers } from 'lucide-react';
import useGraphStore from '../../store/useGraphStore';

/* ─── Performance thresholds ─────────────────────────────────── */
const PERF = { LARGE: 200, HUGE: 500, MASSIVE: 1000 };

/* ─── Dagre layout — LR orientation, tighter spacing ─────────── */
function applyDagreLayout(graph) {
    const g = new dagre.graphlib.Graph();
    // LR reads more naturally for codebases; tighter spacing reduces whitespace
    g.setGraph({ rankdir: 'LR', nodesep: 120, ranksep: 220, edgesep: 60 });
    g.setDefaultEdgeLabel(() => ({}));
    graph.forEachNode((id) => g.setNode(id, { width: 160, height: 60 }));
    graph.forEachEdge((key, attrs, src, tgt) => g.setEdge(src, tgt));
    dagre.layout(g);
    g.nodes().forEach((id) => {
        const pos = g.node(id);
        if (pos && graph.hasNode(id)) {
            graph.setNodeAttribute(id, 'x', pos.x);
            graph.setNodeAttribute(id, 'y', pos.y);
        }
    });
}

/* ─── Visual encoding ────────────────────────────────────────── */
const RISK_COLORS = {
    critical: '#ef4444', high: '#f97316', moderate: '#eab308',
    medium: '#eab308', low: '#22c55e', none: '#64748b',
};
const TYPE_COLORS = {
    file: '#3b82f6', function: '#10b981', class: '#6366f1',
    module: '#8b5cf6', database: '#f59e0b', external: '#ec4899', api_call: '#f59e0b',
};
const CLUSTER_COLORS = [
    '#3b82f6','#10b981','#f97316','#8b5cf6',
    '#ec4899','#14b8a6','#f59e0b','#6366f1','#ef4444','#22d3ee',
];
const EDGE_COLORS = {
    calls: '#3b82f6', uses_api: '#f59e0b', contains: '#8b5cf6',
    structural: '#6366f1', dependency: '#64748b', depends_on: '#14b8a6', flow: '#ec4899',
};

// Legend metadata — used both for node and edge legends
const RISK_LEGEND = [
    { key: 'critical', label: 'Critical', color: '#ef4444' },
    { key: 'high',     label: 'High',     color: '#f97316' },
    { key: 'moderate', label: 'Moderate', color: '#eab308' },
    { key: 'low',      label: 'Low',      color: '#22c55e' },
    { key: 'none',     label: 'None',     color: '#64748b' },
];
const EDGE_LEGEND = [
    { key: 'calls',      label: 'Calls',      color: '#3b82f6' },
    { key: 'contains',   label: 'Contains',   color: '#8b5cf6' },
    { key: 'depends_on', label: 'Imports',    color: '#14b8a6' },
    { key: 'uses_api',   label: 'Uses API',   color: '#f59e0b' },
    { key: 'flow',       label: 'Data Flow',  color: '#ec4899' },
    { key: 'structural', label: 'Structural', color: '#6366f1' },
];

/* ─── Helpers ────────────────────────────────────────────────── */
function basename(fp) { return fp ? fp.replace(/\\/g,'/').split('/').pop() || fp : 'unknown'; }
function truncate(s, n = 24) { return s && s.length > n ? s.slice(0, n - 1) + '…' : s; }
function aggregateRisk(nodes) {
    const p = { critical:5, high:4, moderate:3, medium:3, low:2, none:1 };
    let mx = 0, mr = 'none';
    for (const n of nodes) { const r = n.risk_level||n.risk||'none'; if((p[r]||0)>mx){mx=p[r]||0;mr=r;} }
    return mr;
}
function getNodeSize(n) {
    // Larger range: 8–32px (was 5–18px). Risk tier adds a visible bump.
    if (n._isFileNode) return Math.max(18, Math.min(36, Math.sqrt(n._childCount) * 8));
    const loc = n.loc || 10;
    const r = n.risk_level || n.risk || 'none';
    let b = Math.max(8, Math.min(24, Math.sqrt(loc) * 2));
    if (r === 'critical') b *= 1.6;
    else if (r === 'high') b *= 1.35;
    else if (r === 'moderate') b *= 1.15;
    if (n.type === 'module') b *= 1.2;
    return b;
}

/* ─── Toolbar button ─────────────────────────────────────────── */
const ToolBtn = ({ onClick, active, activeStyle, children, label }) => (
    <button
        onClick={onClick}
        aria-label={label}
        aria-pressed={active}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
        style={active ? activeStyle : {
            background: 'rgba(10,15,30,0.82)',
            border: '1px solid rgba(255,255,255,0.1)',
            color: '#94a3b8',
            backdropFilter: 'blur(8px)',
        }}
        onMouseEnter={e => { if (!active) e.currentTarget.style.color = '#e2e8f0'; }}
        onMouseLeave={e => { if (!active) e.currentTarget.style.color = '#94a3b8'; }}
    >
        {children}
    </button>
);

/* ─── Minimap ────────────────────────────────────────────────── */
// Lightweight canvas-based minimap — no external plugin needed.
// Renders a scaled-down version of all nodes and the current viewport rect.
const Minimap = ({ graphRef, sigmaRef }) => {
    const canvasRef = useRef(null);
    const rafRef    = useRef(null);

    useEffect(() => {
        const canvas  = canvasRef.current;
        const sigma   = sigmaRef.current;
        const graph   = graphRef.current;
        if (!canvas || !sigma || !graph || graph.order === 0) return;

        const W = canvas.width  = canvas.offsetWidth  * window.devicePixelRatio;
        const H = canvas.height = canvas.offsetHeight * window.devicePixelRatio;
        const ctx = canvas.getContext('2d');

        const draw = () => {
            ctx.clearRect(0, 0, W, H);

            // Compute bounding box of all nodes in graph-space
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            graph.forEachNode((id, attrs) => {
                if (attrs.x < minX) minX = attrs.x;
                if (attrs.x > maxX) maxX = attrs.x;
                if (attrs.y < minY) minY = attrs.y;
                if (attrs.y > maxY) maxY = attrs.y;
            });
            const pad = 20;
            const gW = (maxX - minX) || 1;
            const gH = (maxY - minY) || 1;

            const toMX = (x) => ((x - minX) / gW) * (W - pad * 2) + pad;
            const toMY = (y) => ((y - minY) / gH) * (H - pad * 2) + pad;

            // Draw edges
            ctx.globalAlpha = 0.25;
            graph.forEachEdge((key, attrs, src, tgt, srcAttrs, tgtAttrs) => {
                ctx.strokeStyle = attrs.color || '#475569';
                ctx.lineWidth   = 0.8;
                ctx.beginPath();
                ctx.moveTo(toMX(srcAttrs.x), toMY(srcAttrs.y));
                ctx.lineTo(toMX(tgtAttrs.x), toMY(tgtAttrs.y));
                ctx.stroke();
            });

            // Draw nodes
            ctx.globalAlpha = 1;
            graph.forEachNode((id, attrs) => {
                const r = Math.max(2, (attrs.size || 6) * 0.35);
                ctx.fillStyle = attrs.color || '#64748b';
                ctx.beginPath();
                ctx.arc(toMX(attrs.x), toMY(attrs.y), r, 0, Math.PI * 2);
                ctx.fill();
            });

            // Draw viewport rectangle
            try {
                const cam    = sigma.getCamera();
                const extent = sigma.getGraphExtent?.() || { x: [minX, maxX], y: [minY, maxY] };
                const { x: cx, y: cy, ratio } = cam.getState();

                // Map camera center back to graph coords
                const vpW = sigma.getContainer().offsetWidth;
                const vpH = sigma.getContainer().offsetHeight;
                const halfW = (vpW / 2)  * ratio;
                const halfH = (vpH / 2) * ratio;

                const rx = toMX(cx - halfW);
                const ry = toMY(cy - halfH);
                const rw = toMX(cx + halfW) - rx;
                const rh = toMY(cy + halfH) - ry;

                ctx.strokeStyle = 'rgba(99,102,241,0.8)';
                ctx.lineWidth   = 1.5;
                ctx.strokeRect(rx, ry, rw, rh);
                ctx.fillStyle   = 'rgba(99,102,241,0.08)';
                ctx.fillRect(rx, ry, rw, rh);
            } catch { /* camera not ready */ }

            rafRef.current = requestAnimationFrame(draw);
        };

        draw();
        return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
    }, [graphRef, sigmaRef]);

    return (
        <canvas
            ref={canvasRef}
            style={{
                width:  '100%',
                height: '100%',
                display: 'block',
            }}
            aria-hidden="true"
        />
    );
};

/* ─── Legend overlay ─────────────────────────────────────────── */
const Legend = ({ colorMode }) => (
    <div
        className="absolute bottom-3 left-3 z-10 flex flex-col gap-2 pointer-events-none"
        aria-label="Graph legend"
        role="img"
    >
        {/* Node color legend */}
        <div
            className="px-3 py-2 rounded-xl text-[10px]"
            style={{
                background: 'rgba(10,15,30,0.85)',
                border: '1px solid rgba(255,255,255,0.09)',
                backdropFilter: 'blur(8px)',
                minWidth: 130,
            }}
        >
            <div className="text-slate-500 font-bold uppercase tracking-wider mb-1.5">
                {colorMode === 'cluster' ? 'Clusters' : 'Risk Level'}
            </div>
            {colorMode !== 'cluster' && RISK_LEGEND.map(({ key, label, color }) => (
                <div key={key} className="flex items-center gap-2 py-0.5">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: color }} />
                    <span className="text-slate-300">{label}</span>
                </div>
            ))}
            {colorMode === 'cluster' && CLUSTER_COLORS.slice(0, 5).map((color, i) => (
                <div key={i} className="flex items-center gap-2 py-0.5">
                    <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: color }} />
                    <span className="text-slate-300">Cluster {i + 1}</span>
                </div>
            ))}
        </div>

        {/* Edge type legend */}
        <div
            className="px-3 py-2 rounded-xl text-[10px]"
            style={{
                background: 'rgba(10,15,30,0.85)',
                border: '1px solid rgba(255,255,255,0.09)',
                backdropFilter: 'blur(8px)',
                minWidth: 130,
            }}
        >
            <div className="text-slate-500 font-bold uppercase tracking-wider mb-1.5">Edge Type</div>
            {EDGE_LEGEND.map(({ key, label, color }) => (
                <div key={key} className="flex items-center gap-2 py-0.5">
                    <span className="flex-shrink-0 w-5 h-0.5 rounded-full" style={{ background: color }} />
                    <span className="text-slate-300">{label}</span>
                </div>
            ))}
        </div>
    </div>
);

/* ═══════════════════════════════════════════════════════════════ */
const SigmaRenderer = ({ nodes, edges }) => {
    const containerRef = useRef(null);
    const sigmaRef     = useRef(null);
    const graphRef     = useRef(null);

    const selectNode          = useGraphStore((s) => s.selectNode);
    const setGraphData        = useGraphStore((s) => s.setGraphData);
    const setHoveredNode      = useGraphStore((s) => s.setHoveredNode);
    const selectedNodeId      = useGraphStore((s) => s.selectedNodeId);
    const hoveredNodeId       = useGraphStore((s) => s.hoveredNodeId);
    const filters             = useGraphStore((s) => s.filters);
    const expandedFiles       = useGraphStore((s) => s.expandedFiles);
    const toggleFileExpansion = useGraphStore((s) => s.toggleFileExpansion);
    const collapseAll         = useGraphStore((s) => s.collapseAll);
    const expandAll           = useGraphStore((s) => s.expandAll);
    const colorMode           = useGraphStore((s) => s.colorMode);
    const setColorMode        = useGraphStore((s) => s.setColorMode);
    const highlightedClusterId = useGraphStore((s) => s.highlightedClusterId);

    const selectedRef = useRef(null);
    const hoveredRef  = useRef(null);

    const nodeCount      = useMemo(() => nodes.length, [nodes.length]);
    const isLargeGraph   = nodeCount > PERF.LARGE;
    const isHugeGraph    = nodeCount > PERF.HUGE;
    const isMassiveGraph = nodeCount > PERF.MASSIVE;

    useEffect(() => { selectedRef.current = selectedNodeId; sigmaRef.current?.refresh(); }, [selectedNodeId]);
    useEffect(() => { hoveredRef.current  = hoveredNodeId;  sigmaRef.current?.refresh(); }, [hoveredNodeId]);

    /* ── Drill-down visibility ─────────────────────────────── */
    const { visibleNodes, visibleEdges } = useMemo(() => {
        const byFile = {};
        for (const n of nodes) { const f = n.file||'unknown'; (byFile[f]||(byFile[f]=[])).push(n); }

        const vNodes = [];
        const fileNodeIds = {};

        for (const [fp, children] of Object.entries(byFile)) {
            const fileId = `__file__${fp}`;
            fileNodeIds[fp] = new Set(children.map(c => c.id));
            // Raise collapse threshold to 4 — small files stay expanded by default
            if (children.length <= 3 || expandedFiles.has(fp)) {
                for (const c of children) vNodes.push(c);
            } else {
                vNodes.push({
                    id: fileId, name: basename(fp), type: 'file', file: fp,
                    risk_level: aggregateRisk(children),
                    loc: children.reduce((a, c) => a + (c.loc || 10), 0),
                    _isFileNode: true, _childCount: children.length, _filePath: fp,
                    node_summary: `File with ${children.length} nodes. Highest risk: ${aggregateRisk(children)}.`,
                    architectural_role: 'file',
                });
            }
        }

        const nodeIdToFileId = {};
        for (const [fp, ids] of Object.entries(fileNodeIds)) {
            if (!expandedFiles.has(fp) && [...ids].length > 3) {
                const fid = `__file__${fp}`;
                for (const id of ids) nodeIdToFileId[id] = fid;
            }
        }

        const visibleIds = new Set(vNodes.map(n => n.id));
        const seen = new Set(); const vEdges = [];
        for (const e of edges) {
            let src = nodeIdToFileId[e.source] || e.source;
            let tgt = nodeIdToFileId[e.target] || e.target;
            if (src === tgt || !visibleIds.has(src) || !visibleIds.has(tgt)) continue;
            const k = `${src}__${tgt}__${e.type||'calls'}`;
            if (seen.has(k)) continue; seen.add(k);
            vEdges.push({ ...e, source: src, target: tgt });
        }
        return { visibleNodes: vNodes, visibleEdges: vEdges };
    }, [nodes, edges, expandedFiles]);

    useEffect(() => {
        if (visibleNodes.length > 0) setGraphData(visibleNodes, visibleEdges);
    }, [visibleNodes, visibleEdges, setGraphData]);

    /* ── Build graphology graph ────────────────────────────── */
    const buildGraph = useCallback(() => {
        const graph   = new Graph();
        const nodeIds = new Set();

        const filtered = visibleNodes.filter(n => {
            const risk = n.risk_level || n.risk || 'none';
            const type = n.type || 'function';
            if (!filters.riskLevels.includes(risk)) return false;
            if (!filters.nodeTypes.includes(type))  return false;
            if (filters.searchQuery && !n.name?.toLowerCase().includes(filters.searchQuery.toLowerCase()) && !n.id?.toLowerCase().includes(filters.searchQuery.toLowerCase())) return false;
            return true;
        });

        filtered.forEach(n => {
            if (graph.hasNode(n.id)) return;
            nodeIds.add(n.id);
            const risk = n.risk_level || n.risk || 'none';
            const type = n.type || 'function';

            const rawLabel = n._isFileNode
                ? (n._childCount === 1 ? n.name : `${n.name}  [${n._childCount}]`)
                : (n.name || n.id);
            const label = truncate(rawLabel, n._isFileNode ? 28 : 24);

            let color;
            if (n._isFileNode) color = TYPE_COLORS.file;
            else if (colorMode === 'cluster' && n.cluster_id != null)
                color = CLUSTER_COLORS[(typeof n.cluster_id === 'number' ? n.cluster_id - 1 : 0) % CLUSTER_COLORS.length];
            else color = RISK_COLORS[risk] || RISK_COLORS.none;

            const isHighlighted = highlightedClusterId === null || n.cluster_id === highlightedClusterId || n._isFileNode;

            graph.addNode(n.id, {
                label,
                x: Math.random() * 200, y: Math.random() * 200,
                size: getNodeSize(n),
                color: isHighlighted ? color : '#1e293b',
                borderColor: TYPE_COLORS[type] || TYPE_COLORS.function,
                type: 'circle',
                _raw: n,
            });
        });

        // Track parallel edges so we can offset curves
        const edgePairCount = {};
        visibleEdges.forEach(e => {
            const et = e.type || e.label || 'calls';
            if (!filters.edgeTypes.includes(et)) return;
            if (filters.riskPathOnly && !e.risk_path) return;
            if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) return;
            if (e.source === e.target) return;
            const pairKey = [e.source, e.target].sort().join('__');
            edgePairCount[pairKey] = (edgePairCount[pairKey] || 0) + 1;
        });

        const edgePairIdx = {};
        visibleEdges.forEach(e => {
            const et = e.type || e.label || 'calls';
            if (!filters.edgeTypes.includes(et)) return;
            if (filters.riskPathOnly && !e.risk_path) return;
            if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) return;
            if (e.source === e.target) return;
            const k = `${e.source}__${e.target}__${et}`;
            if (graph.hasEdge(k)) return;

            const pairKey = [e.source, e.target].sort().join('__');
            const total   = edgePairCount[pairKey] || 1;
            edgePairIdx[pairKey] = (edgePairIdx[pairKey] || 0) + 1;
            const idx = edgePairIdx[pairKey];

            // Curvature: spread parallel edges so they don't overlap
            // Single edges get a slight curve; multiple edges fan out
            const baseCurve = 0.15;
            const curvature = total > 1
                ? baseCurve + (idx - 1) * 0.2 * (idx % 2 === 0 ? -1 : 1)
                : baseCurve;

            try {
                graph.addEdgeWithKey(k, e.source, e.target, {
                    type: 'curved',
                    curvature,
                    color: EDGE_COLORS[et] || '#94a3b8',
                    size: et === 'calls' ? 2.5 : 1.8,
                    label: et,
                });
            } catch { /* skip duplicate */ }
        });

        return graph;
    }, [visibleNodes, visibleEdges, filters, colorMode, highlightedClusterId]);

    /* ── Initialize Sigma ──────────────────────────────────── */
    useEffect(() => {
        if (!containerRef.current) return;
        if (sigmaRef.current) { sigmaRef.current.kill(); sigmaRef.current = null; }

        const graph = buildGraph();
        graphRef.current = graph;
        if (graph.order === 0) return;

        applyDagreLayout(graph);

        const sigma = new Sigma(graph, containerRef.current, {
            renderLabels:               !isMassiveGraph,
            labelRenderedSizeThreshold: isLargeGraph ? 8 : 5,
            labelSize:                  isHugeGraph  ? 12 : 14,
            labelWeight:                'bold',
            labelColor:                 { color: '#e2e8f0' },
            labelFont:                  'Inter, system-ui, sans-serif',
            defaultEdgeType:            'curved',
            defaultNodeColor:           '#64748b',
            defaultEdgeColor:           '#475569',
            minCameraRatio:             isLargeGraph ? 0.01 : 0.02,
            maxCameraRatio:             isLargeGraph ? 10   : 20,
            stagePadding:               isHugeGraph  ? 40   : 60,
            labelDensity:               isHugeGraph  ? 0.3  : 0.6,
            labelGridCellSize:          isHugeGraph  ? 240  : 180,
            enableEdgeEvents:           !isLargeGraph,
            // Register curved edge renderer
            edgeProgramClasses: {
                curved: EdgeCurvedArrowProgram,
            },
            nodeReducer: (node, data) => {
                const res = { ...data };
                const sel = selectedRef.current;
                const hov = hoveredRef.current;
                if (sel) {
                    if (node === sel) { res.highlighted = true; res.zIndex = 2; }
                    else if (graph.hasEdge(sel, node) || graph.hasEdge(node, sel)) { res.highlighted = true; }
                    else { res.color = '#1e293b'; res.label = ''; }
                }
                if (hov && node === hov) {
                    res.highlighted = true;
                    if (sel && node !== sel && !graph.hasEdge(sel, node) && !graph.hasEdge(node, sel))
                        res.label = data.label;
                }
                return res;
            },
            edgeReducer: (edge, data) => {
                const res = { ...data };
                const sel = selectedRef.current;
                if (sel) {
                    const ends = graph.extremities(edge);
                    if (!ends.includes(sel)) res.hidden = true;
                    else { res.size = 3.5; res.color = '#60a5fa'; }
                }
                return res;
            },
        });

        sigma.on('clickNode',       ({ node }) => selectNode(node));
        sigma.on('doubleClickNode', ({ node, event }) => {
            event.original?.preventDefault?.();
            const raw = graph.getNodeAttribute(node, '_raw');
            if (raw?._isFileNode) toggleFileExpansion(raw._filePath);
            else if (raw?.file)   toggleFileExpansion(raw.file);
        });
        sigma.on('clickStage', () => selectNode(null));
        sigma.on('enterNode',  ({ node }) => { setHoveredNode(node);  if (containerRef.current) containerRef.current.style.cursor = 'pointer'; });
        sigma.on('leaveNode',  ()         => { setHoveredNode(null); if (containerRef.current) containerRef.current.style.cursor = 'default'; });

        sigmaRef.current = sigma;
        return () => { if (sigmaRef.current) { sigmaRef.current.kill(); sigmaRef.current = null; } };
    }, [buildGraph]);

    const handleRelayout = useCallback(() => {
        if (!graphRef.current || graphRef.current.order === 0) return;
        applyDagreLayout(graphRef.current);
        sigmaRef.current?.refresh();
    }, []);

    const hasExpanded = expandedFiles.size > 0;

    return (
        <div className="relative w-full h-full" style={{ background: '#0a0f1e' }}>
            {/* Graph canvas */}
            <div
                ref={containerRef}
                className="w-full h-full"
                style={{ minHeight: 500 }}
                role="img"
                aria-label="Interactive code graph. Click nodes to inspect them."
            />

            {/* ── Toolbar overlay ─────────────────────────── */}
            <div
                className="absolute top-3 left-3 z-10 flex flex-col gap-2"
                role="toolbar"
                aria-label="Graph controls"
            >
                {/* Status badge */}
                <div
                    className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-mono"
                    style={{
                        background: 'rgba(10,15,30,0.85)',
                        border: '1px solid rgba(255,255,255,0.09)',
                        backdropFilter: 'blur(8px)',
                        color: '#94a3b8',
                    }}
                    aria-live="polite"
                >
                    <span
                        className="w-2 h-2 rounded-full bg-emerald-500"
                        style={{ boxShadow: '0 0 6px rgba(16,185,129,0.5)' }}
                        aria-hidden="true"
                    />
                    {hasExpanded ? 'Expanded view' : 'File view'}
                    <span className="text-slate-600">·</span>
                    Double-click to {hasExpanded ? 'collapse' : 'expand'}
                </div>

                {/* Action buttons */}
                <div className="flex flex-wrap gap-1.5">
                    {hasExpanded ? (
                        <ToolBtn
                            onClick={() => { collapseAll(); selectNode(null); }}
                            label="Collapse all files"
                            activeStyle={{}}
                        >
                            <FolderClosed className="w-3.5 h-3.5" aria-hidden="true" />
                            Collapse All
                        </ToolBtn>
                    ) : (
                        <ToolBtn onClick={expandAll} label="Expand all files" activeStyle={{}}>
                            <FolderOpen className="w-3.5 h-3.5" aria-hidden="true" />
                            Expand All
                        </ToolBtn>
                    )}

                    <ToolBtn
                        onClick={() => setColorMode(colorMode === 'cluster' ? 'risk' : 'cluster')}
                        active={colorMode === 'cluster'}
                        label={colorMode === 'cluster' ? 'Switch to risk color mode' : 'Switch to cluster color mode'}
                        activeStyle={{
                            background: 'rgba(249,115,22,0.18)',
                            border: '1px solid rgba(249,115,22,0.35)',
                            color: '#fdba74',
                            backdropFilter: 'blur(8px)',
                        }}
                    >
                        <Layers className="w-3.5 h-3.5" aria-hidden="true" />
                        {colorMode === 'cluster' ? 'By Cluster' : 'By Risk'}
                    </ToolBtn>

                    <ToolBtn onClick={handleRelayout} label="Re-run layout">
                        <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
                        Re-layout
                    </ToolBtn>

                    <ToolBtn
                        onClick={() => sigmaRef.current?.getCamera()?.animatedReset()}
                        label="Fit graph to view"
                    >
                        <Maximize2 className="w-3.5 h-3.5" aria-hidden="true" />
                        Fit View
                    </ToolBtn>
                </div>
            </div>

            {/* ── Minimap — bottom right ───────────────────── */}
            <div
                className="absolute bottom-3 right-3 z-10 rounded-xl overflow-hidden"
                style={{
                    width: 180, height: 120,
                    background: 'rgba(10,15,30,0.88)',
                    border: '1px solid rgba(255,255,255,0.09)',
                    backdropFilter: 'blur(8px)',
                }}
                aria-hidden="true"
            >
                <Minimap graphRef={graphRef} sigmaRef={sigmaRef} />
            </div>

            {/* ── Legend — bottom left ─────────────────────── */}
            <Legend colorMode={colorMode} />

            {/* ── Performance mode banner ──────────────────── */}
            {isLargeGraph && (
                <div
                    className="absolute top-3 right-3 z-10 inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs"
                    style={{
                        background: 'rgba(30,58,138,0.75)',
                        border: '1px solid rgba(59,130,246,0.3)',
                        backdropFilter: 'blur(8px)',
                        color: '#93c5fd',
                    }}
                    role="status"
                    aria-live="polite"
                    aria-label={`Performance mode active: ${nodeCount} nodes`}
                >
                    <Zap className="w-3.5 h-3.5 text-blue-300" aria-hidden="true" />
                    <span className="tabular-nums font-mono font-semibold">{nodeCount}</span> nodes
                    {isHugeGraph    && <span className="text-blue-400">· Reduced labels</span>}
                    {isMassiveGraph && <span className="text-blue-400">· Minimal rendering</span>}
                </div>
            )}
        </div>
    );
};

export default SigmaRenderer;
