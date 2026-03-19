import { motion } from 'framer-motion';
import clsx from 'clsx';
import useGraphStore from '../../store/useGraphStore';
import {
    Database, X, MapPin, PhoneCall, Shield,
    AlertTriangle, MousePointerClick, GitFork, Cpu,
} from 'lucide-react';

/* ── Risk badge config ──────────────────────────────────────── */
const RISK_CONFIG = {
    critical: { bg: 'rgba(239,68,68,0.1)',   color: '#fca5a5', border: 'rgba(239,68,68,0.25)'   },
    high:     { bg: 'rgba(249,115,22,0.1)',  color: '#fdba74', border: 'rgba(249,115,22,0.25)'  },
    moderate: { bg: 'rgba(234,179,8,0.1)',   color: '#fde047', border: 'rgba(234,179,8,0.25)'   },
    medium:   { bg: 'rgba(234,179,8,0.1)',   color: '#fde047', border: 'rgba(234,179,8,0.25)'   },
    low:      { bg: 'rgba(16,185,129,0.1)',  color: '#6ee7b7', border: 'rgba(16,185,129,0.25)'  },
    none:     { bg: 'rgba(100,116,139,0.1)', color: '#94a3b8', border: 'rgba(100,116,139,0.25)' },
};

/* ── Section heading helper ─────────────────────────────────── */
const SectionLabel = ({ icon: Icon, children }) => (
    <div className="flex items-center gap-1.5 mb-2">
        <Icon className="w-3 h-3 text-slate-500 flex-shrink-0" aria-hidden="true" />
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">{children}</span>
    </div>
);

/* ── Small metric tile ──────────────────────────────────────── */
const MetricTile = ({ label, value }) => (
    <div
        className="flex flex-col items-center justify-center py-2 px-1 rounded-lg text-center"
        style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.06)' }}
    >
        <span className="text-base font-bold text-slate-100 tabular-nums leading-none">{value}</span>
        <span className="text-[9px] text-slate-500 uppercase mt-1 leading-none">{label}</span>
    </div>
);

const NodeDetailPanel = () => {
    const selectedNodeId = useGraphStore((s) => s.selectedNodeId);
    const rawNodes       = useGraphStore((s) => s.rawNodes);
    const rawEdges       = useGraphStore((s) => s.rawEdges);
    const clearSelection = useGraphStore((s) => s.clearSelection);

    const selectedNode = selectedNodeId
        ? rawNodes.find((n) => n.id === selectedNodeId) ?? null
        : null;

    /* ── Empty state ─────────────────────────────────────────── */
    if (!selectedNode) {
        return (
            <div
                className="flex flex-col items-center justify-center text-center p-6 rounded-2xl min-h-[200px]"
                style={{ background: 'rgba(15,23,42,0.4)', border: '1px dashed rgba(255,255,255,0.07)' }}
                aria-label="No node selected"
            >
                <MousePointerClick className="w-12 h-12 text-slate-700 mb-3" aria-hidden="true" />
                <h3 className="text-sm font-semibold text-slate-400 mb-1">Select a Node</h3>
                <p className="text-xs text-slate-600 leading-relaxed max-w-[180px]">
                    Click any node in the graph to inspect its details
                </p>
                <div className="mt-4 text-[10px] text-slate-700 space-y-1">
                    <p>Single click → select</p>
                    <p>Double click → expand / collapse file</p>
                </div>
            </div>
        );
    }

    const risk     = selectedNode.risk_level || selectedNode.risk || 'none';
    const type     = selectedNode.classification || selectedNode.type || 'function';
    const language = selectedNode.language || 'python';
    const riskCfg  = RISK_CONFIG[risk] || RISK_CONFIG.none;

    const outgoingCalls = rawEdges.filter(e => e.source === selectedNode.id);

    return (
        <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            key={selectedNode.id}
            className="flex flex-col gap-4 pb-6"
            aria-label={`Node details: ${selectedNode.name}`}
        >
            {/* ── Node header ─────────────────────────────────── */}
            <div
                className="flex items-start justify-between gap-2 p-3 rounded-xl"
                style={{ background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(255,255,255,0.07)' }}
            >
                <div className="flex items-center gap-2.5 min-w-0">
                    <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                        style={{ background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.2)' }}
                        aria-hidden="true"
                    >
                        <Database className="w-4 h-4 text-blue-400" />
                    </div>
                    <div className="min-w-0">
                        <h3 className="text-sm font-bold text-slate-100 leading-tight truncate">
                            {selectedNode.name}
                        </h3>
                        <p className="text-[10px] font-mono text-slate-600 truncate mt-0.5">{selectedNode.id}</p>
                    </div>
                </div>
                <button
                    onClick={clearSelection}
                    aria-label="Close node detail"
                    className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-lg transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
                    style={{ background: 'rgba(255,255,255,0.05)' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                >
                    <X className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
                </button>
            </div>

            {/* ── Type & Language ─────────────────────────────── */}
            <div>
                <SectionLabel icon={CircleDotIcon}>Classification</SectionLabel>
                <div className="flex gap-2 flex-wrap">
                    <span
                        className="px-2.5 py-1 rounded-lg text-xs font-bold uppercase"
                        style={{
                            background: 'rgba(59,130,246,0.12)',
                            color: '#93c5fd',
                            border: '1px solid rgba(59,130,246,0.22)',
                        }}
                        aria-label={`Type: ${type}`}
                    >
                        {type}
                    </span>
                    <span
                        className="px-2.5 py-1 rounded-lg text-xs font-mono font-medium"
                        style={{
                            background: 'rgba(139,92,246,0.1)',
                            color: '#c4b5fd',
                            border: '1px solid rgba(139,92,246,0.2)',
                        }}
                        aria-label={`Language: ${language}`}
                    >
                        {language}
                    </span>
                </div>
            </div>

            {/* ── Risk summary ────────────────────────────────── */}
            <div>
                <SectionLabel icon={Shield}>Risk</SectionLabel>
                <div
                    className="px-3 py-2.5 rounded-xl text-xs leading-relaxed"
                    style={{
                        background: riskCfg.bg,
                        color: riskCfg.color,
                        border: `1px solid ${riskCfg.border}`,
                    }}
                    role="status"
                    aria-label={`Risk level: ${risk}`}
                >
                    <span
                        className="inline-block px-2 py-0.5 rounded-md text-[9px] font-bold uppercase mr-2 mb-1"
                        style={{ background: riskCfg.border, color: riskCfg.color }}
                    >
                        {risk}
                    </span>
                    {selectedNode.node_summary || 'No specific risk identified.'}
                </div>
            </div>

            {/* ── Risk factors ────────────────────────────────── */}
            {selectedNode.risk_analysis?.risk_factors && (() => {
                const entries = Object.entries(selectedNode.risk_analysis.risk_factors)
                    .filter(([, d]) => d.level && d.level !== 'none')
                    .slice(0, 5);
                if (!entries.length) return null;
                return (
                    <div>
                        <SectionLabel icon={AlertTriangle}>Risk Factors</SectionLabel>
                        <div className="space-y-2">
                            {entries.map(([riskName, data], idx) => {
                                const cfg = RISK_CONFIG[data.level] || RISK_CONFIG.low;
                                return (
                                    <div
                                        key={idx}
                                        className="p-2.5 rounded-xl"
                                        style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.06)' }}
                                    >
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-xs font-semibold text-slate-300 capitalize">
                                                {riskName.replace(/_/g, ' ')}
                                            </span>
                                            <span
                                                className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase"
                                                style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}` }}
                                            >
                                                {data.level}
                                            </span>
                                        </div>
                                        <p className="text-[11px] text-slate-400 leading-relaxed">{data.reason}</p>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                );
            })()}

            {/* ── Impact analysis ─────────────────────────────── */}
            {selectedNode.impact_analysis && (
                <div>
                    <SectionLabel icon={AlertTriangle}>Impact Analysis</SectionLabel>
                    <div className="grid grid-cols-3 gap-2">
                        <MetricTile label="Blast Radius"   value={selectedNode.impact_analysis.blast_radius_score} />
                        <MetricTile label="Critical Path"  value={selectedNode.impact_analysis.critical_path_likelihood} />
                        <MetricTile label="Sensitivity"    value={selectedNode.impact_analysis.change_sensitivity} />
                    </div>
                </div>
            )}

            {/* ── Cluster membership ──────────────────────────── */}
            {selectedNode.cluster_name && (
                <div>
                    <SectionLabel icon={GitFork}>Microservice Cluster</SectionLabel>
                    <div
                        className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl"
                        style={{
                            background: 'rgba(249,115,22,0.08)',
                            border: '1px solid rgba(249,115,22,0.2)',
                        }}
                    >
                        <div className="w-2.5 h-2.5 rounded-full bg-orange-400 flex-shrink-0" aria-hidden="true" />
                        <span className="text-sm font-semibold text-orange-300 flex-1 truncate">
                            {selectedNode.cluster_name}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 flex-shrink-0">
                            #{selectedNode.cluster_id}
                        </span>
                    </div>
                </div>
            )}

            {/* ── GNN Embedding sparkline ──────────────────────── */}
            {Array.isArray(selectedNode.embedding) && selectedNode.embedding.length > 0 && (
                <div>
                    <div className="flex items-center justify-between mb-2">
                        <SectionLabel icon={Cpu}>GNN Embedding</SectionLabel>
                        <span className="text-[9px] text-slate-600 font-mono">
                            {selectedNode.embedding.length}-dim
                        </span>
                    </div>
                    <div
                        className="p-3 rounded-xl"
                        style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(255,255,255,0.06)' }}
                        aria-label={`GNN embedding visualization, ${selectedNode.embedding.length} dimensions`}
                    >
                        <div className="flex items-end gap-px h-8" aria-hidden="true">
                            {selectedNode.embedding.slice(0, 48).map((val, i) => {
                                const norm = Math.abs(val);
                                const h = Math.max(2, Math.min(32, Math.round(norm * 64)));
                                return (
                                    <div
                                        key={i}
                                        title={`dim ${i}: ${val.toFixed(3)}`}
                                        style={{
                                            height: h + 'px',
                                            background: val >= 0 ? '#3b82f6' : '#f97316',
                                            width: '4px',
                                            borderRadius: '1px',
                                            flexShrink: 0,
                                            opacity: 0.5 + norm * 0.5,
                                        }}
                                    />
                                );
                            })}
                        </div>
                        <div className="flex justify-between mt-1.5">
                            <span className="text-[9px] text-blue-500">positive</span>
                            <span className="text-[9px] text-slate-600">first 48 dims</span>
                            <span className="text-[9px] text-orange-500">negative</span>
                        </div>
                    </div>
                </div>
            )}

            {/* ── File location ───────────────────────────────── */}
            {selectedNode.file && (
                <div>
                    <SectionLabel icon={MapPin}>Location</SectionLabel>
                    <div
                        className="px-3 py-2.5 rounded-xl"
                        style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.06)' }}
                    >
                        <p className="text-xs font-mono text-slate-300 break-all leading-relaxed">
                            {selectedNode.file}
                            {selectedNode.line_start && (
                                <span className="text-blue-400" aria-label={`line ${selectedNode.line_start}`}>
                                    :{selectedNode.line_start}
                                </span>
                            )}
                        </p>
                    </div>
                </div>
            )}

            {/* ── Outgoing calls ──────────────────────────────── */}
            {outgoingCalls.length > 0 && (
                <div>
                    <SectionLabel icon={PhoneCall}>
                        Calls ({outgoingCalls.length})
                    </SectionLabel>
                    <div className="space-y-0.5">
                        {outgoingCalls.slice(0, 10).map((edge, idx) => {
                            const targetNode = rawNodes.find(n => n.id === edge.target);
                            return (
                                <div
                                    key={idx}
                                    className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-mono text-slate-400 transition-colors duration-100"
                                    style={{ background: 'transparent' }}
                                    onMouseEnter={e => {
                                        e.currentTarget.style.background = 'rgba(255,255,255,0.04)';
                                        e.currentTarget.style.color = '#e2e8f0';
                                    }}
                                    onMouseLeave={e => {
                                        e.currentTarget.style.background = 'transparent';
                                        e.currentTarget.style.color = '';
                                    }}
                                >
                                    <div
                                        className="w-1 h-1 rounded-full bg-blue-500 flex-shrink-0"
                                        aria-hidden="true"
                                    />
                                    {targetNode?.name || edge.target}
                                </div>
                            );
                        })}
                        {outgoingCalls.length > 10 && (
                            <p className="text-[10px] text-slate-600 px-2.5 py-1">
                                +{outgoingCalls.length - 10} more calls
                            </p>
                        )}
                    </div>
                </div>
            )}
        </motion.div>
    );
};

/* Inline icon component to avoid re-importing CircleDot */
const CircleDotIcon = (props) => (
    <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="1" fill="currentColor" />
    </svg>
);

export default NodeDetailPanel;
