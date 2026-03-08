import React from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import useGraphStore from '../../store/useGraphStore';
import {
    Package,
    FileCode,
    Zap,
    CheckCircle2,
    X,
    AlertTriangle,
    Shield,
    Terminal,
    Box,
    Globe,
    Database,
    Cpu
} from 'lucide-react';

const TYPE_ICONS = {
    function: <Cpu className="w-4 h-4" />,
    api_call: <Globe className="w-4 h-4" />,
    class: <Box className="w-4 h-4" />,
    module: <Package className="w-4 h-4" />,
    file: <FileCode className="w-4 h-4" />,
    database: <Database className="w-4 h-4" />,
    external: <Globe className="w-4 h-4" />,
};

const NodeDetailPanel = () => {
    const selectedNodeId = useGraphStore((s) => s.selectedNodeId);
    const rawNodes = useGraphStore((s) => s.rawNodes);
    const clearSelection = useGraphStore((s) => s.clearSelection);

    const selectedNode = selectedNodeId
        ? rawNodes.find((n) => n.id === selectedNodeId) || null
        : null;

    if (!selectedNode) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-center py-10 opacity-50">
                <Package className="w-10 h-10 text-slate-600 mb-3" />
                <h3 className="text-sm font-bold text-slate-300">Node Details</h3>
                <p className="text-xs text-slate-500 mt-1">
                    Select a node in the graph to explore its properties
                </p>
            </div>
        );
    }

    const risk = selectedNode.risk_level || selectedNode.risk || 'low';
    const type = selectedNode.classification || selectedNode.type || 'function';

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            key={selectedNode.id}
            className="space-y-3 min-h-full"
        >
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                    <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                        {TYPE_ICONS[type] || <Terminal className="w-5 h-5" />}
                    </div>
                    <div className="min-w-0">
                        <h3 className="text-lg font-bold text-white truncate">{selectedNode.name}</h3>
                        <p className="text-[10px] font-mono text-slate-500 truncate">{type.toUpperCase()}</p>
                    </div>
                </div>
                <button
                    onClick={clearSelection}
                    className="p-1 rounded hover:bg-slate-700 text-slate-500 hover:text-slate-300 transition-colors flex-shrink-0"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            {/* Classification Quick Badge (New Prominent View) */}
            <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="text-blue-400">
                        {TYPE_ICONS[type] || <Terminal className="w-4 h-4" />}
                    </div>
                    <span className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                        {type.replace('_', ' ')}
                    </span>
                </div>
                <div className={clsx(
                    "px-2 py-0.5 rounded text-[9px] font-black uppercase border",
                    risk === 'critical' ? "bg-red-500/20 text-red-500 border-red-500/30" :
                        risk === 'high' ? "bg-orange-500/20 text-orange-500 border-orange-500/30" :
                            risk === 'medium' || risk === 'moderate' ? "bg-yellow-500/20 text-yellow-500 border-yellow-500/30" :
                                "bg-green-500/20 text-green-500 border-green-500/30"
                )}>
                    {risk} Risk
                </div>
            </div>

            <p className="text-[10px] font-mono text-slate-600 break-all">{selectedNode.id}</p>

            {/* Summary */}
            {selectedNode.node_summary && (
                <div className="text-sm text-slate-300 italic border-l-2 border-slate-700 pl-3 py-1">
                    {selectedNode.node_summary}
                </div>
            )}

            {/* Impact Analysis */}
            {selectedNode.impact_analysis && (
                <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-3">
                    <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-2 tracking-wider flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> Impact Analysis
                    </h4>
                    <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-slate-800/50 rounded p-1">
                            <div className="text-lg font-bold text-white">
                                {selectedNode.impact_analysis.blast_radius_score}/10
                            </div>
                            <div className="text-[9px] text-slate-400 uppercase">Blast Radius</div>
                        </div>
                        <div className="bg-slate-800/50 rounded p-1">
                            <div className="text-lg font-bold text-white">
                                {selectedNode.impact_analysis.critical_path_likelihood}/10
                            </div>
                            <div className="text-[9px] text-slate-400 uppercase">Critical Path</div>
                        </div>
                        <div className="bg-slate-800/50 rounded p-1">
                            <div className="text-sm font-bold text-white mt-1 capitalize">
                                {selectedNode.impact_analysis.change_sensitivity}
                            </div>
                            <div className="text-[9px] text-slate-400 uppercase mt-1">Sensitivity</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Risk Factors */}
            <div
                className={clsx(
                    'p-3 rounded-lg border',
                    risk === 'high' || risk === 'critical'
                        ? 'bg-red-500/5 border-red-500/20'
                        : risk === 'medium' || risk === 'moderate'
                            ? 'bg-yellow-500/5 border-yellow-500/20'
                            : 'bg-green-500/5 border-green-500/20'
                )}
            >
                <h4
                    className={clsx(
                        'text-xs font-bold uppercase mb-3 flex items-center gap-1',
                        risk === 'high' || risk === 'critical'
                            ? 'text-red-400'
                            : risk === 'medium' || risk === 'moderate'
                                ? 'text-yellow-400'
                                : 'text-green-400'
                    )}
                >
                    <Shield className="w-4 h-4" /> Risk Analysis
                </h4>

                {selectedNode.risk_analysis?.risk_factors ? (
                    <div className="space-y-3">
                        {Object.entries(selectedNode.risk_analysis.risk_factors)
                            .filter(([_, data]) => data.level && data.level !== 'none')
                            .map(([riskName, data], idx) => (
                                <div
                                    key={idx}
                                    className="bg-slate-900/50 rounded p-2 text-xs border border-slate-700/50"
                                >
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="font-mono text-slate-300 capitalize">
                                            {riskName.replace(/_/g, ' ')}
                                        </span>
                                        <span
                                            className={clsx(
                                                'px-1.5 py-0.5 rounded text-[9px] uppercase font-bold',
                                                data.level === 'critical'
                                                    ? 'bg-red-500 text-white'
                                                    : data.level === 'high'
                                                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                                                        : data.level === 'moderate'
                                                            ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                                                            : 'bg-slate-700 text-slate-300'
                                            )}
                                        >
                                            {data.level}
                                        </span>
                                    </div>
                                    <div className="text-[10px] text-slate-400 italic font-sans leading-relaxed">{data.reason}</div>
                                </div>
                            ))}
                    </div>
                ) : (
                    <p className="text-[11px] text-slate-400 italic">No specific risk factors detected.</p>
                )}
            </div>

            {/* Architecture Role */}
            <div className="flex flex-col text-xs px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg">
                <span className="text-slate-500 uppercase text-[9px] font-bold mb-1 tracking-wider">Architectural Role</span>
                <span className="font-bold text-slate-200 uppercase">
                    {selectedNode.architectural_role || 'General Component'}
                </span>
            </div>

            {/* Sensitive Behaviors */}
            {selectedNode.sensitive_behaviors &&
                Object.keys(selectedNode.sensitive_behaviors).some(
                    (k) => selectedNode.sensitive_behaviors[k]
                ) && (
                    <div>
                        <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-2 tracking-wider flex items-center gap-1">
                            <Zap className="w-3 h-3 text-amber-500" /> Sensitive Behaviors
                        </h4>
                        <div className="flex flex-wrap gap-2">
                            {Object.entries(selectedNode.sensitive_behaviors).map(([key, val]) =>
                                val ? (
                                    <span
                                        key={key}
                                        className="px-2 py-1 bg-amber-500/10 text-amber-500 border border-amber-500/20 text-[10px] uppercase font-mono rounded"
                                    >
                                        {key.replace(/_/g, ' ')}
                                    </span>
                                ) : null
                            )}
                        </div>
                    </div>
                )}

            {/* File location */}
            {selectedNode.file && (
                <div className="pt-2 border-t border-slate-800">
                    <h4 className="text-[10px] font-bold text-slate-500 uppercase mb-2 flex items-center gap-1 tracking-wider">
                        <FileCode className="w-3 h-3" /> Location
                    </h4>
                    <div className="text-[11px] font-mono text-slate-400 bg-black/40 p-2 rounded break-all border border-slate-800">
                        {selectedNode.file}
                        {selectedNode.line_start ? `:${selectedNode.line_start}` : ''}
                    </div>
                </div>
            )}
        </motion.div>
    );
};

export default NodeDetailPanel;
