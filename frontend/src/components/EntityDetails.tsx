'use client';

import React, { useEffect, useState } from 'react';

interface LineageInfo {
    source: string;
    payload_id: string;
    confidence: number;
    file_name?: string;
    json_path?: string;
}

interface EntityData {
    name: string;
    legal_name: string;
    revenue_usd: number;
    employee_count: number;
    jurisdiction_code: string;
    lineage_metadata: Record<string, LineageInfo>;
}

interface EntityDetailsProps {
    entityId: string;
}

export default function EntityDetails({ entityId }: EntityDetailsProps) {
    const [data, setData] = useState<EntityData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!entityId) return;

        const fetchData = async () => {
            setLoading(true);
            setError('');
            try {
                const res = await fetch(`http://localhost:8000/api/v1/entities/${entityId}/golden-record`);
                if (!res.ok) throw new Error('Failed to fetch entity details');
                const json = await res.json();
                setData(json);
            } catch (err) {
                setError('Could not load entity details.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [entityId]);

    if (loading) return <div className="text-sm text-gray-500">Loading details...</div>;
    if (error) return <div className="text-sm text-red-500">{error}</div>;
    if (!data) return null;

    const renderField = (label: string, fieldKey: string, value: any) => {
        const lineage = data.lineage_metadata?.[fieldKey];

        return (
            <div className="mb-2 group relative">
                <span className="font-semibold text-gray-700">{label}: </span>
                <span className="text-gray-900 border-b border-dotted border-gray-400 cursor-help">
                    {value !== null && value !== undefined ? value.toLocaleString() : 'N/A'}
                </span>

                {/* Tooltip */}
                {lineage && (
                    <div className="absolute left-0 bottom-full mb-2 w-64 p-2 bg-black text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                        <p><strong>Source:</strong> {lineage.source}</p>
                        <p><strong>Payload ID:</strong> {lineage.payload_id.substring(0, 8)}...</p>
                        <p><strong>Confidence:</strong> {(lineage.confidence * 100).toFixed(0)}%</p>
                        {lineage.file_name && <p className="truncate" title={lineage.file_name}><strong>File:</strong> {lineage.file_name}</p>}
                        {lineage.json_path && <p className="truncate" title={lineage.json_path}><strong>Path:</strong> {lineage.json_path}</p>}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="bg-white p-4 rounded shadow border border-gray-200">
            <h2 className="text-xl font-bold mb-4 border-b pb-2">Golden Record</h2>

            {renderField("Name", "name", data.name)}
            {renderField("Legal Name", "legal_name", data.legal_name)}
            {renderField("Jurisdiction", "jurisdiction_code", data.jurisdiction_code)}
            {renderField("Revenue (USD)", "revenue_usd", data.revenue_usd)}
            {renderField("Employees", "employee_count", data.employee_count)}

            <div className="mt-4 text-xs text-gray-400">
                * Hover over fields to see data lineage.
            </div>
        </div>
    );
}
