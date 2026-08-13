import { useState, useCallback, useEffect } from 'react';

const BASE_URL = 'http://127.0.0.1:5001';

export function useSimulation() {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [history, setHistory] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [config, setConfig] = useState(null);
  const [nodesStats, setNodesStats] = useState([]);
  const [logs, setLogs] = useState([{ time: new Date().toLocaleTimeString(), msg: 'Waiting for actions...', type: 'info' }]);
  const [isGraphInitialized, setIsGraphInitialized] = useState(false);

  const addLog = (msg, type = 'info') => {
    setLogs(prev => [...prev.slice(-49), { time: new Date().toLocaleTimeString(), msg, type }]);
  };

  const apiRequest = async (endpoint, method = 'GET', body = null) => {
    try {
      const options = { method, headers: {} };
      if (body) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
      }
      const res = await fetch(`${BASE_URL}${endpoint}`, options);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      throw err;
    }
  };

  const refreshMetrics = useCallback(async () => {
    try {
      const data = await apiRequest('/api/metrics');
      if (data.status !== 'error') setMetrics(data);
    } catch (e) {}
  }, []);

  const refreshHistory = useCallback(async () => {
    try {
      const data = await apiRequest('/api/history');
      if (data.status !== 'error') setHistory(data);
    } catch (e) {}
  }, []);

  const refreshGraph = useCallback(async () => {
    try {
      const data = await apiRequest('/api/graph/data');
      if (data.status !== 'error') {
        setGraphData({ nodes: data.nodes || [], edges: data.edges || [] });
      }
    } catch (e) {}
  }, []);

  const refreshNodesStats = useCallback(async () => {
    try {
      const data = await apiRequest('/api/nodes/stats');
      if (data.status !== 'error') {
        setNodesStats(data.nodes || []);
      }
    } catch (e) {}
  }, []);

  const initializeGraph = async (params) => {
    setLoading(true);
    try {
      const res = await apiRequest('/api/config', 'POST', params);
      const initRes = await apiRequest('/api/graph/initialize', 'POST');
      if (initRes.status === 'success') {
        addLog(`Graph ready - ${initRes.num_nodes} nodes, ${initRes.num_edges} edges`, 'success');
        setIsGraphInitialized(true);
        await Promise.all([refreshMetrics(), refreshHistory(), refreshGraph(), refreshNodesStats()]);
      } else {
        addLog(`Init failed: ${initRes.message}`, 'error');
      }
    } catch (e) {
      addLog('Failed to connect to backend', 'error');
    }
    setLoading(false);
  };

  const applyWeights = async (params) => {
    setLoading(true);
    try {
      const res = await apiRequest('/api/config', 'POST', params);
      if (res.status === 'success') {
        setConfig(params);
        addLog(`Config applied - α=${params.alpha} β=${params.beta} BW=${params.betweenness_weight} defectors=${params.defector_ratio}`, 'success');
      }
    } catch (e) {
      addLog('Failed to apply config', 'error');
    }
    setLoading(false);
  };

  const runSteps = async (steps) => {
    setLoading(true);
    try {
      const res = await apiRequest('/api/evolution/run', 'POST', { steps });
      if (res.status === 'success') {
        addLog(`Completed ${steps} steps`, 'success');
        await Promise.all([refreshMetrics(), refreshHistory(), refreshGraph(), refreshNodesStats()]);
      }
    } catch (e) {
      addLog('Simulation failed', 'error');
    }
    setLoading(false);
  };

  const toggleNode = async (id) => {
    try {
      const res = await apiRequest(`/api/node/${id}/toggle`, 'POST');
      if (res.status === 'success') {
        addLog(`Node #${id} toggled ${res.is_offline ? 'offline' : 'online'} manually.`, 'success');
        await Promise.all([refreshMetrics(), refreshGraph(), refreshNodesStats()]);
      }
      return res;
    } catch (e) {
      addLog('Toggle request failed', 'error');
      throw e;
    }
  };

  const getNodeInfo = async (id) => {
    return await apiRequest(`/api/node/${id}`);
  };

  return {
    metrics, history, graphData, nodesStats, config, logs, isGraphInitialized, loading,
    initializeGraph, applyWeights, runSteps, refreshMetrics, refreshGraph, toggleNode, getNodeInfo
  };
}
