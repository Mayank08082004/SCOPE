import React from 'react';
import { Card, CardContent } from "@/components/ui/card";

export function MetricsDisplay({ metrics, steps }) {
  const m = metrics || {};
  
  const stats = [
    { label: "Nodes", value: m.num_nodes || 0, desc: "in graph" },
    { label: "Edges", value: m.num_edges || 0, desc: "connections" },
    { label: "Avg Path Length", value: m.apl ? m.apl.toFixed(6) : "0", desc: "hops" },
    { label: "Clustering Coeff", value: m.clustering_coefficient ? m.clustering_coefficient.toFixed(6) : "0", desc: "0 -> 1" },
    { label: "Avg Degree", value: m.avg_degree ? m.avg_degree.toFixed(2) : "0", desc: "per node" },
    { label: "Density", value: m.density ? m.density.toFixed(5) : "0", desc: "graph density" },
    { label: "Steps Run", value: steps || 0, desc: "evolution steps" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-6">
      {stats.map((s, i) => (
        <Card key={i} className="bg-card">
          <CardContent className="p-4 flex flex-col justify-center h-full">
            <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-1">{s.label}</div>
            <div className="text-2xl font-bold">{s.value}</div>
            <div className="text-xs text-muted-foreground mt-1">{s.desc}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
