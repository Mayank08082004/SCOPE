import React, { useRef, useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";

export function NetworkGraph({ nodes, edges, onNodeClick }) {
  const canvasRef = useRef(null);
  const simPositionsRef = useRef({});

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !nodes.length) return;
    const ctx = canvas.getContext('2d');
    
    // We want the canvas to automatically match its display size.
    // To handle resize easily, we could use ResizeObserver, 
    // but for now we'll just set it to its clientWidth.
    const W = canvas.parentElement.clientWidth;
    const H = 300;
    canvas.width = W;
    canvas.height = H;

    ctx.clearRect(0, 0, W, H);

    const maxDeg = Math.max(...nodes.map(n => n.degree), 1);
    const sample = nodes.length > 150 ? [...nodes].sort(() => Math.random() - 0.5).slice(0, 150) : nodes;
    const sIds = new Set(sample.map(n => n.id));
    const sEdges = edges.filter(e => sIds.has(e.source) && sIds.has(e.target));

    // Update positions in the ref instead of state to avoid infinite re-renders
    const currentPositions = simPositionsRef.current;
    nodes.forEach(n => {
      if (!currentPositions[n.id]) currentPositions[n.id] = { x: Math.random(), y: Math.random() };
    });

    // Draw edges
    ctx.strokeStyle = 'rgba(150, 150, 150, 0.15)';
    ctx.lineWidth = 1;
    sEdges.forEach(e => {
      const a = currentPositions[e.source];
      const b = currentPositions[e.target];
      if (!a || !b) return;
      const ax = 24 + a.x * (W - 48), ay = 24 + a.y * (H - 48);
      const bx = 24 + b.x * (W - 48), by = 24 + b.y * (H - 48);
      ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.stroke();
    });

    // Draw nodes
    nodes.forEach(n => {
      const p = currentPositions[n.id];
      if (!p) return;
      const px = 24 + p.x * (W - 48), py = 24 + p.y * (H - 48);
      
      let r, fill;
      if (n.is_offline) {
        r = 4;
        fill = '#ef4444'; // Red for offline nodes
      } else if (n.is_defector) {
        const ratio = n.degree / maxDeg;
        r = 3 + ratio * 11;
        fill = '#f97316'; // Orange for defectors
      } else {
        const ratio = n.degree / maxDeg;
        r = 3 + ratio * 11;
        fill = ratio > 0.6 ? '#3b82f6' : ratio > 0.3 ? '#8b5cf6' : '#64748b';
      }
      
      ctx.beginPath(); ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fillStyle = fill;
      ctx.fill();
    });

  }, [nodes, edges]);

  const handleCanvasClick = (ev) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const W = canvas.width;
    const H = canvas.height;
    
    // Calculate the scale between CSS display size and internal canvas coordinate size
    const scaleX = W / rect.width;
    const scaleY = H / rect.height;
    
    const mx = (ev.clientX - rect.left) * scaleX;
    const my = (ev.clientY - rect.top) * scaleY;
    
    let closest = null, minD = 20; // 20 pixels radius mapped
    
    nodes.forEach(n => {
      const p = simPositionsRef.current[n.id];
      if (!p) return;
      const px = 24 + p.x * (W - 48), py = 24 + p.y * (H - 48);
      const d = Math.hypot(mx - px, my - py);
      if (d < minD) { minD = d; closest = n; }
    });
    
    if (closest && onNodeClick) {
      onNodeClick(closest.id);
    }
  };

  return (
    <Card className="col-span-2 lg:col-span-1">
      <CardHeader>
        <CardTitle>Network Topology</CardTitle>
        <CardDescription>Sampled up to 150 nodes. Click nodes to inspect.</CardDescription>
      </CardHeader>
      <CardContent className="flex justify-center">
        <canvas 
          ref={canvasRef}
          onClick={handleCanvasClick}
          className="w-full h-[300px] cursor-crosshair rounded-md bg-secondary/50 border border-border"
        />
      </CardContent>
    </Card>
  );
}
