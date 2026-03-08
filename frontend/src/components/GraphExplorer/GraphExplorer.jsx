import React from 'react';
import SigmaRenderer from './SigmaRenderer';
import FilterToolbar from './FilterToolbar';
import NodeDetailPanel from './NodeDetailPanel';
import useGraphStore from '../../store/useGraphStore';

const GraphExplorer = ({ nodes, edges }) => {
    return (
        <div className="flex flex-col h-full">
            {/* Top toolbar */}
            <FilterToolbar />

            {/* Graph canvas - full width */}
            <div className="flex-1 relative">
                <SigmaRenderer nodes={nodes} edges={edges} />
            </div>
        </div>
    );
};

export default GraphExplorer;
