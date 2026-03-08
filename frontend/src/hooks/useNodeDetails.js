import { useState, useCallback } from 'react';
import { getNodeDetails } from '../api';

/**
 * Hook for lazy loading node details
 * Only fetches full node data when requested
 */
export function useNodeDetails(jobId) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchNodeDetails = useCallback(async (nodeId) => {
    if (!jobId || !nodeId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const details = await getNodeDetails(jobId, nodeId);
      setSelectedNode(details);
    } catch (err) {
      setError(err.message || 'Failed to fetch node details');
      console.error('Failed to fetch node details:', err);
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  const clearSelection = useCallback(() => {
    setSelectedNode(null);
    setError(null);
  }, []);

  return {
    selectedNode,
    loading,
    error,
    fetchNodeDetails,
    clearSelection
  };
}
