const API_BASE_URL = 'http://localhost:8000/api/v1';

export async function fetchEntityGraph(entityId: string) {
    const response = await fetch(`${API_BASE_URL}/graph/${entityId}`);
    if (!response.ok) {
        throw new Error('Failed to fetch graph data');
    }
    return response.json();
}
