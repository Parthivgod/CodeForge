import React, { useState } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import MetricsCards from './MetricsCards';
import TreeExplorer from './TreeExplorer';
import ActionBar from './ActionBar';
import { CheckCircle2, ChevronRight, FileCode, Package, Zap } from 'lucide-react';

const ResultsDashboard = ({ results, jobId, onReset }) => {
    const {
        nodes = [],
        tree_data: treeData = { nodes: [], edges: [] },
        stats = { confidence: '0%', nodes: 0, edges: 0, loc: '0' },
        report = ""
    } = results;
    const [selectedNodeId, setSelectedNodeId] = useState(null);
    const [filterEdgeType, setFilterEdgeType] = useState('all');

    // Filter edges based on type
    const filteredEdges = filterEdgeType === 'all'
        ? treeData.edges
        : treeData.edges.filter(e => e.label === filterEdgeType);

    // Find the full data for the selected node
    const selectedNode = selectedNodeId !== null
        ? nodes.find(n => n.id === selectedNodeId)
        : null;

    const handleNodeClick = (node) => {
        if (node.id === 'root') {
            setSelectedNodeId(null);
        } else {
            setSelectedNodeId(node.id);
        }
    };

    // Use report for insight or a default fallback
    const firstInsight = report ? report.split('\n')[0].replace('# ', '') : "Codebase graph generated with granular nodes and relations.";

    return (
        <div className="max-w-7xl mx-auto p-4 md:p-8 animate-in fade-in duration-700">

            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h2 className="text-3xl font-bold flex items-center gap-3">
                        <CheckCircle2 className="text-green-500 w-8 h-8" />
                        Graph Analysis Complete
                    </h2>
                    <p className="text-slate-400 mt-1">Analysis finished • AI Confidence Score: {stats.confidence}</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 bg-slate-900/50 border border-slate-800 rounded-lg px-3 py-1.5 glass">
                        <label htmlFor="edge-filter" className="text-[10px] uppercase font-bold text-slate-500 whitespace-nowrap">Show Relations:</label>
                        <select
                            id="edge-filter"
                            value={filterEdgeType}
                            onChange={(e) => setFilterEdgeType(e.target.value)}
                            className="bg-transparent text-xs font-mono text-blue-400 outline-none cursor-pointer hover:text-blue-300 transition-colors"
                        >
                            <option value="all" className="bg-slate-900 text-slate-300">All Types</option>
                            <option value="calls" className="bg-slate-900 text-slate-300">Function Calls</option>
                            <option value="structural" className="bg-slate-900 text-slate-300">Structural</option>
                            <option value="dependency" className="bg-slate-900 text-slate-300">Dependencies</option>
                            <option value="flow" className="bg-slate-900 text-slate-300">Data Flow</option>
                        </select>
                    </div>
                    <span className="px-3 py-1 bg-green-500/10 text-green-400 text-xs font-mono rounded border border-green-500/20 uppercase">
                        JOB-ID: {jobId?.substring(0, 8)}
                    </span>
                </div>
            </div>

            <MetricsCards stats={{ ...stats, edges: filteredEdges.length }} />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2">
                    <TreeExplorer
                        nodes={treeData.nodes}
                        edges={filteredEdges}
                        onNodeClick={handleNodeClick}
                    />
                </div>

                <div className="space-y-6">
                    {/* Selected Node Detail Panel */}
                    <div className="glass p-6 rounded-xl border border-slate-800 transition-all min-h-[300px]">
                        {selectedNode ? (
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                key={selectedNode.id}
                            >
                                <div className="flex items-center gap-2 mb-4">
                                    <Package className="w-5 h-5 text-blue-400" />
                                    <h3 className="text-lg font-bold text-white truncate">{selectedNode.name}</h3>
                                </div>
                                <p className="text-xs font-mono text-slate-500 mb-4">{selectedNode.id}</p>

                                <div className="space-y-4">
                                    <div className="flex items-center justify-between text-xs px-2 py-1 bg-slate-800/50 rounded">
                                        <span className="text-slate-500 uppercase">Type</span>
                                        <span className="font-bold uppercase text-blue-400">
                                            {selectedNode.type}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between text-xs px-2 py-1 bg-slate-800/50 rounded">
                                        <span className="text-slate-500 uppercase">Language</span>
                                        <span className="font-bold text-slate-300">
                                            {selectedNode.language || 'N/A'}
                                        </span>
                                    </div>

                                    {/* Risk Analysis Section */}
                                    <div className={clsx(
                                        "p-3 rounded-lg border",
                                        selectedNode.risk_level === 'high' ? "bg-red-500/10 border-red-500/20" :
                                            selectedNode.risk_level === 'medium' ? "bg-yellow-500/10 border-yellow-500/20" : "bg-green-500/10 border-green-500/20"
                                    )}>
                                        <h4 className={clsx(
                                            "text-xs font-bold uppercase mb-1 flex items-center gap-1",
                                            selectedNode.risk_level === 'high' ? "text-red-400" :
                                                selectedNode.risk_level === 'medium' ? "text-yellow-400" : "text-green-400"
                                        )}>
                                            <Zap className="w-3 h-3" /> Risk: {selectedNode.risk_level}
                                        </h4>
                                        <p className="text-[11px] text-slate-300 italic">
                                            {selectedNode.failure_reason}
                                        </p>
                                    </div>

                                    <div>
                                        <h4 className="text-xs font-bold text-slate-500 uppercase mb-2 flex items-center gap-1">
                                            <FileCode className="w-3 h-3" /> Location
                                        </h4>
                                        <div className="text-[11px] font-mono text-slate-400 bg-black/20 p-2 rounded break-all transition-colors">
                                            {selectedNode.file}:{selectedNode.line_start}
                                        </div>
                                    </div>

                                    {selectedNode.calls && selectedNode.calls.length > 0 && (
                                        <div>
                                            <h4 className="text-xs font-bold text-slate-500 uppercase mb-2">Calls ({selectedNode.calls.length})</h4>
                                            <div className="max-h-32 overflow-y-auto space-y-1 pr-2 thin-scrollbar">
                                                {selectedNode.calls.map((call, i) => (
                                                    <div key={i} className="text-[10px] font-mono text-slate-400 bg-slate-800/30 p-1 rounded">
                                                        {call}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <button
                                    onClick={() => setSelectedNodeId(null)}
                                    className="mt-6 w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded transition-colors"
                                >
                                    Clear Selection
                                </button>
                            </motion.div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-center py-10 opacity-50">
                                <Package className="w-10 h-10 text-slate-600 mb-3" />
                                <h3 className="text-sm font-bold text-slate-300">Node Details</h3>
                                <p className="text-xs text-slate-500 mt-1">Select a function or class in the graph to explore its properties</p>
                            </div>
                        )}
                    </div>

                    {/* AI Insight Card */}
                    <div className="glass p-6 rounded-xl border-l-4 border-l-purple-500">
                        <h3 className="text-sm font-bold text-purple-400 uppercase mb-2">Architect Insight</h3>
                        <p className="text-sm text-slate-300 leading-relaxed italic">
                            "{firstInsight}"
                        </p>
                    </div>

                    <ActionBar
                        onReset={onReset}
                        onDownload={() => alert('Downloading graph data...')}
                        onDeploy={() => alert('Deploying to Cloud...')}
                    />
                </div>
            </div>
        </div>
    );
};
export default ResultsDashboard;
