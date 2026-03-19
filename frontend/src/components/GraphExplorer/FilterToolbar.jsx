import React, { useState, useCallback } from 'react';
import useGraphStore from '../../store/useGraphStore';
import {
    Search,
    SlidersHorizontal,
    AlertTriangle,
    CircleDot,
    GitBranch,
    ShieldAlert,
    X,
} from 'lucide-react';

const RISK_OPTIONS = [
    { key: 'critical', label: 'Critical', hex: '#ef4444' },
    { key: 'high',     label: 'High',     hex: '#f97316' },
    { key: 'moderate', label: 'Moderate', hex: '#eab308' },
    { key: 'low',      label: 'Low',      hex: '#22c55e' },
    { key: 'none',     label: 'None',     hex: '#64748b' },
];

const NODE_TYPE_OPTIONS = [
    { key: 'function', label: 'Function' },
    { key: 'class',    label: 'Class'    },
    { key: 'module',   label: 'Module'   },
    { key: 'file',     label: 'File'     },
    { key: 'api_call', label: 'API Call' },
    { key: 'database', label: 'Database' },
    { key: 'external', label: 'External' },
];

const EDGE_TYPE_OPTIONS = [
    { key: 'calls',      label: 'Calls',      hex: '#3b82f6' },
    { key: 'uses_api',   label: 'Uses API',   hex: '#f59e0b' },
    { key: 'contains',   label: 'Contains',   hex: '#8b5cf6' },
    { key: 'structural', label: 'Structural', hex: '#6366f1' },
    { key: 'dependency', label: 'Dependency', hex: '#64748b' },
    { key: 'depends_on', label: 'Imports',    hex: '#14b8a6' },
    { key: 'flow',       label: 'Flow',       hex: '#ec4899' },
];

/* Generic pill-shaped toggle button */
const FilterPill = ({ active, onClick, children, accentHex }) => (
    <button
        role="checkbox"
        aria-checked={active}
        onClick={onClick}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
        style={{
            background: active ? (accentHex ? accentHex + '22' : 'rgba(71,85,105,0.4)') : 'rgba(15,23,42,0.5)',
            color: active ? (accentHex || '#e2e8f0') : '#64748b',
            border: `1px solid ${active ? (accentHex ? accentHex + '44' : 'rgba(71,85,105,0.5)') : 'rgba(255,255,255,0.06)'}`,
            opacity: active ? 1 : 0.65,
        }}
    >
        {children}
    </button>
);

const FilterToolbar = () => {
    const filters           = useGraphStore((s) => s.filters);
    const toggleRiskLevel   = useGraphStore((s) => s.toggleRiskLevel);
    const toggleNodeType    = useGraphStore((s) => s.toggleNodeType);
    const toggleEdgeType    = useGraphStore((s) => s.toggleEdgeType);
    const setSearchQuery    = useGraphStore((s) => s.setSearchQuery);
    const toggleRiskPathOnly = useGraphStore((s) => s.toggleRiskPathOnly);
    const graphStats        = useGraphStore((s) => s.graphStats);

    const [localSearch, setLocalSearch] = useState('');
    const [expanded, setExpanded] = useState(false);

    const debounceRef = React.useRef(null);
    const handleSearch = useCallback(
        (val) => {
            setLocalSearch(val);
            clearTimeout(debounceRef.current);
            debounceRef.current = setTimeout(() => setSearchQuery(val), 300);
        },
        [setSearchQuery]
    );

    return (
        <div
            style={{
                background: 'rgba(10,15,30,0.92)',
                backdropFilter: 'blur(12px)',
                borderBottom: '1px solid rgba(255,255,255,0.07)',
            }}
            role="toolbar"
            aria-label="Graph filters"
        >
            {/* Primary row */}
            <div className="flex items-center gap-3 px-4 py-2.5 flex-wrap">
                {/* Search */}
                <div className="relative flex-1 min-w-[160px] max-w-xs">
                    <Search
                        className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 pointer-events-none"
                        aria-hidden="true"
                    />
                    <input
                        type="search"
                        value={localSearch}
                        onChange={e => handleSearch(e.target.value)}
                        placeholder="Search nodes…"
                        aria-label="Search nodes"
                        className="w-full pl-9 pr-8 py-2 rounded-xl text-xs text-slate-200 placeholder-slate-600 transition-all duration-150 focus:outline-none"
                        style={{
                            background: 'rgba(30,41,59,0.7)',
                            border: '1px solid rgba(255,255,255,0.08)',
                        }}
                        onFocus={e => e.currentTarget.style.borderColor = '#3b82f6'}
                        onBlur={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'}
                    />
                    {localSearch && (
                        <button
                            onClick={() => handleSearch('')}
                            aria-label="Clear search"
                            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors focus-visible:outline focus-visible:outline-1 focus-visible:outline-blue-400"
                        >
                            <X className="w-3 h-3" aria-hidden="true" />
                        </button>
                    )}
                </div>

                {/* Stats */}
                <div
                    className="hidden sm:flex items-center gap-3 text-[10px] font-mono text-slate-500 px-3 py-1.5 rounded-lg"
                    style={{ background: 'rgba(30,41,59,0.4)', border: '1px solid rgba(255,255,255,0.05)' }}
                    aria-label={`Graph has ${graphStats.totalNodes} nodes and ${graphStats.totalEdges} edges`}
                >
                    <span className="inline-flex items-center gap-1">
                        <CircleDot className="w-3 h-3" aria-hidden="true" />
                        <span className="tabular-nums">{graphStats.totalNodes}</span> nodes
                    </span>
                    <span
                        className="w-px h-3"
                        style={{ background: 'rgba(255,255,255,0.1)' }}
                        aria-hidden="true"
                    />
                    <span className="inline-flex items-center gap-1">
                        <GitBranch className="w-3 h-3" aria-hidden="true" />
                        <span className="tabular-nums">{graphStats.totalEdges}</span> edges
                    </span>
                </div>

                {/* Risk path toggle */}
                <button
                    onClick={toggleRiskPathOnly}
                    aria-pressed={filters.riskPathOnly}
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-[11px] font-bold uppercase transition-all duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
                    style={{
                        background: filters.riskPathOnly ? 'rgba(239,68,68,0.15)' : 'rgba(30,41,59,0.5)',
                        color: filters.riskPathOnly ? '#fca5a5' : '#64748b',
                        border: `1px solid ${filters.riskPathOnly ? 'rgba(239,68,68,0.3)' : 'rgba(255,255,255,0.07)'}`,
                    }}
                >
                    <ShieldAlert className="w-3.5 h-3.5" aria-hidden="true" />
                    Risk Path
                </button>

                {/* Filter expand */}
                <button
                    onClick={() => setExpanded(v => !v)}
                    aria-expanded={expanded}
                    aria-controls="filter-panel"
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-[11px] font-bold uppercase transition-all duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
                    style={{
                        background: expanded ? 'rgba(59,130,246,0.15)' : 'rgba(30,41,59,0.5)',
                        color: expanded ? '#93c5fd' : '#64748b',
                        border: `1px solid ${expanded ? 'rgba(59,130,246,0.3)' : 'rgba(255,255,255,0.07)'}`,
                    }}
                >
                    <SlidersHorizontal className="w-3.5 h-3.5" aria-hidden="true" />
                    Filters
                </button>
            </div>

            {/* Expanded filter panel */}
            {expanded && (
                <div
                    id="filter-panel"
                    role="region"
                    aria-label="Advanced filters"
                    className="px-4 pb-3 pt-1 grid grid-cols-1 md:grid-cols-3 gap-5"
                    style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
                >
                    {/* Risk level */}
                    <fieldset>
                        <legend className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase mb-2.5 tracking-wider">
                            <AlertTriangle className="w-3 h-3" aria-hidden="true" />
                            Risk Level
                        </legend>
                        <div className="flex flex-wrap gap-1.5">
                            {RISK_OPTIONS.map(opt => (
                                <FilterPill
                                    key={opt.key}
                                    active={filters.riskLevels.includes(opt.key)}
                                    onClick={() => toggleRiskLevel(opt.key)}
                                    accentHex={opt.hex}
                                >
                                    <span
                                        className="w-2 h-2 rounded-full flex-shrink-0"
                                        style={{ background: opt.hex }}
                                        aria-hidden="true"
                                    />
                                    {opt.label}
                                </FilterPill>
                            ))}
                        </div>
                    </fieldset>

                    {/* Node type */}
                    <fieldset>
                        <legend className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase mb-2.5 tracking-wider">
                            <CircleDot className="w-3 h-3" aria-hidden="true" />
                            Node Type
                        </legend>
                        <div className="flex flex-wrap gap-1.5">
                            {NODE_TYPE_OPTIONS.map(opt => (
                                <FilterPill
                                    key={opt.key}
                                    active={filters.nodeTypes.includes(opt.key)}
                                    onClick={() => toggleNodeType(opt.key)}
                                >
                                    {opt.label}
                                </FilterPill>
                            ))}
                        </div>
                    </fieldset>

                    {/* Edge type */}
                    <fieldset>
                        <legend className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase mb-2.5 tracking-wider">
                            <GitBranch className="w-3 h-3" aria-hidden="true" />
                            Edge Type
                        </legend>
                        <div className="flex flex-wrap gap-1.5">
                            {EDGE_TYPE_OPTIONS.map(opt => (
                                <FilterPill
                                    key={opt.key}
                                    active={filters.edgeTypes.includes(opt.key)}
                                    onClick={() => toggleEdgeType(opt.key)}
                                    accentHex={opt.hex}
                                >
                                    <span
                                        className="inline-block w-3.5 h-0.5 rounded-full flex-shrink-0"
                                        style={{ background: opt.hex }}
                                        aria-hidden="true"
                                    />
                                    {opt.label}
                                </FilterPill>
                            ))}
                        </div>
                    </fieldset>
                </div>
            )}
        </div>
    );
};

export default FilterToolbar;
