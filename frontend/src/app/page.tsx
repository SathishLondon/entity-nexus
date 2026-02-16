'use client';

import { useState } from 'react';
import GraphViz from '@/components/GraphViz';
import { fetchEntityGraph } from '@/lib/api';
import { Node, Edge } from '@xyflow/react';
import EntityDetails from '@/components/EntityDetails';

export default function Home() {
  const [entityId, setEntityId] = useState('804735132'); // Default to sample DUNS
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchEntityGraph(entityId);
      setNodes(data.nodes || []);
      setEdges(data.edges || []);
    } catch (err) {
      setError('Failed to fetch graph data. Is the backend running?');
      console.error(err);

      // Fallback mock data for demo purposes if backend is down
      setNodes([
        { id: '1', position: { x: 0, y: 0 }, data: { label: 'Gorman Mfg' }, type: 'input' },
        { id: '2', position: { x: 0, y: 100 }, data: { label: 'Subsidiary A' } },
        { id: '3', position: { x: 200, y: 0 }, data: { label: 'Subsidiary B' } },
      ]);
      setEdges([
        { id: 'e1-2', source: '1', target: '2', label: 'OWNS' },
        { id: 'e1-3', source: '1', target: '3', label: 'PARTNER' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8 font-sans bg-gray-50">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-gray-900">Entity Nexus</h1>
        <p className="text-gray-600">Enterprise Entity Resolution & Graph Explorer</p>
      </header>

      <div className="flex gap-4 mb-8">
        <input
          type="text"
          value={entityId}
          onChange={(e) => setEntityId(e.target.value)}
          placeholder="Enter Entity ID / DUNS"
          className="border p-2 rounded w-64 text-black"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-blue-300"
        >
          {loading ? 'Loading...' : 'Analyze'}
        </button>
      </div>

      {error && (
        <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
          <p>{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Golden Record Details */}
        <div className="lg:col-span-1">
          <EntityDetails entityId={entityId} />
        </div>

        {/* Right Column: Interactive Graph */}
        <div className="lg:col-span-2 border rounded-lg shadow-lg overflow-hidden bg-white h-[600px]">
          <GraphViz initialNodes={nodes} initialEdges={edges} />
        </div>
      </div>
    </div>
  );
}
