import { create } from 'zustand';

const useGraphStore = create((set, get) => ({
    // --- Graph data ---
    rawNodes: [],
    rawEdges: [],

    // --- Selection & UI ---
    selectedNodeId: null,
    hoveredNodeId: null,

    // --- Filters ---
    filters: {
        riskLevels: ['low', 'moderate', 'high', 'critical', 'none'],
        nodeTypes: ['file', 'function', 'class', 'module', 'database', 'external', 'api_call'],
        edgeTypes: ['calls', 'uses_api', 'contains', 'structural', 'dependency', 'depends_on', 'flow'],
        searchQuery: '',
        riskPathOnly: false,
    },

    // --- Stats ---
    graphStats: {
        totalNodes: 0,
        totalEdges: 0,
        visibleNodes: 0,
        visibleEdges: 0,
    },

    // --- Layout ---
    layoutRunning: false,

    // --- Drill-down (hierarchical view) ---
    expandedFiles: new Set(),   // Set of file paths currently expanded

    // ========== ACTIONS ==========

    setGraphData: (nodes, edges) =>
        set({
            rawNodes: nodes,
            rawEdges: edges,
            graphStats: {
                totalNodes: nodes.length,
                totalEdges: edges.length,
                visibleNodes: nodes.length,
                visibleEdges: edges.length,
            },
        }),

    selectNode: (nodeId) => set({ selectedNodeId: nodeId }),
    clearSelection: () => set({ selectedNodeId: null }),
    setHoveredNode: (nodeId) => set({ hoveredNodeId: nodeId }),

    // --- Filter actions ---
    toggleRiskLevel: (level) =>
        set((state) => {
            const current = state.filters.riskLevels;
            const next = current.includes(level)
                ? current.filter((l) => l !== level)
                : [...current, level];
            return { filters: { ...state.filters, riskLevels: next } };
        }),

    toggleNodeType: (type) =>
        set((state) => {
            const current = state.filters.nodeTypes;
            const next = current.includes(type)
                ? current.filter((t) => t !== type)
                : [...current, type];
            return { filters: { ...state.filters, nodeTypes: next } };
        }),

    toggleEdgeType: (type) =>
        set((state) => {
            const current = state.filters.edgeTypes;
            const next = current.includes(type)
                ? current.filter((t) => t !== type)
                : [...current, type];
            return { filters: { ...state.filters, edgeTypes: next } };
        }),

    setSearchQuery: (query) =>
        set((state) => ({ filters: { ...state.filters, searchQuery: query } })),

    toggleRiskPathOnly: () =>
        set((state) => ({
            filters: { ...state.filters, riskPathOnly: !state.filters.riskPathOnly },
        })),

    setLayoutRunning: (val) => set({ layoutRunning: val }),

    // --- Drill-down actions ---
    toggleFileExpansion: (filePath) =>
        set((state) => {
            const next = new Set(state.expandedFiles);
            if (next.has(filePath)) {
                next.delete(filePath);
            } else {
                next.add(filePath);
            }
            return { expandedFiles: next };
        }),

    collapseAll: () => set({ expandedFiles: new Set() }),

    // --- Dynamic expansion: merge new neighbors ---
    mergeNeighbors: (newNodes, newEdges) =>
        set((state) => {
            const existingIds = new Set(state.rawNodes.map((n) => n.id));
            const uniqueNewNodes = newNodes.filter((n) => !existingIds.has(n.id));

            const existingEdgeKeys = new Set(
                state.rawEdges.map((e) => `${e.source}__${e.target}__${e.type}`)
            );
            const uniqueNewEdges = newEdges.filter(
                (e) => !existingEdgeKeys.has(`${e.source}__${e.target}__${e.type}`)
            );

            const mergedNodes = [...state.rawNodes, ...uniqueNewNodes];
            const mergedEdges = [...state.rawEdges, ...uniqueNewEdges];

            return {
                rawNodes: mergedNodes,
                rawEdges: mergedEdges,
                graphStats: {
                    ...state.graphStats,
                    totalNodes: mergedNodes.length,
                    totalEdges: mergedEdges.length,
                },
            };
        }),

    // Compute selected node's full data object
    getSelectedNode: () => {
        const { selectedNodeId, rawNodes } = get();
        if (!selectedNodeId) return null;
        return rawNodes.find((n) => n.id === selectedNodeId) || null;
    },
}));

export default useGraphStore;
