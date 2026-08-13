import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, ScatterChart, Scatter, Cell } from 'recharts';

export function MetricsCharts({ history, graphData, nodesStats }) {
  // Format history data for line charts
  const historyData = history?.apl?.map((val, i) => ({
    step: `S${i}`,
    apl: val,
    cc: history.clustering[i]
  })) || [];

  // Degree Distribution Data (from nodesStats or compute manually if needed)
  // Re-use logic from previous charts: group degrees into buckets
  const degreeBuckets = {};
  if (nodesStats && nodesStats.length) {
    nodesStats.forEach(n => {
      // simplified bucket logic, similar to the original app
      const bucket = Math.floor(n.degree / 2) * 2;
      const bucketLabel = `${bucket}-${bucket + 1}`;
      degreeBuckets[bucketLabel] = (degreeBuckets[bucketLabel] || 0) + 1;
    });
  }
  
  const degreeData = Object.keys(degreeBuckets).sort((a,b) => parseInt(a) - parseInt(b)).map(k => ({
    bucket: k,
    count: degreeBuckets[k]
  }));

  const bwData = (nodesStats || []).map(n => ({
    degree: n.degree,
    bandwidth: n.bandwidth
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Avg Path Length Over Time</CardTitle>
        </CardHeader>
        <CardContent className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="step" stroke="var(--color-muted-foreground)" fontSize={12} tickLine={false} />
              <YAxis stroke="var(--color-muted-foreground)" fontSize={12} tickLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'var(--color-popover)', border: '1px solid var(--color-border)' }}
                itemStyle={{ color: 'var(--color-chart-1)' }}
              />
              <Line type="monotone" dataKey="apl" name="APL" stroke="var(--color-chart-1)" strokeWidth={2} dot={{ r: 3, fill: "var(--color-chart-1)" }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Clustering Coefficient Over Time</CardTitle>
        </CardHeader>
        <CardContent className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="step" stroke="var(--color-muted-foreground)" fontSize={12} tickLine={false} />
              <YAxis stroke="var(--color-muted-foreground)" fontSize={12} tickLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'var(--color-popover)', border: '1px solid var(--color-border)' }}
                itemStyle={{ color: 'var(--color-chart-2)' }}
              />
              <Line type="monotone" dataKey="cc" name="Clustering" stroke="var(--color-chart-2)" strokeWidth={2} dot={{ r: 3, fill: "var(--color-chart-2)" }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Degree Distribution</CardTitle>
        </CardHeader>
        <CardContent className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={degreeData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis dataKey="bucket" stroke="var(--color-muted-foreground)" fontSize={12} tickLine={false} />
              <YAxis stroke="var(--color-muted-foreground)" fontSize={12} tickLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'var(--color-popover)', border: '1px solid var(--color-border)', borderRadius: '6px' }}
                cursor={{ fill: 'var(--color-muted)' }}
              />
              <Bar dataKey="count" name="Nodes" fill="var(--color-chart-3)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Bandwidth vs Degree</CardTitle>
        </CardHeader>
        <CardContent className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="degree" type="number" name="Degree" stroke="var(--color-muted-foreground)" fontSize={12} tickLine={false} />
              <YAxis dataKey="bandwidth" type="number" name="Bandwidth" unit=" Mbps" stroke="var(--color-muted-foreground)" fontSize={12} tickLine={false} />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ backgroundColor: 'var(--color-popover)', border: '1px solid var(--color-border)', borderRadius: '6px' }}
              />
              <Scatter name="Nodes" data={bwData} fill="var(--color-chart-4)">
                {bwData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill="var(--color-chart-4)" />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
