import React, { useState, useEffect } from 'react';
import { useSimulation } from '../hooks/useSimulation';
import { MetricsDisplay } from '../components/dashboard/MetricsDisplay';
import { ControlPanel } from '../components/dashboard/ControlPanel';
import { NetworkGraph } from '../components/dashboard/NetworkGraph';
import { NodeInspector } from '../components/dashboard/NodeInspector';
import { MetricsCharts } from '../components/dashboard/MetricsCharts';
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function SimulationDashboard() {
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
    <div className="min-h-screen p-4 md:p-8 pb-24 bg-[#fbfbfd] dark:bg-black font-sans">
      <div className="max-w-[1600px] mx-auto space-y-8">
        
        {/* Apple-style minimalist header */}
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-6">
          <div>
            <h1 className="text-4xl font-semibold tracking-tight text-slate-900 dark:text-white">Simulation Engine</h1>
            <p className="text-base text-slate-500 dark:text-slate-400 mt-2">
              Phase 2 Mathematical Simulation Model
            </p>
          </div>
          <div className="flex gap-4 mt-4 sm:mt-0">
             <div className="flex flex-col items-center justify-center border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2 bg-white/50 dark:bg-slate-900/50 backdrop-blur-md">
                 <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-0.5">Status</span>
                 <span className={`text-sm font-semibold ${isGraphInitialized ? 'text-green-500' : 'text-orange-500'}`}>
                    {isGraphInitialized ? 'Online' : 'Offline'}
                 </span>
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="h-[500px] rounded-3xl overflow-hidden bg-slate-50 dark:bg-slate-900 shadow-[inset_0_2px_20px_rgba(0,0,0,0.02)] dark:shadow-[inset_0_2px_20px_rgba(0,0,0,0.2)]">
               <div className="w-full h-full">
                  <NetworkGraph nodes={graphData.nodes} edges={graphData.edges} onNodeClick={setSelectedNodeId} />
               </div>
            </div>
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

