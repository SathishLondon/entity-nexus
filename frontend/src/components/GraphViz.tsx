'use client';

import React, { useCallback, useEffect, useState } from 'react';
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
    Node
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface GraphVizProps {
    initialNodes?: Node[];
    initialEdges?: Edge[];
}

const GraphViz: React.FC<GraphVizProps> = ({ initialNodes = [], initialEdges = [] }) => {
    const [riskMode, setRiskMode] = useState(false);

    // Transform edges to include labels if they have data
    const processEdges = useCallback((edges: Edge[]) => {
        return edges.map(edge => ({
            ...edge,
            label: edge.data && edge.data.ownership_percentage
                ? `${edge.data.ownership_percentage}%`
                : edge.label || '',
            style: { stroke: '#555' },
            labelStyle: { fill: '#333', fontWeight: 700 },
        }));
    }, []);

    // Transform nodes for Risk Mode
    const processNodes = useCallback((nodes: Node[], isRiskMode: boolean) => {
        return nodes.map(node => {
            let style = { background: '#fff', border: '1px solid #777', width: 180, padding: 10, borderRadius: 5 };

            if (isRiskMode) {
                const score = (node.data?.risk_score as number) || 0;
                if (score > 75) style = { ...style, background: '#fee2e2', border: '2px solid #ef4444' }; // Red
                else if (score > 50) style = { ...style, background: '#fef3c7', border: '2px solid #f59e0b' }; // Yellow
                else style = { ...style, background: '#dcfce7', border: '2px solid #22c55e' }; // Green
            }

            return {
                ...node,
                style,
                data: {
                    ...node.data,
                    label: (
                        <div>
                            <div className="font-bold">{String(node.data.name || node.id)}</div>
                            {isRiskMode && (
                                <div className="text-xs mt-1">
                                    Risk Score: {node.data.risk_score || 'N/A'}
                                </div>
                            )}
                        </div>
                    )
                }
            };
        });
    }, []);

    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);

    useEffect(() => {
        setNodes(processNodes(initialNodes, riskMode));
        setEdges(processEdges(initialEdges));
    }, [initialNodes, initialEdges, riskMode, processNodes, processEdges, setNodes, setEdges]);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges],
    );

    return (
        <div style={{ width: '100%', height: '80vh', border: '1px solid #ddd', position: 'relative' }}>
            <div className="absolute top-4 right-4 z-10 bg-white p-2 rounded shadow border border-gray-200">
                <label className="flex items-center space-x-2 text-sm font-medium text-gray-700 cursor-pointer">
                    <input
                        type="checkbox"
                        checked={riskMode}
                        onChange={(e) => setRiskMode(e.target.checked)}
                        className="form-checkbox h-4 w-4 text-blue-600 rounded"
                    />
                    <span>Risk Heatmap</span>
                </label>
                {riskMode && (
                    <div className="mt-2 text-xs space-y-1">
                        <div className="flex items-center"><span className="w-3 h-3 bg-red-200 border border-red-500 mr-2"></span> High (&gt;75)</div>
                        <div className="flex items-center"><span className="w-3 h-3 bg-yellow-100 border border-yellow-500 mr-2"></span> Medium (&gt;50)</div>
                        <div className="flex items-center"><span className="w-3 h-3 bg-green-100 border border-green-500 mr-2"></span> Low (&lt;50)</div>
                    </div>
                )}
            </div>

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
