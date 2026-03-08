import React from 'react';
import SigmaRenderer from './SigmaRenderer';
import FilterToolbar from './FilterToolbar';
import NodeDetailPanel from './NodeDetailPanel';
import useGraphStore from '../../store/useGraphStore';

const GraphExplorer = ({ nodes, edges }) => {
    const selectedNodeId = useGraphStore((s) => s.selectedNodeId);

    return (
        <div className="flex flex-col h-full">
            {/* Top toolbar */}
            <FilterToolbar />

            {/* Main area: graph + detail panel */}
            <div className="flex flex-1 min-h-0">
                {/* Graph canvas */}
                <div className="flex-1 relative">
                    <SigmaRenderer nodes={nodes} edges={edges} />
                </div>

                {/* Right detail panel */}
                <div
                    className={`transition-all duration-300 overflow-y-auto border-l border-slate-800 bg-slate-900/70 backdrop-blur-md flex-shrink-0 ${selectedNodeId ? 'w-80 min-w-[320px] p-4' : 'w-0 min-w-0 p-0 overflow-hidden'
                        }`}
                >
                    <NodeDetailPanel />
                </div>
            </div>
        </div>
    );
};

export default GraphExplorer;
