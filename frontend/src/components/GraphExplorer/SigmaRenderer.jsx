import React, { useEffect, useRef, useCallback, useMemo } from 'react';
import Graph from 'graphology';
import Sigma from 'sigma';
import dagre from 'dagre';
import useGraphStore from '../../store/useGraphStore';

/* ─── Performance Configuration ─── */
const PERFORMANCE_THRESHOLDS = {
    LARGE_GRAPH: 200,      // Disable animations above this
    HUGE_GRAPH: 500,       // Reduce label density above this
    MASSIVE_GRAPH: 1000    // Minimal rendering above this
};

/* ─── Dagre layout helper ─── */
function applyDagreLayout(graph) {
    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: 'TB', nodesep: 500, ranksep: 600, edgesep: 300 });
    g.setDefaultEdgeLabel(() => ({}));

    graph.forEachNode((id, attrs) => {
        g.setNode(id, { width: 180, height: 70 });
    });
    graph.forEachEdge((key, attrs, source, target) => {
        g.setEdge(source, target);
    });

    dagre.layout(g);

    g.nodes().forEach((id) => {
        const pos = g.node(id);
        if (pos && graph.hasNode(id)) {
            graph.setNodeAttribute(id, 'x', pos.x);
            graph.setNodeAttribute(id, 'y', pos.y);
        }
    });
}

/* ─── Visual encoding maps ─── */
const RISK_COLORS = {
    critical: '#ef4444',
    high: '#f97316',
    moderate: '#eab308',
    medium: '#eab308',
    low: '#22c55e',
    none: '#64748b',
};

const TYPE_COLORS = {
    file: '#3b82f6',
    function: '#10b981',
    class: '#6366f1',
    module: '#8b5cf6',
    database: '#f59e0b',
    external: '#ec4899',
    api_call: '#f59e0b',
};

const EDGE_COLORS = {
    calls: '#3b82f6',
    uses_api: '#f59e0b',
    contains: '#8b5cf6',
    structural: '#6366f1',
    dependency: '#64748b',
    depends_on: '#14b8a6',
    flow: '#ec4899',
};

/* ─── Helpers ─── */
function basename(filepath) {
    if (!filepath) return 'unknown';
    return filepath.replace(/\\/g, '/').split('/').pop() || filepath;
}

/** Truncate a label to maxLen characters, appending '…' if needed */
function truncateLabel(label, maxLen = 24) {
    if (!label || label.length <= maxLen) return label;
    return label.slice(0, maxLen - 1) + '…';
}

function aggregateRisk(nodes) {
    const prio = { critical: 5, high: 4, moderate: 3, medium: 3, low: 2, none: 1 };
    let max = 0, maxRisk = 'none';
    for (const n of nodes) {
        const r = n.risk_level || n.risk || 'none';
        if ((prio[r] || 0) > max) { max = prio[r] || 0; maxRisk = r; }
    }
    return maxRisk;
}

const SigmaRenderer = ({ nodes, edges }) => {
    const containerRef = useRef(null);
    const sigmaRef = useRef(null);
    const graphRef = useRef(null);

    const selectNode = useGraphStore((s) => s.selectNode);
    const setGraphData = useGraphStore((s) => s.setGraphData);
    const setHoveredNode = useGraphStore((s) => s.setHoveredNode);
    const selectedNodeId = useGraphStore((s) => s.selectedNodeId);
    const hoveredNodeId = useGraphStore((s) => s.hoveredNodeId);
    const filters = useGraphStore((s) => s.filters);
    const expandedFiles = useGraphStore((s) => s.expandedFiles);
    const toggleFileExpansion = useGraphStore((s) => s.toggleFileExpansion);
    const collapseAll = useGraphStore((s) => s.collapseAll);
    const expandAll = useGraphStore((s) => s.expandAll);

    const selectedRef = useRef(null);
    const hoveredRef = useRef(null);

    // Performance: Calculate node count for optimization decisions
    const nodeCount = useMemo(() => nodes.length, [nodes.length]);
    const isLargeGraph = nodeCount > PERFORMANCE_THRESHOLDS.LARGE_GRAPH;
    const isHugeGraph = nodeCount > PERFORMANCE_THRESHOLDS.HUGE_GRAPH;
    const isMassiveGraph = nodeCount > PERFORMANCE_THRESHOLDS.MASSIVE_GRAPH;

    useEffect(() => {
        selectedRef.current = selectedNodeId;
        if (sigmaRef.current) sigmaRef.current.refresh();
    }, [selectedNodeId]);

    useEffect(() => {
        hoveredRef.current = hoveredNodeId;
        if (sigmaRef.current) sigmaRef.current.refresh();
    }, [hoveredNodeId]);

    /* ─── Compute visible nodes & edges based on drill-down level ─── */
    const { visibleNodes, visibleEdges } = useMemo(() => {
        const byFile = {};
        for (const n of nodes) {
            const f = n.file || 'unknown';
            if (!byFile[f]) byFile[f] = [];
            byFile[f].push(n);
        }

        const vNodes = [];
        const fileNodeIds = {};

        for (const [filePath, children] of Object.entries(byFile)) {
            const fileId = `__file__${filePath}`;
            fileNodeIds[filePath] = new Set(children.map((c) => c.id));

            // Auto-expand files with only 1 function, or manually expanded files
            if (children.length === 1 || expandedFiles.has(filePath)) {
                for (const child of children) {
                    vNodes.push(child);
                }
            } else {
                const totalLoc = children.reduce((acc, c) => acc + (c.loc || 10), 0);
                const risk = aggregateRisk(children);
                const nodeCount = children.length;
                vNodes.push({
                    id: fileId,
                    name: basename(filePath),
                    type: 'file',
                    file: filePath,
                    risk_level: risk,
                    loc: totalLoc,
                    _isFileNode: true,
                    _childCount: nodeCount,
                    _filePath: filePath,
                    // Give file nodes summary info for detail panel
                    node_summary: `File containing ${nodeCount} nodes. Highest risk: ${risk}.`,
                    architectural_role: 'file',
                });
            }
        }

        // Remap edges for collapsed files
        const nodeIdToFileId = {};
        for (const [filePath, childIds] of Object.entries(fileNodeIds)) {
            if (!expandedFiles.has(filePath)) {
                const fileId = `__file__${filePath}`;
                for (const cid of childIds) {
                    nodeIdToFileId[cid] = fileId;
                }
            }
        }

        const visibleNodeIds = new Set(vNodes.map((n) => n.id));
        const edgeSeen = new Set();
        const vEdges = [];

        for (const e of edges) {
            let src = nodeIdToFileId[e.source] || e.source;
            let tgt = nodeIdToFileId[e.target] || e.target;
            if (src === tgt) continue;
            if (!visibleNodeIds.has(src) || !visibleNodeIds.has(tgt)) continue;
            const key = `${src}__${tgt}__${e.type || 'calls'}`;
            if (edgeSeen.has(key)) continue;
            edgeSeen.add(key);
            vEdges.push({ ...e, source: src, target: tgt });
        }

        return { visibleNodes: vNodes, visibleEdges: vEdges };
    }, [nodes, edges, expandedFiles]);

    // Sync visible nodes to the store so NodeDetailPanel can find them
    useEffect(() => {
        if (visibleNodes.length > 0) {
            setGraphData(visibleNodes, visibleEdges);
        }
    }, [visibleNodes, visibleEdges, setGraphData]);

    /* ─── Build graph ─── */
    const buildGraph = useCallback(() => {
        const graph = new Graph();
        const nodeIds = new Set();

        const filteredNodes = visibleNodes.filter((n) => {
            const risk = n.risk_level || n.risk || 'none';
            const type = n.type || 'function';
            if (!filters.riskLevels.includes(risk)) return false;
            if (!filters.nodeTypes.includes(type)) return false;
            if (
                filters.searchQuery &&
                !n.name?.toLowerCase().includes(filters.searchQuery.toLowerCase()) &&
                !n.id?.toLowerCase().includes(filters.searchQuery.toLowerCase())
            )
                return false;
            return true;
        });

        filteredNodes.forEach((n) => {
            if (graph.hasNode(n.id)) return;
            nodeIds.add(n.id);
            const risk = n.risk_level || n.risk || 'none';
            const type = n.type || 'function';

            const rawLabel = n._isFileNode
                ? n._childCount === 1
                    ? `📄 ${n.name}`  // No count for single-function files
                    : `📄 ${n.name}  (${n._childCount})`
                : n.name || n.id;
            const label = truncateLabel(rawLabel, n._isFileNode ? 28 : 24);

            graph.addNode(n.id, {
                label,
                x: Math.random() * 200,
                y: Math.random() * 200,
                size: getNodeSize(n),
                color: n._isFileNode
                    ? TYPE_COLORS.file
                    : RISK_COLORS[risk] || RISK_COLORS.none,
                borderColor: TYPE_COLORS[type] || TYPE_COLORS.function,
                type: 'circle',
                _raw: n,
            });
        });

        visibleEdges.forEach((e) => {
            const edgeType = e.type || e.label || 'calls';
            if (!filters.edgeTypes.includes(edgeType)) return;
            if (filters.riskPathOnly && !e.risk_path) return;
            if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) return;
            if (e.source === e.target) return;

            const key = `${e.source}__${e.target}__${edgeType}`;
            if (graph.hasEdge(key)) return;

            try {
                graph.addEdgeWithKey(key, e.source, e.target, {
                    type: 'arrow',
                    color: EDGE_COLORS[edgeType] || '#94a3b8',
                    size: edgeType === 'calls' ? 2 : 1.5,
                    label: edgeType,
                });
            } catch (err) { /* skip */ }
        });

        return graph;
    }, [visibleNodes, visibleEdges, filters]);

    function getNodeSize(node) {
        if (node._isFileNode) return Math.max(14, Math.min(28, Math.sqrt(node._childCount) * 6));
        const loc = node.loc || 10;
        const risk = node.risk_level || node.risk || 'none';
        let base = Math.max(5, Math.min(18, Math.sqrt(loc) * 1.5));
        if (risk === 'critical') base *= 1.4;
        if (risk === 'high') base *= 1.2;
        if (node.type === 'module') base *= 1.3;
        return base;
    }

    /* ─── Initialize ─── */
    useEffect(() => {
        if (!containerRef.current) return;

        if (sigmaRef.current) {
            sigmaRef.current.kill();
            sigmaRef.current = null;
        }

        const graph = buildGraph();
        graphRef.current = graph;

        if (graph.order === 0) return;

        // Dagre hierarchical layout — keeps connected nodes tight
        applyDagreLayout(graph);

        const sigma = new Sigma(graph, containerRef.current, {
            renderLabels: !isMassiveGraph,  // Disable labels for massive graphs
            labelRenderedSizeThreshold: isLargeGraph ? 6 : 4,  // Higher threshold for large graphs
            labelSize: isHugeGraph ? 11 : 13,  // Smaller labels for huge graphs
            labelWeight: 'bold',
            labelColor: { color: '#e2e8f0' },
            labelFont: 'Inter, system-ui, sans-serif',
            defaultEdgeType: 'arrow',
            defaultNodeColor: '#64748b',
            defaultEdgeColor: '#475569',
            minCameraRatio: isLargeGraph ? 0.01 : 0.02,  // Allow more zoom out for large graphs
            maxCameraRatio: isLargeGraph ? 10 : 20,  // Less zoom in for large graphs
            stagePadding: isHugeGraph ? 40 : 60,  // Less padding for huge graphs
            labelDensity: isHugeGraph ? 0.3 : 0.5,  // Reduce label density for huge graphs
            labelGridCellSize: isHugeGraph ? 240 : 180,  // More space between labels for huge graphs
            enableEdgeEvents: !isLargeGraph,  // Disable edge events for performance on large graphs
            nodeReducer: (node, data) => {
                const res = { ...data };
                const activeSelected = selectedRef.current;
                const activeHovered = hoveredRef.current;

                if (activeSelected) {
                    if (node === activeSelected) {
                        res.highlighted = true;
                        res.zIndex = 2;
                    } else if (graph.hasEdge(activeSelected, node) || graph.hasEdge(node, activeSelected)) {
                        res.highlighted = true;
                    } else {
                        res.color = '#1e293b';
                        res.label = '';
                    }
                }

                if (activeHovered && node === activeHovered) {
                    res.highlighted = true;
                    if (activeSelected && node !== activeSelected && !graph.hasEdge(activeSelected, node) && !graph.hasEdge(node, activeSelected)) {
                        res.label = data.label;
                    }
                }

                return res;
            },
            edgeReducer: (edge, data) => {
                const res = { ...data };
                const activeSelected = selectedRef.current;
                if (activeSelected) {
                    const ends = graph.extremities(edge);
                    if (!ends.includes(activeSelected)) {
                        res.hidden = true;
                    } else {
                        res.size = 3;
                        res.color = '#60a5fa';
                    }
                }
                return res;
            },
        });

        // Single click: select
        sigma.on('clickNode', ({ node }) => {
            selectNode(node);
        });

        // Double-click: drill-down
        sigma.on('doubleClickNode', ({ node, event }) => {
            event.original?.preventDefault?.();
            const raw = graph.getNodeAttribute(node, '_raw');
            if (raw?._isFileNode) {
                toggleFileExpansion(raw._filePath);
            } else if (raw?.file) {
                toggleFileExpansion(raw.file);
            }
        });

        sigma.on('clickStage', () => {
            selectNode(null);
        });

        sigma.on('enterNode', ({ node }) => {
            setHoveredNode(node);
            if (containerRef.current) containerRef.current.style.cursor = 'pointer';
        });

        sigma.on('leaveNode', () => {
            setHoveredNode(null);
            if (containerRef.current) containerRef.current.style.cursor = 'default';
        });

        sigmaRef.current = sigma;

        return () => {
            if (sigmaRef.current) {
                sigmaRef.current.kill();
                sigmaRef.current = null;
            }
        };
    }, [buildGraph]);

    const handleRelayout = useCallback(() => {
        if (!graphRef.current || graphRef.current.order === 0) return;
        applyDagreLayout(graphRef.current);
        if (sigmaRef.current) sigmaRef.current.refresh();
    }, []);

    const hasExpanded = expandedFiles.size > 0;

    return (
        <div className="relative w-full h-full">
            <div
                ref={containerRef}
                className="w-full h-full bg-slate-950"
                style={{ minHeight: '500px' }}
            />

            {/* Top controls - File status and expand/collapse */}
            <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
                <div className="bg-slate-900/80 backdrop-blur-sm px-3 py-1.5 rounded-lg flex items-center gap-2 border border-slate-800">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    <span className="text-xs font-mono text-slate-300">
                        {hasExpanded ? 'File Expanded' : 'File View'} • Double-click to {hasExpanded ? 'collapse' : 'expand'}
                    </span>
                </div>
                
                <div className="flex gap-2">
                    {hasExpanded ? (
                        <button
                            onClick={() => { collapseAll(); selectNode(null); }}
                            className="px-3 py-1.5 bg-blue-600/80 hover:bg-blue-500 text-white text-xs font-mono rounded-lg border border-blue-500 backdrop-blur-sm transition-colors"
                        >
                            ← Collapse All
                        </button>
                    ) : (
                        <button
                            onClick={() => { expandAll(); }}
                            className="px-3 py-1.5 bg-green-600/80 hover:bg-green-500 text-white text-xs font-mono rounded-lg border border-green-500 backdrop-blur-sm transition-colors"
                        >
                            → Expand All
                        </button>
                    )}
                    <button
                        onClick={handleRelayout}
                        className="px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-mono rounded-lg border border-slate-700 backdrop-blur-sm transition-colors"
                    >
                        ⟳ Re-layout
                    </button>
                    <button
                        onClick={() => sigmaRef.current?.getCamera()?.animatedReset()}
                        className="px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-mono rounded-lg border border-slate-700 backdrop-blur-sm transition-colors"
                    >
                        ⊞ Fit View
                    </button>
                </div>
            </div>

            {/* Performance indicator for large graphs */}
            {isLargeGraph && (
                <div className="absolute top-24 left-4 z-10 bg-blue-900/80 backdrop-blur-sm px-3 py-1.5 rounded-lg flex items-center gap-2 border border-blue-700">
                    <svg className="w-3 h-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span className="text-xs font-mono text-blue-200">
                        Performance Mode: {nodeCount} nodes
                        {isHugeGraph && ' • Reduced labels'}
                        {isMassiveGraph && ' • Minimal rendering'}
                    </span>
                </div>
            )}

        </div>
    );
};

export default SigmaRenderer;
