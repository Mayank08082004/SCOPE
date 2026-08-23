import React, { useState, useEffect } from 'react';
import { NetworkGraph } from '../components/dashboard/NetworkGraph';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Info, Activity, AlertTriangle, Cpu, Power, ShieldAlert, Send, Clock, CheckCircle2, XCircle } from 'lucide-react';

export default function NetworkDashboard() {
  const [networkState, setNetworkState] = useState(null);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [isCommanding, setIsCommanding] = useState(false);
  
  // File Transfer State
  const [transferSource, setTransferSource] = useState('');
  const [transferTarget, setTransferTarget] = useState('');
  const [transferStatus, setTransferStatus] = useState(null);
  const [isTransferring, setIsTransferring] = useState(false);

  useEffect(() => {
    const fetchState = async () => {
      try {
        const res = await fetch('http://localhost:5002/api/network/state');
        const data = await res.json();
        setNetworkState(data);
      } catch (err) {
        console.error("Tracker offline");
      }
    };
    
    fetchState();
    const interval = setInterval(fetchState, 2000);
    return () => clearInterval(interval);
  }, []);

  const sendCommand = async (action) => {
    if (!selectedNodeId) return;
    setIsCommanding(true);
    try {
      await fetch('http://localhost:5002/api/tracker/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node_id: selectedNodeId, action })
      });
      if (action === 'KILL') setSelectedNodeId(null);
    } catch (err) {
      console.error("Failed to send command", err);
    }
    setIsCommanding(false);
  };

  const startTransfer = async () => {
    if (!transferSource || !transferTarget) return;
    setIsTransferring(true);
    setTransferStatus({ status: 'IN_PROGRESS', path: [], reason: '' });
    
    try {
      const res = await fetch('http://localhost:5002/api/tracker/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_id: transferSource, target_id: transferTarget })
      });
      const { transfer_id } = await res.json();
      
      // Poll for result
      let isPolling = true;
      const poll = setInterval(async () => {
        if (!isPolling) return;
        
        try {
          const statusRes = await fetch(`http://localhost:5002/api/tracker/transfer_status/${transfer_id}`);
          const statusData = await statusRes.json();
          
          if (!isPolling) return; // double check after await
          
          if (statusData.status !== 'IN_PROGRESS') {
            isPolling = false;
            clearInterval(poll);
            setTransferStatus(statusData);
            setIsTransferring(false);
          } else {
            setTransferStatus(statusData);
          }
        } catch (err) {
          // ignore fetch errors during polling
        }
      }, 500);
      
      // Safety timeout
      setTimeout(() => { 
        if (isPolling) {
          isPolling = false;
          clearInterval(poll); 
          setIsTransferring(false); 
          setTransferStatus({ status: 'FAILED_TIMEOUT', path: [], reason: 'Transfer stuck in infinite routing loop or timed out' });
        }
      }, 10000);
      
    } catch (err) {
      console.error("Transfer failed", err);
      setTransferStatus({ status: 'FAILED', reason: 'Network error', path: [] });
      setIsTransferring(false);
    }
  };

  // Format data for NetworkGraph
  const nodes = networkState ? Object.keys(networkState.nodes).map(id => ({
    id,
    group: networkState.nodes[id].is_defector ? 2 : 1, // Defectors in red
    degree: networkState.edges[id]?.length || 0,
    ...networkState.nodes[id]
  })) : [];
  
  const edges = [];
  if (networkState) {
    Object.keys(networkState.edges).forEach(source => {
      networkState.edges[source].forEach(target => {
        edges.push({ source, target });
      });
    });
  }

  // Calculate Top Hubs
  const topHubs = [...nodes].sort((a, b) => b.degree - a.degree).slice(0, 5);

  const selectedNode = selectedNodeId && networkState?.nodes[selectedNodeId] 
    ? { id: selectedNodeId, ...networkState.nodes[selectedNodeId], degree: networkState.edges[selectedNodeId]?.length || 0 } 
    : null;

  return (
    <div className="min-h-screen p-4 md:p-8 pb-24 bg-[#fbfbfd] dark:bg-black font-sans">
      <div className="max-w-[1600px] mx-auto space-y-8">
        
        {/* Apple-style minimalist header */}
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center pb-6">
          <div>
            <h1 className="text-4xl font-semibold tracking-tight text-slate-900 dark:text-white">C2 Dashboard</h1>
            <p className="text-base text-slate-500 dark:text-slate-400 mt-2 flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-500" /> Live TCP Socket Network
            </p>
          </div>
          <div className="flex gap-6 mt-4 sm:mt-0">
             <div className="flex flex-col items-center group relative cursor-help">
                 <span className="text-xs text-slate-500 font-medium uppercase tracking-widest mb-1 border-b border-dashed border-slate-400">Dropped</span>
                 <span className="text-2xl text-orange-500 font-semibold">{networkState?.telemetry?.total_packets_dropped || 0}</span>
                 <div className="absolute top-full mt-2 w-48 p-2 bg-slate-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
                    Background dummy packets dropped by Defectors (Black Hole routing).
                 </div>
             </div>
             <div className="flex flex-col items-center group relative cursor-help">
                 <span className="text-xs text-slate-500 font-medium uppercase tracking-widest mb-1 border-b border-dashed border-slate-400">Transmitted</span>
                 <span className="text-2xl text-blue-500 font-semibold">{networkState?.telemetry?.total_packets_sent || 0}</span>
                 <div className="absolute top-full right-0 mt-2 w-48 p-2 bg-slate-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
                    Background dummy packets successfully relayed by Honest nodes.
                 </div>
             </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Left Panel */}
          <div className="lg:col-span-1 space-y-8 flex flex-col">
            
            <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(255,255,255,0.02)] rounded-3xl bg-white/70 dark:bg-slate-900/50 backdrop-blur-xl">
              <CardHeader className="pb-2 pt-6 px-6">
                <CardTitle className="text-lg font-medium flex items-center gap-2 text-slate-800 dark:text-slate-200">
                  <Info className="w-5 h-5 text-blue-500" /> Legend
                </CardTitle>
              </CardHeader>
              <CardContent className="px-6 pb-6 space-y-5 text-sm text-slate-600 dark:text-slate-400">
                <div className="flex items-start gap-4">
                  <div className="w-4 h-4 mt-0.5 rounded-full bg-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.6)] shrink-0"></div>
                  <span className="leading-relaxed"><strong className="text-slate-900 dark:text-white font-semibold">Honest Node</strong><br/>Routes traffic efficiently using Gradient Ascent.</span>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-4 h-4 mt-0.5 rounded-full bg-orange-500 shadow-[0_0_12px_rgba(249,115,22,0.6)] shrink-0"></div>
                  <span className="leading-relaxed"><strong className="text-slate-900 dark:text-white font-semibold">Defector</strong><br/>Fabricates degree to attract connections and drops data.</span>
                </div>
              </CardContent>
            </Card>

            <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(255,255,255,0.02)] rounded-3xl bg-white/70 dark:bg-slate-900/50 backdrop-blur-xl flex-grow">
              <CardHeader className="pb-2 pt-6 px-6">
                <CardTitle className="text-lg font-medium flex items-center gap-2 text-slate-800 dark:text-slate-200">
                  <Cpu className="w-5 h-5 text-blue-500" /> Super Hubs
                </CardTitle>
              </CardHeader>
              <CardContent className="px-6 pb-6">
                <div className="space-y-3">
                  {topHubs.length > 0 ? topHubs.map((node, i) => (
                    <div key={node.id} className="flex justify-between items-center p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer border border-slate-100 dark:border-slate-800" onClick={() => setSelectedNodeId(node.id)}>
                      <div className="flex items-center gap-3">
                        <span className="text-slate-400 font-medium text-sm">{i+1}</span>
                        <span className={`font-medium ${node.is_defector ? 'text-orange-500' : 'text-blue-500'}`}>{node.id}</span>
                      </div>
                      <span className="bg-white dark:bg-slate-900 px-3 py-1 rounded-full text-xs font-semibold shadow-sm text-slate-600 dark:text-slate-300">Deg: {node.degree}</span>
                    </div>
                  )) : (
                    <p className="text-sm text-slate-500">Waiting for topology...</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Center Panel: Network Graph */}
          <div className="lg:col-span-2 flex flex-col gap-6">
              {/* Fix the graph container height and styling */}
              <div className="h-[500px] border-none rounded-3xl overflow-hidden bg-slate-50 dark:bg-slate-900 shadow-[inset_0_2px_20px_rgba(0,0,0,0.02)] dark:shadow-[inset_0_2px_20px_rgba(0,0,0,0.2)] relative">
                 <div className="absolute bottom-6 left-6 z-10 flex gap-4 bg-white/80 dark:bg-black/60 backdrop-blur-md px-4 py-2 rounded-full border border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-600 dark:text-slate-300 shadow-sm">
                   <span>🟢 Active Nodes: {nodes.length}</span>
                   <span className="border-l border-slate-300 dark:border-slate-700 pl-4">🔗 TCP Connections (Edges): {edges.length / 2}</span>
                 </div>
                 {/* Provide fixed 100% height to NetworkGraph parent so it fills the 500px container */}
                 <div className="w-full h-full">
                    <NetworkGraph nodes={nodes} edges={edges} onNodeClick={setSelectedNodeId} />
                 </div>
              </div>

              {/* File Transfer Terminal */}
              <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(255,255,255,0.02)] rounded-3xl bg-white/70 dark:bg-slate-900/50 backdrop-blur-xl">
                <CardHeader className="pb-2 pt-6 px-6">
                  <CardTitle className="text-lg font-medium flex items-center gap-2 text-slate-800 dark:text-slate-200">
                    <Send className="w-5 h-5 text-blue-500" /> P2P File Transfer Simulator
                  </CardTitle>
                  <p className="text-sm text-slate-500 mt-1">
                    Simulates Gradient Ascent Routing through live TCP sockets. <br/>
                    <span className="text-orange-500/80 font-medium italic">Note: Defectors inflate their degree to act as "Black Holes", tricking the algorithm into routing packets straight to them where they are silently dropped!</span>
                  </p>
                </CardHeader>
                <CardContent className="px-6 pb-6 space-y-6">
                  
                  <div className="flex flex-col sm:flex-row gap-4 items-end">
                    <div className="flex-1 space-y-2 w-full">
                      <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Source Node</label>
                      <select 
                        value={transferSource} onChange={(e)=>setTransferSource(e.target.value)}
                        className="w-full p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none shadow-inner focus:ring-2 focus:ring-blue-500 outline-none text-sm text-slate-700 dark:text-slate-200 appearance-none"
                      >
                        <option value="">Select source...</option>
                        {nodes.map(n => <option key={n.id} value={n.id}>{n.id}</option>)}
                      </select>
                    </div>
                    <div className="flex-1 space-y-2 w-full">
                      <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Target Node</label>
                      <select 
                        value={transferTarget} onChange={(e)=>setTransferTarget(e.target.value)}
                        className="w-full p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border-none shadow-inner focus:ring-2 focus:ring-blue-500 outline-none text-sm text-slate-700 dark:text-slate-200 appearance-none"
                      >
                        <option value="">Select target...</option>
                        {nodes.map(n => <option key={n.id} value={n.id}>{n.id}</option>)}
                      </select>
                    </div>
                    <button 
                      onClick={startTransfer}
                      disabled={isTransferring || !transferSource || !transferTarget}
                      className="w-full sm:w-auto px-6 py-3 rounded-xl bg-blue-500 hover:bg-blue-600 text-white font-semibold text-sm transition-colors disabled:opacity-50 shadow-md shadow-blue-500/20"
                    >
                      {isTransferring ? 'Routing...' : 'Execute Transfer'}
                    </button>
                  </div>

                  {/* Transfer Status Trace */}
                  {transferStatus && (
                    <div className={`p-5 rounded-2xl border ${
                      transferStatus.status === 'SUCCESS' ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800/50' : 
                      transferStatus.status === 'IN_PROGRESS' ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800/50' :
                      'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800/50'
                    }`}>
                      <div className="flex items-center gap-3 mb-3">
                        {transferStatus.status === 'SUCCESS' && <CheckCircle2 className="w-5 h-5 text-green-500" />}
                        {transferStatus.status === 'IN_PROGRESS' && <Clock className="w-5 h-5 text-blue-500 animate-spin" />}
                        {['DROPPED_BY_DEFECTOR', 'FAILED_DEADEND', 'FAILED_TTL', 'FAILED'].includes(transferStatus.status) && <XCircle className="w-5 h-5 text-orange-500" />}
                        <span className="font-semibold text-slate-800 dark:text-slate-200">
                          Status: {transferStatus.status.replace(/_/g, ' ')}
                        </span>
                      </div>
                      
                      {transferStatus.reason && (
                        <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">{transferStatus.reason}</p>
                      )}
                      
                      {transferStatus.path && transferStatus.path.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Route Trace ({transferStatus.path.length} hops)</p>
                          <div className="flex flex-wrap gap-2 items-center text-sm font-mono">
                            {transferStatus.path.map((step, idx) => (
                              <React.Fragment key={idx}>
                                <span className={`px-2 py-1 rounded-lg ${step === transferSource ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' : step === transferTarget ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300'}`}>
                                  {step}
                                </span>
                                {idx < transferStatus.path.length - 1 && <span className="text-slate-400">→</span>}
                              </React.Fragment>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                </CardContent>
              </Card>

          </div>

          {/* Right Panel: C2 Inspector */}
          <div className="lg:col-span-1">
            <Card className="border-none shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(255,255,255,0.02)] rounded-3xl bg-white/70 dark:bg-slate-900/50 backdrop-blur-xl h-full">
                <CardHeader className="pb-2 pt-6 px-6">
                  <CardTitle className="text-lg font-medium flex items-center gap-2 text-slate-800 dark:text-slate-200">
                    <ShieldAlert className="w-5 h-5 text-blue-500" /> Inspector
                  </CardTitle>
                </CardHeader>
                <CardContent className="px-6 pb-6 space-y-6">
                    {selectedNode ? (
                        <>
                          <div className="space-y-3 font-mono text-sm text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-800">
                              <p className="flex justify-between items-center"><span className="text-slate-400">ID</span> <strong className="text-slate-900 dark:text-white text-base">{selectedNode.id}</strong></p>
                              <p className="flex justify-between items-center"><span className="text-slate-400">Internal IP</span> <strong>{selectedNode.ip}:{selectedNode.port}</strong></p>
                              <p className="flex justify-between items-center"><span className="text-slate-400">TCP Degree</span> <strong>{selectedNode.degree}</strong></p>
                              <p className="flex justify-between items-center"><span className="text-slate-400">Status</span> 
                                <span className={`px-3 py-1 rounded-full text-xs font-bold ${selectedNode.is_defector ? 'bg-orange-100 text-orange-600 dark:bg-orange-500/20 dark:text-orange-400' : 'bg-blue-100 text-blue-600 dark:bg-blue-500/20 dark:text-blue-400'}`}>
                                  {selectedNode.is_defector ? 'DEFECTOR' : 'HONEST'}
                                </span>
                              </p>
                          </div>

                          <div className="space-y-3">
                            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 ml-1">Terminal Actions</h3>
                            
                            <button 
                              onClick={() => sendCommand('TOGGLE_DEFECTOR')}
                              disabled={isCommanding}
                              className="w-full py-3 px-4 rounded-2xl bg-orange-50 hover:bg-orange-100 dark:bg-orange-500/10 dark:hover:bg-orange-500/20 text-orange-600 dark:text-orange-400 text-sm font-semibold transition-colors flex items-center justify-center gap-2"
                            >
                              <AlertTriangle className="w-4 h-4" /> 
                              {selectedNode.is_defector ? 'Cure Node (Make Honest)' : 'Infect Node (Defect)'}
                            </button>

                            <button 
                              onClick={() => sendCommand('KILL')}
                              disabled={isCommanding}
                              className="w-full py-3 px-4 rounded-2xl bg-red-50 hover:bg-red-100 dark:bg-red-500/10 dark:hover:bg-red-500/20 text-red-600 dark:text-red-400 text-sm font-semibold transition-colors flex items-center justify-center gap-2"
                            >
                              <Power className="w-4 h-4" /> 
                              Terminate Instance
                            </button>
                          </div>
                          <div className="space-y-3 pt-6 border-t border-slate-200 dark:border-slate-800">
                            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 ml-1">Dynamic Scaling</h3>
                            <div className="bg-slate-900 rounded-xl p-3 shadow-inner">
                              <p className="text-xs text-slate-400 mb-2">Run this in your host terminal to scale up/down instantly without dropping the network:</p>
                              <code className="text-[10px] text-green-400 font-mono break-all selection:bg-green-900">
                                docker compose up -d --scale node=65 --scale defector=10 --no-recreate
                              </code>
                            </div>
                          </div>
                        </>
                    ) : (
                        <div className="h-64 flex flex-col items-center justify-center text-center opacity-40">
                          <Cpu className="w-12 h-12 mb-4 text-slate-400" />
                          <p className="text-sm text-slate-500">Select a node from the topology<br/>to open C2 terminal</p>
                        </div>
                    )}
                    
                    {!selectedNode && (
                      <div className="space-y-3 pt-4">
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 ml-1">Dynamic Scaling</h3>
                        <div className="bg-slate-900 rounded-xl p-3 shadow-inner">
                          <p className="text-xs text-slate-400 mb-2">Run this in your host terminal to scale up/down instantly without dropping the network:</p>
                          <code className="text-[10px] text-green-400 font-mono break-all selection:bg-green-900">
                            docker compose up -d --scale node=65 --scale defector=10 --no-recreate
                          </code>
                        </div>
                      </div>
                    )}
                </CardContent>
            </Card>
          </div>
        </div>

      </div>
    </div>
  );
}
