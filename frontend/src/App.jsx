import React, { useState, useEffect } from 'react';
import { useSimulation } from './hooks/useSimulation';
import { MetricsDisplay } from './components/dashboard/MetricsDisplay';
import { ControlPanel } from './components/dashboard/ControlPanel';
import { NetworkGraph } from './components/dashboard/NetworkGraph';
import { NodeInspector } from './components/dashboard/NodeInspector';
import { MetricsCharts } from './components/dashboard/MetricsCharts';
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function App() {
  const { 
    metrics, history, graphData, nodesStats, logs, isGraphInitialized, loading,
    initializeGraph, applyWeights, runSteps, refreshMetrics, toggleNode, getNodeInfo 
  } = useSimulation();

  const [selectedNodeId, setSelectedNodeId] = useState(null);

  // Auto scroll logs
  useEffect(() => {
    const el = document.getElementById('logContainer');
    if (el) el.scrollTop = el.scrollHeight;
  }, [logs]);

  // Handle dark mode toggle
  const [isDark, setIsDark] = useState(true);
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  return (
    <div className="min-h-screen p-4 md:p-6 pb-20">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-border pb-4 gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">SCOPE <span className="text-muted-foreground font-normal">— P2P Network Simulator</span></h1>
            <p className="text-sm text-muted-foreground mt-1">Self-Organizing Peer-to-peer via OODA Loop Agents · Flask API on localhost:5001</p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => setIsDark(!isDark)}
              className="text-xs font-medium border border-border px-3 py-1.5 rounded-md hover:bg-secondary transition-colors"
            >
              {isDark ? 'Light Mode' : 'Dark Mode'}
            </button>
            <div className="flex items-center gap-2 border border-border px-3 py-1.5 rounded-md">
              <div className={`w-2 h-2 rounded-full ${isGraphInitialized ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
              <span className="text-xs font-medium">{isGraphInitialized ? 'Ready' : 'Waiting...'}</span>
            </div>
          </div>
        </header>

        <MetricsDisplay metrics={metrics} steps={history?.steps} />

        <ControlPanel 
          initializeGraph={initializeGraph}
          applyWeights={applyWeights}
          runSteps={runSteps}
          refreshMetrics={refreshMetrics}
        />

        {/* Network & Inspector row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <NetworkGraph nodes={graphData.nodes} edges={graphData.edges} onNodeClick={setSelectedNodeId} />
          </div>
          <div className="lg:col-span-1">
            <NodeInspector selectedNodeId={selectedNodeId} getNodeInfo={getNodeInfo} toggleNode={toggleNode} />
          </div>
        </div>

        {isGraphInitialized && (
          <div className="pt-4">
            <MetricsCharts history={history} graphData={graphData} nodesStats={nodesStats} />
          </div>
        )}

        {/* Activity Log */}
        <Card>
          <CardContent className="p-0">
            <div className="bg-[#1e1e1e] rounded-lg border border-border overflow-hidden">
              <div className="bg-[#2d2d2d] border-b border-[#404040] px-4 py-2 text-xs font-semibold text-[#a0a0a0] uppercase tracking-wider">
                Activity Log
              </div>
              <div id="logContainer" className="p-4 h-[200px] overflow-y-auto font-mono text-sm">
                {logs.map((log, i) => (
                  <div key={i} className="mb-1">
                    <span className="text-[#6e7681] mr-3">{log.time}</span>
                    <span className={log.type === 'error' ? 'text-red-400' : log.type === 'success' ? 'text-[#7ee787]' : 'text-[#c9d1d9]'}>
                      {log.msg}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}

export default App;
