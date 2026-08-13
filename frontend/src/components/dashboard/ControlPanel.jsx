import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";

export function ControlPanel({ initializeGraph, applyWeights, runSteps, refreshMetrics, config }) {
  const [initParams, setInitParams] = useState({ nodes: 100, degree: 4, steps: 10 });
  
  const [weightParams, setWeightParams] = useState({
    alpha: 2,
    beta: 0.6,
    gamma: 1,
    betweenness_weight: 0.5,
    query_ttl: 20,
    num_search_queries: 500,
    churn_enabled: false,
    churn_rate: 0.1,
    churn_interval: 5,
    defector_ratio: 0.1
  });

  const handleInitParamsChange = (e) => {
    setInitParams({ ...initParams, [e.target.name]: Number(e.target.value) });
  };

  const handleWeightParamsChange = (e) => {
    const { name, value, type, checked } = e.target;
    setWeightParams({ 
      ...weightParams, 
      [name]: type === 'checkbox' ? checked : Number(value) 
    });
  };

  return (
    <Card className="mb-6">
      <CardHeader className="pb-3 border-b border-border/50">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
          <CardTitle className="text-lg">Configuration & Control</CardTitle>
          <div className="flex gap-2">
            <Button onClick={() => initializeGraph(initParams)} variant="default">Initialize graph</Button>
            <Button onClick={() => runSteps(1)} variant="secondary">Single step</Button>
            <Button onClick={() => runSteps(initParams.steps)} variant="secondary">Run steps</Button>
            <Button onClick={refreshMetrics} variant="outline">Refresh metrics</Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-6">
        <div className="flex flex-wrap gap-6 mb-8">
          <div className="flex flex-col gap-1.5 w-24">
            <label className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Nodes</label>
            <Input type="number" name="nodes" value={initParams.nodes} onChange={handleInitParamsChange} />
          </div>
          <div className="flex flex-col gap-1.5 w-24">
            <label className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Initial degree</label>
            <Input type="number" name="degree" value={initParams.degree} onChange={handleInitParamsChange} />
          </div>
          <div className="flex flex-col gap-1.5 w-24">
            <label className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Steps to run</label>
            <Input type="number" name="steps" value={initParams.steps} onChange={handleInitParamsChange} />
          </div>
        </div>

        <div className="border border-border/50 rounded-lg p-5 bg-secondary/20">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-4 flex items-center gap-2">
            Utility Function Weights & Search Parameters
          </h4>
          <div className="flex flex-wrap gap-5 items-end">
            <div className="flex flex-col gap-1.5 w-24">
              <label className="text-xs text-muted-foreground font-medium truncate" title="Hub-seeking desire">α (Centrality)</label>
              <Input type="number" name="alpha" value={weightParams.alpha} onChange={handleWeightParamsChange} step="0.1" />
            </div>
            <div className="flex flex-col gap-1.5 w-24">
              <label className="text-xs text-muted-foreground font-medium truncate" title="Connection penalty">β (Cost)</label>
              <Input type="number" name="beta" value={weightParams.beta} onChange={handleWeightParamsChange} step="0.1" />
            </div>
            <div className="flex flex-col gap-1.5 w-24">
              <label className="text-xs text-muted-foreground font-medium truncate" title="Clustering incentive">γ (Similarity)</label>
              <Input type="number" name="gamma" value={weightParams.gamma} onChange={handleWeightParamsChange} step="0.1" />
            </div>
            <div className="flex flex-col gap-1.5 w-24">
              <label className="text-xs text-muted-foreground font-medium truncate" title="Betweenness Centrality bonus">BW Weight</label>
              <Input type="number" name="betweenness_weight" value={weightParams.betweenness_weight} onChange={handleWeightParamsChange} step="0.1" />
            </div>
            <div className="flex flex-col gap-1.5 w-24">
              <label className="text-xs text-muted-foreground font-medium">Query TTL</label>
              <Input type="number" name="query_ttl" value={weightParams.query_ttl} onChange={handleWeightParamsChange} />
            </div>
            <div className="flex flex-col gap-1.5 w-24">
              <label className="text-xs text-muted-foreground font-medium">Search queries</label>
              <Input type="number" name="num_search_queries" value={weightParams.num_search_queries} onChange={handleWeightParamsChange} />
            </div>
            
            <div className="flex flex-col justify-center items-center gap-1.5 w-24 mb-1">
              <label className="text-xs text-muted-foreground font-medium">Enable Churn</label>
              <Switch 
                checked={weightParams.churn_enabled} 
                onCheckedChange={(checked) => setWeightParams(prev => ({ ...prev, churn_enabled: checked }))} 
              />
            </div>
            <div className="flex flex-col gap-1.5 w-24">
              <label className="text-xs text-muted-foreground font-medium">Churn Rate</label>
              <Input type="number" name="churn_rate" value={weightParams.churn_rate} onChange={handleWeightParamsChange} step="0.01" />
            </div>
            <div className="flex flex-col gap-1.5 w-24">
              <label className="text-xs text-muted-foreground font-medium">Churn Interval</label>
              <Input type="number" name="churn_interval" value={weightParams.churn_interval} onChange={handleWeightParamsChange} />
            </div>
            <div className="flex flex-col gap-1.5 w-24">
              <label className="text-xs text-muted-foreground font-medium">Defector Ratio</label>
              <Input type="number" name="defector_ratio" value={weightParams.defector_ratio} onChange={handleWeightParamsChange} step="0.01" />
            </div>
            
            <Button 
              onClick={() => applyWeights(weightParams)} 
              variant="outline" 
              className="border-green-500/50 text-green-600 dark:text-green-400 hover:bg-green-500/10"
            >
              Apply weights
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
