import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export function NodeInspector({ selectedNodeId, getNodeInfo, toggleNode }) {
  const [nodeData, setNodeData] = useState(null);
  const [inputId, setInputId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (selectedNodeId !== null) {
      setInputId(selectedNodeId.toString());
      fetchNode(selectedNodeId);
    }
  }, [selectedNodeId]);

  const fetchNode = async (id) => {
    setLoading(true);
    setError('');
    try {
      const data = await getNodeInfo(id);
      if (data.status === 'error') {
        setError(data.message);
        setNodeData(null);
      } else {
        setNodeData(data);
      }
    } catch (err) {
      setError('API Unreachable');
      setNodeData(null);
    }
    setLoading(false);
  };

  const handleInspect = () => {
    if (inputId.trim()) {
      fetchNode(parseInt(inputId, 10));
    }
  };

  const handleToggle = async () => {
    if (nodeData) {
      await toggleNode(nodeData.id);
      fetchNode(nodeData.id);
    }
  };

  return (
    <Card className="col-span-2 lg:col-span-1 flex flex-col">
      <CardHeader>
        <CardTitle>Node Inspector</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-4">
        <div className="flex gap-2">
          <Input 
            placeholder="Node ID..." 
            value={inputId} 
            onChange={e => setInputId(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleInspect()}
          />
          <Button onClick={handleInspect} variant="secondary">Inspect</Button>
        </div>

        {error && <div className="text-destructive text-sm font-medium">{error}</div>}

        {!nodeData && !error && !loading && (
          <div className="flex-1 rounded-md border border-dashed border-border flex items-center justify-center p-6 text-muted-foreground text-sm text-center">
            Initialize the graph, then enter a node ID or click a node on the canvas.
          </div>
        )}

        {nodeData && (
          <div className="flex-1 rounded-md bg-secondary/30 p-4 space-y-3 text-sm">
            <div className="flex justify-between items-center border-b border-border pb-2">
              <span className="text-muted-foreground font-medium">Node ID</span>
              <span className="font-bold">#{nodeData.id}</span>
            </div>
            <div className="flex justify-between items-center border-b border-border pb-2">
              <span className="text-muted-foreground font-medium">Status</span>
              <div className="flex gap-2">
                {nodeData.is_defector && (
                  <Badge className="bg-orange-600 hover:bg-orange-700">Defector</Badge>
                )}
                {nodeData.is_offline ? (
                  <Badge variant="destructive">Offline</Badge>
                ) : (
                  <Badge className="bg-green-600 hover:bg-green-700">Online</Badge>
                )}
              </div>
            </div>
            <div className="flex justify-between items-center border-b border-border pb-2">
              <span className="text-muted-foreground font-medium">Degree</span>
              <span className="font-medium">{nodeData.degree} connections</span>
            </div>
            <div className="flex justify-between items-center border-b border-border pb-2">
              <span className="text-muted-foreground font-medium">Bandwidth</span>
              <span className="font-medium">{nodeData.bandwidth} Mbps</span>
            </div>
            <div className="flex justify-between items-center border-b border-border pb-2">
              <span className="text-muted-foreground font-medium">Memory size</span>
              <span className="font-medium">{nodeData.memory_size} known nodes</span>
            </div>
            
            <div className="pt-4">
              <Button 
                onClick={handleToggle}
                className="w-full" 
                variant={nodeData.is_offline ? "default" : "destructive"}
              >
                {nodeData.is_offline ? 'Wake Up Node' : 'Kill Node'}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
