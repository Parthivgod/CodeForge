import React, { useState, useCallback } from 'react';
import useGraphStore from '../../store/useGraphStore';
import {
    Search,
    Filter,
    AlertTriangle,
    CircleDot,
    GitBranch,
    ShieldAlert,
    X,
} from 'lucide-react';

const RISK_OPTIONS = [
    { key: 'critical', label: 'Critical', color: 'bg-red-500' },
    { key: 'high', label: 'High', color: 'bg-orange-500' },
    { key: 'moderate', label: 'Moderate', color: 'bg-yellow-500' },
    { key: 'low', label: 'Low', color: 'bg-green-500' },
    { key: 'none', label: 'None', color: 'bg-gray-500' },
];

const NODE_TYPE_OPTIONS = [
    { key: 'function', label: 'Function', icon: '⨍' },
    { key: 'class', label: 'Class', icon: '◆' },
    { key: 'module', label: 'Module', icon: '▣' },
    { key: 'file', label: 'File', icon: '□' },
    { key: 'api_call', label: 'API Call', icon: '⬡' },
    { key: 'database', label: 'Database', icon: '▲' },
    { key: 'external', label: 'External', icon: '⬡' },
];

const EDGE_TYPE_OPTIONS = [
    { key: 'calls', label: 'Calls', color: '#3b82f6' },
    { key: 'uses_api', label: 'Uses API', color: '#f59e0b' },
    { key: 'contains', label: 'Contains', color: '#8b5cf6' },
    { key: 'structural', label: 'Structural', color: '#6366f1' },
    { key: 'dependency', label: 'Dependency', color: '#64748b' },
    { key: 'depends_on', label: 'Imports', color: '#14b8a6' },
    { key: 'flow', label: 'Flow', color: '#ec4899' },
];

const FilterToolbar = () => {
    const filters = useGraphStore((s) => s.filters);
    const toggleRiskLevel = useGraphStore((s) => s.toggleRiskLevel);
    const toggleNodeType = useGraphStore((s) => s.toggleNodeType);
    const toggleEdgeType = useGraphStore((s) => s.toggleEdgeType);
    const setSearchQuery = useGraphStore((s) => s.setSearchQuery);
    const toggleRiskPathOnly = useGraphStore((s) => s.toggleRiskPathOnly);
    const graphStats = useGraphStore((s) => s.graphStats);

    const [localSearch, setLocalSearch] = useState('');
    const [expanded, setExpanded] = useState(false);

    // Debounced search
    const debounceRef = React.useRef(null);
    const handleSearch = useCallback(
        (val) => {
            setLocalSearch(val);
            clearTimeout(debounceRef.current);
            debounceRef.current = setTimeout(() => {
                setSearchQuery(val);
            }, 300);
        },
        [setSearchQuery]
    );

    return (
        <div className="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 py-3">
            {/* Top bar */}
            <div className="flex items-center gap-4 flex-wrap">
                {/* Search */}
                <div className="relative flex-1 max-w-xs">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                        type="text"
                        value={localSearch}
                        onChange={(e) => handleSearch(e.target.value)}
                        placeholder="Search nodes..."
                        className="w-full pl-9 pr-8 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                    />
                    {localSearch && (
                        <button
                            onClick={() => handleSearch('')}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                        >
                            <X className="w-3 h-3" />
                        </button>
                    )}
                </div>

                {/* Stats */}
                <div className="flex items-center gap-3 text-[10px] font-mono text-slate-500 uppercase">
                    <span>
                        <CircleDot className="w-3 h-3 inline mr-1" />
                        {graphStats.totalNodes} nodes
                    </span>
                    <span>
                        <GitBranch className="w-3 h-3 inline mr-1" />
                        {graphStats.totalEdges} edges
                    </span>
                </div>

                {/* Risk path toggle */}
                <button
                    onClick={toggleRiskPathOnly}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold uppercase transition-all border ${filters.riskPathOnly
                        ? 'bg-red-500/20 text-red-400 border-red-500/30'
                        : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
                        }`}
                >
                    <ShieldAlert className="w-3.5 h-3.5" />
                    Risk Path
                </button>

                {/* Filter expand */}
                <button
                    onClick={() => setExpanded(!expanded)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold uppercase transition-all border ${expanded
                        ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                        : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
                        }`}
                >
                    <Filter className="w-3.5 h-3.5" />
                    Filters
                </button>
            </div>

            {/* Expanded filter panel */}
            {expanded && (
                <div className="mt-3 pt-3 border-t border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Risk level */}
                    <div>
                        <div className="text-[10px] font-bold text-slate-500 uppercase mb-2 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" /> Risk Level
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                            {RISK_OPTIONS.map((opt) => (
                                <button
                                    key={opt.key}
                                    onClick={() => toggleRiskLevel(opt.key)}
                                    className={`px-2 py-1 rounded text-[10px] font-bold uppercase transition-all border ${filters.riskLevels.includes(opt.key)
                                        ? `${opt.color}/20 text-white border-white/20`
                                        : 'bg-slate-800/50 text-slate-600 border-slate-700/50 opacity-50'
                                        }`}
                                >
                                    <span className={`inline-block w-2 h-2 rounded-full ${opt.color} mr-1`} />
                                    {opt.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Node type */}
                    <div>
                        <div className="text-[10px] font-bold text-slate-500 uppercase mb-2 flex items-center gap-1">
                            <CircleDot className="w-3 h-3" /> Node Type
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                            {NODE_TYPE_OPTIONS.map((opt) => (
                                <button
                                    key={opt.key}
                                    onClick={() => toggleNodeType(opt.key)}
                                    className={`px-2 py-1 rounded text-[10px] font-bold transition-all border ${filters.nodeTypes.includes(opt.key)
                                        ? 'bg-slate-700 text-slate-200 border-slate-600'
                                        : 'bg-slate-800/50 text-slate-600 border-slate-700/50 opacity-50'
                                        }`}
                                >
                                    {opt.icon} {opt.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Edge type */}
                    <div>
                        <div className="text-[10px] font-bold text-slate-500 uppercase mb-2 flex items-center gap-1">
                            <GitBranch className="w-3 h-3" /> Edge Type
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                            {EDGE_TYPE_OPTIONS.map((opt) => (
                                <button
                                    key={opt.key}
                                    onClick={() => toggleEdgeType(opt.key)}
                                    className={`px-2 py-1 rounded text-[10px] font-bold transition-all border ${filters.edgeTypes.includes(opt.key)
                                        ? 'bg-slate-700 text-slate-200 border-slate-600'
                                        : 'bg-slate-800/50 text-slate-600 border-slate-700/50 opacity-50'
                                        }`}
                                >
                                    <span
                                        className="inline-block w-3 h-0.5 mr-1 rounded"
                                        style={{ backgroundColor: opt.color }}
                                    />
                                    {opt.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FilterToolbar;
