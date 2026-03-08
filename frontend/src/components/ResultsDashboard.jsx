import React from 'react';
import MetricsCards from './MetricsCards';
import GraphExplorer from './GraphExplorer/GraphExplorer';
import ActionBar from './ActionBar';
import { CheckCircle2 } from 'lucide-react';

const ResultsDashboard = ({ results, jobId, onReset }) => {
    const {
        nodes = [],
        edges = [],
        tree_data: treeData = { nodes: [], edges: [] },
        stats = { confidence: '0%', nodes: 0, edges: 0, loc: '0' },
        report = ""
    } = results;

    // Use raw backend edges and nodes directly (not React Flow formatted ones)
    const graphEdges = edges.length > 0 ? edges : treeData.edges;

    // Extract best insight from backend report
    const extractInsight = (raw) => {
        if (!raw) return "Codebase graph generated with granular nodes and relations.";
        const lines = raw.split('\n').map(l => l.replace(/^#+\s*/, '').trim()).filter(Boolean);
        // Prioritize lines containing risk / architectural role info
        const insightLine = lines.find(l => /risk|insight|architect|confidence/i.test(l));
        return insightLine || lines[0] || "Codebase graph generated with granular nodes and relations.";
    };
    const firstInsight = extractInsight(report);

    return (
        <div className="w-full h-screen flex flex-col bg-slate-950">

            {/* Header bar */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md flex-shrink-0">
                <div>
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <CheckCircle2 className="text-green-500 w-6 h-6" />
                        Graph Analysis Complete
                    </h2>
                    <p className="text-slate-500 text-xs mt-0.5">
                        AI Confidence: {stats.confidence} • {stats.nodes} nodes • {stats.edges} edges • {stats.loc} LoC
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <span className="px-3 py-1 bg-green-500/10 text-green-400 text-xs font-mono rounded border border-green-500/20 uppercase">
                        JOB-ID: {jobId?.substring(0, 8)}
                    </span>
                    <ActionBar
                        onReset={onReset}
                        onDownload={() => alert('Downloading graph data...')}
                        onDeploy={() => alert('Deploying to Cloud...')}
                    />
                </div>
            </div>

            {/* Mini metrics row */}
            <div className="px-6 py-3 border-b border-slate-800 bg-slate-900/50 flex-shrink-0">
                <MetricsCards stats={stats} />
            </div>

            {/* AI Insight banner */}
            <div className="px-6 py-2 border-b border-slate-800 bg-slate-900/30 flex-shrink-0">
                <p className="text-xs text-purple-400 italic">
                    <span className="font-bold uppercase mr-2">Architect Insight:</span>
                    "{firstInsight}"
                </p>
            </div>

            {/* Graph explorer fills remaining space */}
            <div className="flex-1 min-h-0">
                <GraphExplorer
                    nodes={nodes}
                    edges={graphEdges}
                />
            </div>
        </div>
    );
};

export default ResultsDashboard;
