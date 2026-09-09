import React, { useState, useEffect, useMemo } from 'react';
import PageHeader from '../components/common/PageHeader';
import { Network, GitFork, Layers, RefreshCw, AlertCircle, Search, Filter, Calendar, Tag, ChevronRight, Info } from 'lucide-react';
import PrototypeDisclaimer from '../components/common/PrototypeDisclaimer';
import { getStandardsNetwork, getStandardSubgraph } from '../services/api';

export default function NetworkPage() {
  const [networkData, setNetworkData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [edgeFilter, setEdgeFilter] = useState('ALL'); // 'ALL', 'DECLARED', 'INFERRED'
  const [searchQuery, setSearchQuery] = useState('');
  const [subgraphLoading, setSubgraphLoading] = useState(false);

  // Fetch full network on mount
  const fetchNetwork = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getStandardsNetwork();
      setNetworkData(res);

      // Check if URL contains standard_id parameter
      const params = new URLSearchParams(window.location.search);
      const targetId = params.get('standard_id') || params.get('id');
      if (targetId && res.nodes.some(n => n.id === targetId)) {
        setSelectedNodeId(targetId);
      } else if (res.nodes.length > 0) {
        setSelectedNodeId(res.nodes[0].id);
      }
    } catch (err) {
      console.error('Failed to load standards network graph:', err);
      setError(err.message || 'Failed to connect to backend network service');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNetwork();
  }, []);

  // Filter edges based on edgeFilter selector
  const filteredEdges = useMemo(() => {
    if (!networkData?.edges) return [];
    if (edgeFilter === 'DECLARED') return networkData.edges.filter(e => !e.is_inferred);
    if (edgeFilter === 'INFERRED') return networkData.edges.filter(e => e.is_inferred);
    return networkData.edges;
  }, [networkData, edgeFilter]);

  // Compute node layout positions deterministically in a ring / cluster arrangement
  const nodePositions = useMemo(() => {
    if (!networkData?.nodes) return {};
    const nodes = networkData.nodes;
    const count = nodes.length;
    const positions = {};
    const centerX = 400;
    const centerY = 280;
    const radius = 210;

    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / count - Math.PI / 2;
      positions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    return positions;
  }, [networkData]);

  // Active selected node object
  const selectedNode = useMemo(() => {
    if (!selectedNodeId || !networkData?.nodes) return null;
    return networkData.nodes.find(n => n.id === selectedNodeId) || null;
  }, [selectedNodeId, networkData]);

  // Connected edges for the selected node
  const connectedEdges = useMemo(() => {
    if (!selectedNodeId || !filteredEdges) return [];
    return filteredEdges.filter(e => e.source === selectedNodeId || e.target === selectedNodeId);
  }, [selectedNodeId, filteredEdges]);

  // Connected neighbor node IDs
  const neighborIds = useMemo(() => {
    const ids = new Set();
    connectedEdges.forEach(e => {
      if (e.source === selectedNodeId) ids.add(e.target);
      if (e.target === selectedNodeId) ids.add(e.source);
    });
    return Array.from(ids);
  }, [selectedNodeId, connectedEdges]);

  // Focus and fetch depth-1 subgraph neighborhood for selected standard
  const handleFocusSubgraph = async (nodeId) => {
    setSubgraphLoading(true);
    try {
      const subRes = await getStandardSubgraph(nodeId, 1);
      if (subRes) {
        setSelectedNodeId(subRes.center_node.id);
      }
    } catch (err) {
      console.error('Failed to fetch standard subgraph:', err);
    } finally {
      setSubgraphLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <PageHeader
        title="Standards Network — SIH 2026 Prototype"
        subtitle="Explore directional cross-references, test method standards, safety specifications, and product category relationships between Indian Standards."
        badgeText="Deterministic NetworkX Knowledge Graph"
      />

      <PrototypeDisclaimer />

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center space-x-3">
          <div className="p-3 bg-govnavy-50 rounded-lg text-govnavy-800">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Standard Nodes
            </span>
            <span className="text-xl font-bold font-mono text-slate-900">
              {loading ? '...' : networkData?.total_nodes || 0}
            </span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center space-x-3">
          <div className="p-3 bg-blue-50 rounded-lg text-blue-700">
            <GitFork className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Declared Relationships
            </span>
            <span className="text-xl font-bold font-mono text-blue-900">
              {loading ? '...' : networkData?.declared_edge_count || 0}
            </span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center space-x-3">
          <div className="p-3 bg-amber-50 rounded-lg text-amber-700">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Category Clusters
            </span>
            <span className="text-xl font-bold font-mono text-amber-900">
              {loading ? '...' : networkData?.inferred_edge_count || 0}
            </span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex items-center space-x-3">
          <div className="p-3 bg-emerald-50 rounded-lg text-emerald-700">
            <Filter className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
              Traversal Engine
            </span>
            <span className="text-xs font-bold text-emerald-800 block mt-1">
              NetworkX Graph Core
            </span>
          </div>
        </div>
      </div>

      {/* Main Canvas & Detail Sidebar Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Interactive Graph Canvas */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4 flex flex-col justify-between">
          
          {/* Header Controls */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Network className="w-5 h-5 text-govnavy-800 shrink-0" />
              <h2 className="text-base font-bold text-slate-900">Standards Knowledge Graph Visualizer</h2>
            </div>

            {/* Controls */}
            <div className="flex items-center space-x-2">
              <select
                value={edgeFilter}
                onChange={(e) => setEdgeFilter(e.target.value)}
                className="text-xs px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded font-semibold text-slate-800 focus:outline-none focus:ring-1 focus:ring-govnavy-800"
              >
                <option value="ALL">All Relationships ({networkData?.total_edges || 0})</option>
                <option value="DECLARED">Declared References Only ({networkData?.declared_edge_count || 0})</option>
                <option value="INFERRED">Category Clusters Only ({networkData?.inferred_edge_count || 0})</option>
              </select>

              <button
                onClick={fetchNetwork}
                title="Reset network graph view"
                className="p-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>

          {loading ? (
            <div className="h-[560px] flex flex-col items-center justify-center space-y-3 text-slate-500 text-xs">
              <RefreshCw className="w-8 h-8 animate-spin text-govnavy-800" />
              <span>Building NetworkX Knowledge Graph Visualization...</span>
            </div>
          ) : error ? (
            <div className="h-[560px] flex flex-col items-center justify-center p-6 bg-rose-50 border border-rose-200 rounded text-xs text-rose-800 space-y-3">
              <AlertCircle className="w-8 h-8 text-rose-600" />
              <span>{error}</span>
              <button
                onClick={fetchNetwork}
                className="px-4 py-2 bg-rose-100 hover:bg-rose-200 text-rose-900 rounded font-semibold transition-colors"
              >
                Retry Graph Connection
              </button>
            </div>
          ) : (
            <div className="relative bg-slate-950 rounded-lg overflow-hidden border border-slate-800 p-2">
              
              {/* SVG Canvas */}
              <svg viewBox="0 0 800 560" className="w-full h-[540px] select-none">
                
                {/* Background Grid Pattern */}
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.5" />
                  </pattern>
                  <marker id="arrow-declared" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#3b82f6" />
                  </marker>
                  <marker id="arrow-inferred" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
                  </marker>
                </defs>
                
                <rect width="800" height="560" fill="url(#grid)" />

                {/* Edges */}
                {filteredEdges.map((edge, idx) => {
                  const p1 = nodePositions[edge.source];
                  const p2 = nodePositions[edge.target];
                  if (!p1 || !p2) return null;

                  const isConnectedToSelected =
                    selectedNodeId && (edge.source === selectedNodeId || edge.target === selectedNodeId);

                  const strokeColor = edge.is_inferred
                    ? isConnectedToSelected ? '#fbbf24' : '#78350f'
                    : isConnectedToSelected ? '#60a5fa' : '#1e3a8a';

                  const strokeWidth = isConnectedToSelected ? 2.5 : 1.2;
                  const strokeDash = edge.is_inferred ? '4 3' : 'none';
                  const marker = edge.is_inferred ? 'url(#arrow-inferred)' : 'url(#arrow-declared)';

                  return (
                    <line
                      key={idx}
                      x1={p1.x}
                      y1={p1.y}
                      x2={p2.x}
                      y2={p2.y}
                      stroke={strokeColor}
                      strokeWidth={strokeWidth}
                      strokeDasharray={strokeDash}
                      markerEnd={marker}
                      opacity={selectedNodeId && !isConnectedToSelected ? 0.3 : 0.85}
                    />
                  );
                })}

                {/* Nodes */}
                {(networkData?.nodes || []).map((node) => {
                  const pos = nodePositions[node.id];
                  if (!pos) return null;

                  const isSelected = selectedNodeId === node.id;
                  const isNeighbor = neighborIds.includes(node.id);
                  const isMatchSearch = searchQuery.trim() && (
                    node.is_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    node.title.toLowerCase().includes(searchQuery.toLowerCase())
                  );

                  let fillColor = '#0f172a';
                  let strokeColor = '#334155';
                  let radius = 18;

                  if (isSelected) {
                    fillColor = '#1e3a8a';
                    strokeColor = '#60a5fa';
                    radius = 24;
                  } else if (isNeighbor) {
                    fillColor = '#1e293b';
                    strokeColor = '#fbbf24';
                    radius = 21;
                  } else if (isMatchSearch) {
                    fillColor = '#065f46';
                    strokeColor = '#34d399';
                    radius = 22;
                  }

                  const labelText = node.is_number.split(' ')[0] + ' ' + (node.is_number.split(' ')[1] || '');

                  return (
                    <g
                      key={node.id}
                      transform={`translate(${pos.x}, ${pos.y})`}
                      onClick={() => setSelectedNodeId(node.id)}
                      className="cursor-pointer group"
                    >
                      {/* Outer pulse for selected node */}
                      {isSelected && (
                        <circle r={radius + 6} fill="none" stroke="#60a5fa" strokeWidth="1.5" className="animate-ping opacity-50" />
                      )}

                      {/* Main Node Circle */}
                      <circle
                        r={radius}
                        fill={fillColor}
                        stroke={strokeColor}
                        strokeWidth={isSelected ? 3 : 2}
                        className="transition-all duration-150 group-hover:stroke-saffron-400"
                      />

                      {/* Node Center Icon / Text */}
                      <text
                        textAnchor="middle"
                        dy="0.35em"
                        fontSize={isSelected ? "11" : "9"}
                        fontWeight="bold"
                        fill="#f8fafc"
                        className="font-mono pointer-events-none"
                      >
                        {node.id.split('-')[1] || node.id.slice(0, 6)}
                      </text>

                      {/* Floating Designation Label below Node */}
                      <text
                        textAnchor="middle"
                        y={radius + 14}
                        fontSize="9"
                        fontWeight="600"
                        fill={isSelected ? '#60a5fa' : isNeighbor ? '#fbbf24' : '#94a3b8'}
                        className="font-mono pointer-events-none"
                      >
                        {labelText}
                      </text>
                    </g>
                  );
                })}
              </svg>

              {/* Legend Footer */}
              <div className="absolute bottom-3 left-3 bg-slate-900/90 backdrop-blur-xs p-2.5 rounded border border-slate-800 text-[10px] text-slate-300 flex flex-wrap items-center gap-4">
                <div className="flex items-center space-x-1.5">
                  <div className="w-3 h-0.5 bg-blue-500"></div>
                  <span>Declared Reference</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <div className="w-3 h-0.5 border-b border-dashed border-amber-500"></div>
                  <span>Category Cluster</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-blue-900 border border-blue-400"></div>
                  <span>Selected Node</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-800 border border-amber-400"></div>
                  <span>Connected Neighbor</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right 1 Col: Selected Standard Detail Sidebar */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4 flex flex-col justify-between">
          
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
                <Info className="w-4 h-4 text-govnavy-800 shrink-0" />
                <span>Standard Network Inspector</span>
              </h3>
              {selectedNodeId && (
                <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-govnavy-900 text-white font-bold">
                  {selectedNodeId}
                </span>
              )}
            </div>

            {selectedNode ? (
              <div className="space-y-4 text-xs">
                <div>
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-govnavy-50 text-govnavy-900 border border-govnavy-200 block w-fit mb-1.5">
                    {selectedNode.is_number}
                  </span>
                  <h4 className="font-bold text-slate-900 leading-snug">{selectedNode.title}</h4>
                </div>

                <div className="space-y-1 bg-slate-50 p-3 rounded border border-slate-200">
                  <div className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-500">Category:</span>
                    <span className="font-semibold text-slate-800">{selectedNode.product_category}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-500">Sector:</span>
                    <span className="font-semibold text-slate-800">{selectedNode.sector}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-500">Revision Year:</span>
                    <span className="font-mono font-semibold text-slate-800">{selectedNode.revision_year || 'N/A'}</span>
                  </div>
                </div>

                {/* Connected Neighbors List */}
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-600 block mb-2">
                    Connected Network Neighbors ({neighborIds.length}):
                  </span>

                  {connectedEdges.length === 0 ? (
                    <p className="text-slate-500 text-[11px] italic">No direct relationships connected to this node.</p>
                  ) : (
                    <div className="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                      {connectedEdges.map((edge, idx) => {
                        const targetId = edge.source === selectedNodeId ? edge.target : edge.source;
                        const neighborNode = networkData?.nodes.find(n => n.id === targetId);
                        if (!neighborNode) return null;

                        return (
                          <div
                            key={idx}
                            onClick={() => setSelectedNodeId(neighborNode.id)}
                            className="p-2.5 rounded bg-slate-50 hover:bg-govnavy-50 border border-slate-200 hover:border-govnavy-300 transition-all cursor-pointer group flex items-start justify-between gap-2"
                          >
                            <div>
                              <div className="flex items-center space-x-1.5 mb-1">
                                <span className="font-mono text-[11px] font-bold text-govnavy-900">
                                  {neighborNode.is_number}
                                </span>
                                {edge.is_inferred ? (
                                  <span className="px-1.5 py-0.2 rounded bg-amber-100 text-amber-900 text-[9px] font-semibold border border-amber-200">
                                    Category
                                  </span>
                                ) : (
                                  <span className="px-1.5 py-0.2 rounded bg-blue-100 text-blue-900 text-[9px] font-semibold border border-blue-200">
                                    Declared
                                  </span>
                                )}
                              </div>
                              <p className="text-[11px] text-slate-700 line-clamp-1 group-hover:text-govnavy-900">
                                {neighborNode.title}
                              </p>
                            </div>
                            <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-govnavy-800 shrink-0 mt-1" />
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs space-y-2">
                <Network className="w-8 h-8 mx-auto text-slate-400" />
                <p>Select any node in the graph to inspect its standards relationships and connected neighbors.</p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          {selectedNode && (
            <div className="pt-3 border-t border-slate-200 space-y-2">
              <button
                onClick={() => handleFocusSubgraph(selectedNode.id)}
                disabled={subgraphLoading}
                className="w-full py-2 bg-govnavy-900 hover:bg-govnavy-800 text-white text-xs font-semibold rounded shadow-xs transition-colors flex items-center justify-center space-x-1.5"
              >
                {subgraphLoading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <GitFork className="w-3.5 h-3.5" />
                )}
                <span>Focus Subgraph Neighborhood</span>
              </button>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
