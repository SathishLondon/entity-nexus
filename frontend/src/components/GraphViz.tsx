'use client';

import React, { useCallback, useEffect } from 'react';
import {
    ReactFlow,
    useNodesState,
    useEdgesState,
    addEdge,
    MiniMap,
    Controls,
    Background,
    Connection,
    Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface GraphVizProps {
    initialNodes?: any[];
    initialEdges?: any[];
}

const GraphViz: React.FC<GraphVizProps> = ({ initialNodes = [], initialEdges = [] }) => {
    // Transform edges to include labels if they have data
    const processEdges = (edges: any[]) => {
        return edges.map(edge => ({
            ...edge,
            label: edge.data && edge.data.ownership_percentage
                ? `${edge.data.ownership_percentage}%`
                : edge.label || '',
            style: { stroke: '#555' },
            labelStyle: { fill: '#333', fontWeight: 700 },
        }));
    };

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(processEdges(initialEdges));

    useEffect(() => {
        setNodes(initialNodes);
        setEdges(processEdges(initialEdges));
    }, [initialNodes, initialEdges, setNodes, setEdges]);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges],
    );

    return (
        <div style={{ width: '100%', height: '80vh', border: '1px solid #ddd' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                fitView
            >
                <Controls />
                <MiniMap />
                <Background gap={12} size={1} />
            </ReactFlow>
        </div>
    );
};

export default GraphViz;
