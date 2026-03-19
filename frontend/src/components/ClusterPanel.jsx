import { motion, AnimatePresence } from 'framer-motion';
import { GitFork, ChevronDown, ChevronRight, Layers, FileCode } from 'lucide-react';
import useGraphStore from '../store/useGraphStore';
import clsx from 'clsx';

const CLUSTER_COLORS = [
    '#3b82f6', '#10b981', '#f97316', '#8b5cf6',
    '#ec4899', '#14b8a6', '#f59e0b', '#6366f1',
    '#ef4444', '#22d3ee',
];

const RISK_BADGE = {
    high:     { bg: 'rgba(239,68,68,0.1)',   color: '#fca5a5', border: 'rgba(239,68,68,0.25)'   },
    medium:   { bg: 'rgba(234,179,8,0.1)',   color: '#fde047', border: 'rgba(234,179,8,0.25)'   },
    low:      { bg: 'rgba(16,185,129,0.1)',  color: '#6ee7b7', border: 'rgba(16,185,129,0.25)'  },
};

const ClusterPanel = () => {
    const clusters             = useGraphStore((s) => s.clusters);
    const highlightedClusterId = useGraphStore((s) => s.highlightedClusterId);
    const setHighlightedCluster = useGraphStore((s) => s.setHighlightedCluster);
    const rawNodes             = useGraphStore((s) => s.rawNodes);
    const selectNode           = useGraphStore((s) => s.selectNode);

    if (!clusters || clusters.length === 0) {
        return (
            <div
                className="flex flex-col items-center justify-center text-center p-8 rounded-2xl min-h-[160px]"
                style={{ background: 'rgba(15,23,42,0.4)', border: '1px dashed rgba(255,255,255,0.07)' }}
                aria-label="No clusters available"
            >
                <GitFork className="w-10 h-10 text-slate-700 mb-3" aria-hidden="true" />
                <p className="text-sm font-medium text-slate-500">No clusters yet</p>
                <p className="text-xs text-slate-600 mt-1">Run analysis with GNN enabled</p>
            </div>
        );
    }

    const handleClusterClick = (clusterId) => {
        setHighlightedCluster(highlightedClusterId === clusterId ? null : clusterId);
    };

    return (
        <div className="flex flex-col gap-2 pb-4" role="list" aria-label="Microservice clusters">
            <div className="flex items-center gap-2 px-1 mb-3">
                <GitFork className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    {clusters.length} boundary candidates
                </span>
            </div>

            {clusters.map((cluster, idx) => {
                const color    = CLUSTER_COLORS[idx % CLUSTER_COLORS.length];
                const isActive = highlightedClusterId === cluster.id;
                const riskSt   = RISK_BADGE[cluster.risk] || RISK_BADGE.low;

                const memberNodes = rawNodes.filter(
                    (n) => n.cluster_id === cluster.id || cluster.node_ids?.includes(n.id)
                );

                return (
                    <motion.article
                        key={cluster.id}
                        role="listitem"
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.04 }}
                        className="rounded-xl overflow-hidden cursor-pointer transition-all duration-200"
                        style={{
                            background: isActive ? 'rgba(30,41,59,0.7)' : 'rgba(15,23,42,0.4)',
                            border: `1px solid ${isActive ? color + '55' : 'rgba(255,255,255,0.06)'}`,
                        }}
                        onClick={() => handleClusterClick(cluster.id)}
                        onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && handleClusterClick(cluster.id)}
                        tabIndex={0}
                        aria-expanded={isActive}
                        aria-label={`Cluster: ${cluster.name}`}
                    >
                        {/* Cluster header */}
                        <div className="flex items-center gap-2.5 p-3">
                            <div
                                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                                style={{ backgroundColor: color, boxShadow: isActive ? `0 0 8px ${color}66` : 'none' }}
                                aria-hidden="true"
                            />
                            <span className="text-sm font-semibold text-slate-100 flex-1 truncate">
                                {cluster.name}
                            </span>
                            {isActive
                                ? <ChevronDown  className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" aria-hidden="true" />
                                : <ChevronRight className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" aria-hidden="true" />
                            }
                        </div>

                        {/* Description */}
                        {cluster.description && (
                            <p className="px-3 pb-1.5 text-[11px] text-slate-400 leading-relaxed italic">
                                {cluster.description}
                            </p>
                        )}

                        {/* Stats */}
                        <div className="flex items-center gap-3 px-3 pb-3 text-[10px] font-mono text-slate-500">
                            <span className="inline-flex items-center gap-1">
                                <Layers className="w-3 h-3" aria-hidden="true" />
                                <span aria-label={`${cluster.node_count} nodes`}>{cluster.node_count} nodes</span>
                            </span>
                            <span className="inline-flex items-center gap-1">
                                <FileCode className="w-3 h-3" aria-hidden="true" />
                                <span aria-label={`${cluster.loc_count} lines of code`}>
                                    {cluster.loc_count?.toLocaleString()} LoC
                                </span>
                            </span>
                            <span
                                className="ml-auto px-2 py-0.5 rounded-md text-[9px] font-bold uppercase"
                                style={{
                                    background: riskSt.bg,
                                    color: riskSt.color,
                                    border: `1px solid ${riskSt.border}`,
                                }}
                                aria-label={`Risk: ${cluster.risk}`}
                            >
                                {cluster.risk}
                            </span>
                        </div>

                        {/* Expanded node list */}
                        <AnimatePresence>
                            {isActive && memberNodes.length > 0 && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    transition={{ duration: 0.18 }}
                                    className="overflow-hidden"
                                    style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
                                >
                                    <div className="px-3 py-2 max-h-44 overflow-y-auto space-y-0.5">
                                        {memberNodes.slice(0, 20).map((node) => (
                                            <button
                                                key={node.id}
                                                className="w-full flex items-center gap-2 py-1.5 px-2 rounded-lg text-left transition-colors duration-150 group focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
                                                style={{ background: 'transparent' }}
                                                onClick={e => { e.stopPropagation(); selectNode(node.id); }}
                                                onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                                                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                                                aria-label={`Select node: ${node.name}`}
                                            >
                                                <div
                                                    className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                                                    style={{ backgroundColor: color }}
                                                    aria-hidden="true"
                                                />
                                                <span className="text-[11px] font-mono text-slate-300 group-hover:text-white truncate flex-1">
                                                    {node.name}
                                                </span>
                                                <span className="text-[9px] text-slate-600 uppercase flex-shrink-0">
                                                    {node.type}
                                                </span>
                                            </button>
                                        ))}
                                        {memberNodes.length > 20 && (
                                            <p className="text-[10px] text-slate-600 text-center py-1.5">
                                                +{memberNodes.length - 20} more nodes
                                            </p>
                                        )}

                                        {cluster.responsibilities?.length > 0 && (
                                            <div
                                                className="mt-2 pt-2"
                                                style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
                                            >
                                                <p className="text-[9px] font-bold uppercase text-slate-600 mb-1.5 px-2 tracking-wider">
                                                    Responsibilities
                                                </p>
                                                {cluster.responsibilities.map((r, i) => (
                                                    <div key={i} className="flex items-start gap-1.5 px-2 py-0.5">
                                                        <div
                                                            className="w-1 h-1 rounded-full mt-1.5 flex-shrink-0"
                                                            style={{ backgroundColor: color }}
                                                            aria-hidden="true"
                                                        />
                                                        <span className="text-[10px] text-slate-400 leading-relaxed">{r}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.article>
                );
            })}
        </div>
    );
};

export default ClusterPanel;
