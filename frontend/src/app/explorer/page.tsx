'use client';

import React, { useEffect, useState } from 'react';

interface Module {
    id: string;
    name: string;
    has_dictionary: boolean;
    has_sample: boolean;
    has_pdf: boolean;
}

interface DictionaryItem {
    fieldName: string;
    description: string;
    dnbCode?: string;
    type?: string;
    length?: string;
}

export default function ExplorerPage() {
    const [modules, setModules] = useState<Module[]>([]);
    const [selectedModule, setSelectedModule] = useState<Module | null>(null);
    const [activeTab, setActiveTab] = useState<'dictionary' | 'sample' | 'docs'>('dictionary');

    const [dictionary, setDictionary] = useState<DictionaryItem[]>([]);
    const [sample, setSample] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetch('http://localhost:8000/api/v1/references/modules')
            .then(res => res.json())
            .then(data => {
                setModules(data);
                if (data.length > 0) setSelectedModule(data[0]);
            })
            .catch(err => console.error("Failed to load modules", err));
    }, []);

    useEffect(() => {
        if (!selectedModule) return;

        setLoading(true);
        // Fetch Dictionary
        const fetchDict = fetch(`http://localhost:8000/api/v1/references/${selectedModule.id}/dictionary`)
            .then(res => res.json())
            .catch(() => []);

        // Fetch Sample
        const fetchSample = fetch(`http://localhost:8000/api/v1/references/${selectedModule.id}/sample`)
            .then(res => res.json())
            .catch(() => null);

        Promise.all([fetchDict, fetchSample]).then(([dictData, sampleData]) => {
            // Normalize dictionary keys if needed (pandas might leave them uppercase/messy)
            // We assume the API returns list of dicts. We try to find best matching keys.
            const normalizedDict = dictData.map((item: any) => ({
                fieldName: item['Field Name'] || item['Element Name'] || item['Name'] || 'Unknown',
                description: item['Description'] || item['Definition'] || '',
                dnbCode: item['D&B Code'] || item['Dnb Code'] || '',
                type: item['Data Type'] || item['Type'] || '',
                length: item['Length'] || ''
            }));

            setDictionary(normalizedDict);
            setSample(sampleData);
            setLoading(false);
        });
    }, [selectedModule]);

    return (
        <div className="flex h-screen bg-gray-50">
            {/* Sidebar */}
            <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
                <div className="p-4 border-b border-gray-200">
                    <h2 className="font-bold text-lg text-gray-800">D&B API Explorer</h2>
                </div>
                <ul>
                    {modules.map(mod => (
                        <li
                            key={mod.id}
                            className={`p-3 cursor-pointer hover:bg-gray-100 ${selectedModule?.id === mod.id ? 'bg-blue-50 border-r-4 border-blue-500' : ''}`}
                            onClick={() => setSelectedModule(mod)}
                        >
                            <div className="font-medium text-sm text-gray-700 break-words">{mod.name}</div>
                            <div className="text-xs text-gray-500 mt-1 flex gap-1">
                                {mod.has_dictionary && <span className="bg-green-100 text-green-800 px-1 rounded">Dict</span>}
                                {mod.has_sample && <span className="bg-purple-100 text-purple-800 px-1 rounded">JSON</span>}
                            </div>
                        </li>
                    ))}
                </ul>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col h-full overflow-hidden">
                {selectedModule ? (
                    <>
                        {/* Header */}
                        <div className="bg-white border-b border-gray-200 p-4">
                            <h1 className="text-2xl font-bold text-gray-800">{selectedModule.name}</h1>
                            <div className="flex mt-4 space-x-4 border-b border-gray-200">
                                <button
                                    className={`pb-2 px-1 ${activeTab === 'dictionary' ? 'border-b-2 border-blue-500 text-blue-600 font-semibold' : 'text-gray-500 hover:text-gray-700'}`}
                                    onClick={() => setActiveTab('dictionary')}
                                    disabled={!selectedModule.has_dictionary}
                                >
                                    Data Dictionary
                                </button>
                                <button
                                    className={`pb-2 px-1 ${activeTab === 'sample' ? 'border-b-2 border-blue-500 text-blue-600 font-semibold' : 'text-gray-500 hover:text-gray-700'}`}
                                    onClick={() => setActiveTab('sample')}
                                    disabled={!selectedModule.has_sample}
                                >
                                    Example JSON
                                </button>
                            </div>
                        </div>

                        {/* Content Area */}
                        <div className="flex-1 overflow-auto p-6">
                            {loading ? (
                                <div className="flex items-center justify-center h-full text-gray-400">Loading module data...</div>
                            ) : (
                                <>
                                    {activeTab === 'dictionary' && (
                                        <div className="bg-white shadow rounded-lg overflow-hidden">
                                            <table className="min-w-full divide-y divide-gray-200">
                                                <thead className="bg-gray-50">
                                                    <tr>
                                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Field Name</th>
                                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">D&B Code</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="bg-white divide-y divide-gray-200 text-sm">
                                                    {dictionary.length > 0 ? (
                                                        dictionary.map((row, idx) => (
                                                            <tr key={idx} className="hover:bg-gray-50">
                                                                <td className="px-6 py-4 font-medium text-gray-900">{row.fieldName}</td>
                                                                <td className="px-6 py-4 text-gray-500">{row.type} {row.length ? `(${row.length})` : ''}</td>
                                                                <td className="px-6 py-4 text-gray-500 max-w-xl break-words">{row.description}</td>
                                                                <td className="px-6 py-4 text-gray-500 font-mono">{row.dnbCode}</td>
                                                            </tr>
                                                        ))
                                                    ) : (
                                                        <tr>
                                                            <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                                                                No glossary definitions found in the Excel file.
                                                            </td>
                                                        </tr>
                                                    )}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}

                                    {activeTab === 'sample' && (
                                        <div className="bg-gray-900 text-gray-100 p-4 rounded-lg shadow font-mono text-sm overflow-auto h-full">
                                            <pre>{JSON.stringify(sample, null, 2)}</pre>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex items-center justify-center h-full text-gray-400">
                        Select a module from the sidebar to explore.
                    </div>
                )}
            </div>
        </div>
    );
}
