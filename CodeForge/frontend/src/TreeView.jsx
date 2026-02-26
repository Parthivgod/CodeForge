import { useCallback, useEffect } from 'react';
import ReactFlow, {
    MiniMap,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Position
} from 'react-flow-renderer';
import dagre from 'dagre';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 200;
const nodeHeight = 80;

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
    const isHorizontal = direction === 'LR';
    dagreGraph.setGraph({ rankdir: direction });

    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
    });

    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    return {
        nodes: nodes.map((node) => {
            const nodeWithPosition = dagreGraph.node(node.id);
            node.targetPosition = isHorizontal ? Position.Left : Position.Top;
            node.sourcePosition = isHorizontal ? Position.Right : Position.Bottom;

            // We are shifting the dagre node position (which is center) to top left for react flow
            node.position = {
                x: nodeWithPosition.x - nodeWidth / 2,
                y: nodeWithPosition.y - nodeHeight / 2,
            };

            return node;
        }),
        edges,
    };
};

const nodeColor = (node) => {
    switch (node.data.type) {
        case 'class': return '#6366f1'; // indigo-500
        case 'api_call': return '#f59e0b'; // amber-500
        case 'function': return '#10b981'; // emerald-500
        default: return '#3b82f6'; // blue-500
    }
};

const TreeView = ({ nodes: initialNodes, edges: initialEdges, onNodeClick }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        if (initialNodes.length > 0) {
            const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
                initialNodes,
                initialEdges
            );
            setNodes([...layoutedNodes]);
            setEdges([...layoutedEdges]);
        }
    }, [initialNodes, initialEdges, setNodes, setEdges]);

    const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

    const handleNodeClick = (event, node) => {
        if (onNodeClick) {
            onNodeClick(node);
        }
    };

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeClick={handleNodeClick}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                minZoom={0.05}
                maxZoom={2}
                attributionPosition="bottom-right"
            >
                <Controls />
                <MiniMap
                    nodeColor={nodeColor}
                    nodeStrokeWidth={3}
                    zoomable
                    pannable
                />
                <Background
                    color="#334155"
                    gap={20}
                    variant="dots"
                    style={{ background: '#0f172a' }}
                />
            </ReactFlow>
        </div>
    );
};

export default TreeView;

