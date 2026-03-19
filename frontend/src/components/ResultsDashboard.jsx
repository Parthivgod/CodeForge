import React, { useEffect, useState } from 'react';
import MetricsCards from './MetricsCards';
import GraphExplorer from './GraphExplorer/GraphExplorer';
import NodeDetailPanel from './GraphExplorer/NodeDetailPanel';
import ClusterPanel from './ClusterPanel';
import ActionBar from './ActionBar';
import { CheckCircle2, GitFork, Database, Sparkles } from 'lucide-react';
import { downloadReport } from '../utils/reportGenerator';
import useGraphStore from '../store/useGraphStore';

const ResultsDashboard = ({ results, jobId, onReset }) => {
    const {
        nodes = [],
        edges = [],
        tree_data: treeData = { nodes: [], edges: [] },
        stats = { confidence: '0%', nodes: 0, edges: 0, loc: '0' },
        report = '',
        clusters = [],
    } = results;

    const setClusters = useGraphStore((s) => s.setClusters);
    const [rightTab, setRightTab] = useState('node');

    useEffect(() => {
        if (clusters.length > 0) setClusters(clusters);
    }, [clusters, setClusters]);

    const graphEdges = edges.length > 0 ? edges : treeData.edges;

    const extractInsight = (raw) => {
        if (!raw) return 'Codebase graph generated with granular nodes and relations.';
        const lines = raw.split('\n').map(l => l.replace(/^#+\s*/, '').trim()).filter(Boolean);
        const insightLine = lines.find(l => /risk|insight|architect|confidence/i.test(l));
        return insightLine || lines[0] || 'Codebase graph generated with granular nodes and relations.';
    };
    const firstInsight = extractInsight(report);

    const tabs = [
        { id: 'node',     icon: Database, label: 'Node',     accentColor: '#3b82f6', borderColor: '#3b82f6' },
        { id: 'clusters', icon: GitFork,  label: 'Clusters', accentColor: '#f97316', borderColor: '#f97316', badge: clusters.length > 0 ? clusters.length : null },
    ];

    return (
        <div
            className="w-full h-screen flex flex-col"
            style={{ background: '#0a0f1e' }}
            role="main"
            aria-label="Analysis results dashboard"
        >
            {/* ── Header ───────────────────────────────────────────── */}
            <header
                className="flex items-center justify-between px-6 py-4 flex-shrink-0"
                style={{
                    background: 'rgba(15,23,42,0.88)',
                    backdropFilter: 'blur(12px)',
                    borderBottom: '1px solid rgba(255,255,255,0.07)',
                }}
            >
                <div className="flex items-center gap-3 min-w-0">
                    <div
                        className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)' }}
                        aria-hidden="true"
                    >
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div className="min-w-0">
                        <h1 className="text-base font-bold text-slate-100 leading-tight">
                            Graph Analysis Complete
                        </h1>
                        <p className="text-xs text-slate-500 mt-0.5 truncate">
                            AI Confidence:&nbsp;
                            <span className="text-slate-400 font-medium tabular-nums">{stats.confidence}</span>
                            &nbsp;·&nbsp;
                            <span className="tabular-nums">{stats.nodes}</span> nodes
                            &nbsp;·&nbsp;
                            <span className="tabular-nums">{stats.edges}</span> edges
                            &nbsp;·&nbsp;
                            <span className="tabular-nums">{stats.loc}</span> LoC
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3 flex-shrink-0">
                    {jobId && (
                        <span
                            className="hidden sm:inline-flex items-center px-3 py-1 rounded-lg text-[11px] font-mono font-semibold uppercase tracking-wider"
                            style={{
                                background: 'rgba(16,185,129,0.08)',
                                color: '#6ee7b7',
                                border: '1px solid rgba(16,185,129,0.2)',
                            }}
                            aria-label={`Job ID: ${jobId.substring(0, 8)}`}
                        >
                            Job {jobId.substring(0, 8)}
                        </span>
                    )}
                    <ActionBar
                        onReset={onReset}
                        onDownload={() =>
                            downloadReport(nodes, graphEdges, `analysis-report-${jobId?.substring(0, 8)}.md`)
                        }
                    />
                </div>
            </header>

            {/* ── Metrics row ──────────────────────────────────────── */}
            <div
                className="px-5 py-3 flex-shrink-0"
                style={{ background: 'rgba(15,23,42,0.55)', borderBottom: '1px solid rgba(255,255,255,0.05)' }}
            >
                <MetricsCards stats={stats} />
            </div>

            {/* ── AI Insight banner ────────────────────────────────── */}
            <div
                className="px-5 py-2.5 flex-shrink-0 flex items-center gap-2.5"
                style={{ background: 'rgba(139,92,246,0.06)', borderBottom: '1px solid rgba(139,92,246,0.12)' }}
                role="note"
                aria-label="AI architect insight"
            >
                <Sparkles className="flex-shrink-0 w-3.5 h-3.5 text-purple-400" aria-hidden="true" />
                <p className="text-xs text-purple-300 italic leading-relaxed line-clamp-1">
                    <span className="not-italic font-bold text-purple-400 uppercase tracking-wider mr-2 text-[10px]">
                        Architect Insight
                    </span>
                    {firstInsight}
                </p>
            </div>

            {/* ── Main content ─────────────────────────────────────── */}
            <div className="flex-1 min-h-0 flex overflow-hidden">
                {/* Graph explorer */}
                <div className="flex-1 min-w-0">
                    <GraphExplorer nodes={nodes} edges={graphEdges} />
                </div>

                {/* Right panel */}
                <aside
                    className="w-80 flex-shrink-0 flex flex-col"
                    style={{ borderLeft: '1px solid rgba(255,255,255,0.07)', background: 'rgba(15,23,42,0.6)' }}
                    aria-label="Detail panel"
                >
                    {/* Tab bar */}
                    <div
                        className="flex flex-shrink-0"
                        role="tablist"
                        aria-label="Panel tabs"
                        style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}
                    >
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                role="tab"
                                aria-selected={rightTab === tab.id}
                                aria-controls={`panel-${tab.id}`}
                                id={`tab-${tab.id}`}
                                onClick={() => setRightTab(tab.id)}
                                className="flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-semibold uppercase tracking-wider transition-colors duration-150 relative focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
                                style={{
                                    color: rightTab === tab.id ? (tab.id === 'clusters' ? '#fb923c' : '#60a5fa') : '#64748b',
                                    background: rightTab === tab.id ? 'rgba(255,255,255,0.04)' : 'transparent',
                                }}
                            >
                                {rightTab === tab.id && (
                                    <span
                                        className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
                                        style={{ background: tab.borderColor }}
                                        aria-hidden="true"
                                    />
                                )}
                                <tab.icon className="w-3.5 h-3.5" aria-hidden="true" />
                                {tab.label}
                                {tab.badge != null && (
                                    <span
                                        className="ml-0.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold"
                                        style={{
                                            background: 'rgba(249,115,22,0.18)',
                                            color: '#fdba74',
                                            border: '1px solid rgba(249,115,22,0.25)',
                                        }}
                                        aria-label={`${tab.badge} clusters`}
                                    >
                                        {tab.badge}
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Tab content */}
                    <div
                        className="flex-1 overflow-y-auto p-4"
                        id={`panel-${rightTab}`}
                        role="tabpanel"
                        aria-labelledby={`tab-${rightTab}`}
                    >
                        {rightTab === 'node' ? <NodeDetailPanel /> : <ClusterPanel />}
                    </div>
                </aside>
            </div>
        </div>
    );
};

export default ResultsDashboard;
