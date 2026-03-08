import { motion } from 'framer-motion';
import clsx from 'clsx';
import useGraphStore from '../../store/useGraphStore';
import { Database, X, MapPin, Phone, Shield, AlertTriangle, MousePointerClick } from 'lucide-react';

const NodeDetailPanel = () => {
    const selectedNodeId = useGraphStore((s) => s.selectedNodeId);
    const rawNodes = useGraphStore((s) => s.rawNodes);
    const rawEdges = useGraphStore((s) => s.rawEdges);
    const clearSelection = useGraphStore((s) => s.clearSelection);

    const selectedNode = selectedNodeId ? rawNodes.find((n) => n.id === selectedNodeId) || null : null;

    if (!selectedNode) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-6 min-h-full">
                <MousePointerClick className="w-16 h-16 text-slate-600 mb-4 animate-pulse" />
                <h3 className="text-lg font-bold text-slate-300 mb-2">Select a Node</h3>
                <p className="text-sm text-slate-500 mb-4">
                    Click on any node in the graph to view its details
                </p>
                <div className="text-xs text-slate-600 space-y-2 mt-4">
                    <p>• Single click to select</p>
                    <p>• Double click to expand/collapse files</p>
                </div>
            </div>
        );
    }

    const risk = selectedNode.risk_level || selectedNode.risk || 'low';
    const type = selectedNode.classification || selectedNode.type || 'function';
    const language = selectedNode.language || 'python';

    const outgoingCalls = rawEdges.filter(e => e.source === selectedNode.id);

    const riskColors = {
        critical: 'text-red-500 bg-red-500/10 border-red-500/30',
        high: 'text-orange-500 bg-orange-500/10 border-orange-500/30',
        moderate: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30',
        medium: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30',
        low: 'text-green-500 bg-green-500/10 border-green-500/30',
        none: 'text-slate-500 bg-slate-500/10 border-slate-500/30'
    };

    return (
        <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            key={selectedNode.id}
            className="flex-1 flex flex-col min-h-full pb-6"
        >
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
                <div className="flex items-center gap-2">
                    <Database className="w-5 h-5 text-blue-400" />
                    <h3 className="text-lg font-bold text-white">{selectedNode.name}</h3>
                </div>
                <button onClick={clearSelection} className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-200">
                    <X className="w-5 h-5" />
                </button>
            </div>

            <div className="p-4 space-y-4">
                <div className="text-xs text-slate-500 font-mono">{selectedNode.id}</div>

                <div>
                    <div className="text-xs text-slate-500 uppercase mb-2">Type</div>
                    <div className="inline-block px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg text-sm font-semibold uppercase border border-blue-500/30">
                        {type}
                    </div>
                </div>

                <div>
                    <div className="text-xs text-slate-500 uppercase mb-2">Language</div>
                    <div className="text-white font-mono">{language}</div>
                </div>

                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-2 h-2 rounded-full bg-green-500"></div>
                        <div className="text-xs text-slate-500 uppercase">Risk: {risk.toUpperCase()}</div>
                    </div>
                    <div className={clsx('px-3 py-2 rounded-lg border text-sm', riskColors[risk])}>
                        {selectedNode.node_summary || 'No specific risk identified'}
                    </div>
                </div>

                {selectedNode.risk_analysis?.risk_factors && (
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <Shield className="w-3 h-3 text-slate-500" />
                            <div className="text-xs text-slate-500 uppercase">Risk Factors</div>
                        </div>
                        <div className="space-y-2">
                            {Object.entries(selectedNode.risk_analysis.risk_factors)
                                .filter(([_, data]) => data.level && data.level !== 'none')
                                .slice(0, 5)
                                .map(([riskName, data], idx) => {
                                    const factorRisk = riskColors[data.level] || riskColors.low;
                                    return (
                                        <div key={idx} className="bg-slate-800/50 rounded-lg p-2 border border-slate-700/50">
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="text-xs font-semibold text-slate-300 capitalize">
                                                    {riskName.replace(/_/g, ' ')}
                                                </span>
                                                <span className={clsx('px-2 py-0.5 rounded text-[10px] uppercase font-bold border', factorRisk)}>
                                                    {data.level}
                                                </span>
                                            </div>
                                            <p className="text-[11px] text-slate-400 leading-relaxed">{data.reason}</p>
                                        </div>
                                    );
                                })}
                        </div>
                    </div>
                )}

                {selectedNode.impact_analysis && (
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <AlertTriangle className="w-3 h-3 text-amber-500" />
                            <div className="text-xs text-slate-500 uppercase">Impact Analysis</div>
                        </div>
                        <div className="grid grid-cols-3 gap-2">
                            <div className="bg-slate-800/50 rounded-lg p-2 text-center border border-slate-700/50">
                                <div className="text-lg font-bold text-white">{selectedNode.impact_analysis.blast_radius_score}</div>
                                <div className="text-[10px] text-slate-400 uppercase">Blast Radius</div>
                            </div>
                            <div className="bg-slate-800/50 rounded-lg p-2 text-center border border-slate-700/50">
                                <div className="text-lg font-bold text-white">{selectedNode.impact_analysis.critical_path_likelihood}</div>
                                <div className="text-[10px] text-slate-400 uppercase">Critical Path</div>
                            </div>
                            <div className="bg-slate-800/50 rounded-lg p-2 text-center border border-slate-700/50">
                                <div className="text-sm font-bold text-white capitalize">{selectedNode.impact_analysis.change_sensitivity}</div>
                                <div className="text-[10px] text-slate-400 uppercase">Sensitivity</div>
                            </div>
                        </div>
                    </div>
                )}

                {selectedNode.file && (
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <MapPin className="w-3 h-3 text-slate-500" />
                            <div className="text-xs text-slate-500 uppercase">Location</div>
                        </div>
                        <div className="bg-slate-950/50 p-3 rounded border border-slate-800">
                            <p className="text-xs font-mono text-slate-300 break-all">
                                {selectedNode.file}
                                {selectedNode.line_start && <span className="text-blue-400">:{selectedNode.line_start}</span>}
                            </p>
                        </div>
                    </div>
                )}

                {outgoingCalls.length > 0 && (
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <Phone className="w-3 h-3 text-slate-500" />
                            <div className="text-xs text-slate-500 uppercase">Calls ({outgoingCalls.length})</div>
                        </div>
                        <div className="space-y-1">
                            {outgoingCalls.slice(0, 10).map((edge, idx) => {
                                const targetNode = rawNodes.find(n => n.id === edge.target);
                                return (
                                    <div key={idx} className="text-xs font-mono text-slate-400 hover:text-slate-200 cursor-pointer px-2 py-1 hover:bg-slate-800/50 rounded">
                                        {targetNode?.name || edge.target}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
};

export default NodeDetailPanel;
