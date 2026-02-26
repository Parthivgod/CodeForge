import React from 'react';
import TreeView from '../TreeView';
import { Expand } from 'lucide-react';

const TreeExplorer = ({ nodes, edges, onNodeClick }) => {
    return (
        <div className="bg-slate-900 rounded-xl overflow-hidden border border-slate-800 shadow-2xl relative h-[600px] group">

            {/* Header Overlay */}
            <div className="absolute top-4 left-4 z-10 glass px-3 py-1.5 rounded-lg flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-xs font-mono text-slate-300">Live Graph Preview</span>
            </div>

            <div className="h-full w-full bg-slate-950/50">
                <TreeView nodes={nodes} edges={edges} onNodeClick={onNodeClick} />
            </div>


            {/* Legend */}
            <div className="absolute bottom-4 right-4 z-10 glass p-3 rounded-xl text-[10px] space-y-2 border border-slate-800">
                <div className="font-bold text-slate-500 uppercase mb-1 tracking-wider">Node Risk Level</div>
                <div className="flex items-center gap-2 text-slate-300"><span className="w-3 h-3 rounded-full border-2 border-red-500 shadow-[0_0_5px_rgba(239,68,68,0.5)]" /> High Failure Risk</div>
                <div className="flex items-center gap-2 text-slate-300"><span className="w-3 h-3 rounded-full border-2 border-yellow-500 shadow-[0_0_5px_rgba(234,179,8,0.5)]" /> Medium Risk</div>
                <div className="flex items-center gap-2 text-slate-300"><span className="w-3 h-3 rounded-full border-0 bg-green-500/50" /> Stable Function</div>

                <div className="h-px bg-slate-800 my-2" />
                <div className="font-bold text-slate-500 uppercase mb-1 tracking-wider">Relation Types</div>
                <div className="flex items-center gap-2 text-slate-300"><span className="w-3 h-0.5" style={{ backgroundColor: '#94a3b8' }} /> Calls</div>
                <div className="flex items-center gap-2 text-slate-300"><span className="w-3 h-0.5" style={{ backgroundColor: '#6366f1' }} /> Structural</div>
                <div className="flex items-center gap-2 text-slate-300"><span className="w-3 h-0.5" style={{ backgroundColor: '#475569' }} /> Dependency</div>
                <div className="flex items-center gap-2 text-slate-300"><span className="w-3 h-0.5" style={{ backgroundColor: '#a855f7' }} /> Flow</div>
            </div>
        </div>
    );
};

export default TreeExplorer;
