<template>
  <div class="graph-root">
    <div class="graph-header">
      <div class="header-left">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="header-icon">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
        </svg>
        <div class="header-titles">
          <h3>Architecture Map</h3>
          <p>Project Structure & Cross-File Dependencies</p>
        </div>
      </div>

      <!-- Isolation Mode Banner -->
      <div v-if="isIsolationActive" class="isolation-banner pulse-purple">
        <div class="banner-content">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
          <span class="banner-text"><strong>Journey Isolation Active</strong>: Showing only the spine from Entry Points to this component</span>
        </div>
        <button class="btn-exit" @click="exitIsolation">
          Exit Isolation
        </button>
      </div>

      <div class="header-actions">
        <div class="view-toggle">
          <button 
            :class="['btn-toggle', viewMode === 'ai' ? 'active' : '']" 
            @click="viewMode = 'ai'">
            ✧ AI Map
          </button>
          <button 
            :class="['btn-toggle', viewMode === 'visual' ? 'active' : '']" 
            @click="viewMode = 'visual'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M4 10a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4zm14 0a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-4zM4 22a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4zm14 0a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-4z"></path></svg>
            File Explorer
          </button>
          <button 
            :class="['btn-toggle', viewMode === 'mindmap' ? 'active' : '']" 
            @click="activateMindmap">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
            Project Mindmap
          </button>
        </div>
      </div>
    </div>

    <div class="graph-container">
      <div v-if="loading" class="graph-loading">
        <div class="spinner"></div>
        <p>Analyzing project structure...</p>
      </div>
      
      <div v-if="error" class="graph-error">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        <p>{{ error }}</p>
        <button class="btn-secondary" @click="fetchData">Retry</button>
      </div>
      
      <!-- AI Architecture Mode (New) -->
      <div v-if="viewMode === 'ai' && !loading && !error" class="ai-view-container">
        
        <div v-if="aiArchitectureError" class="ai-warning">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          <p>{{ aiArchitectureError }}</p>
        </div>
        
        <div v-else-if="aiArchitecture" class="ai-content">
          <div class="ai-overview card pulse-glow">
            <div class="ai-badge">✧ AI SUMMARY</div>
            <h2>Project Ecosystem</h2>
            <p>{{ aiArchitecture.project_overview }}</p>
          </div>

          <div class="ai-grid">
             <!-- Architectural Layers -->
             <div class="ai-layers">
               <h3 class="section-title">Architectural Layers</h3>
               <div class="layers-grid">
                 <div v-for="(layer, index) in aiArchitecture.layers" :key="index" class="layer-card hover-lift">
                   <h4>{{ layer.layer_name }}</h4>
                   <p>{{ layer.description }}</p>
                   <div class="file-tags">
                     <span v-for="file in layer.file_names" :key="file" class="tag tag-file">{{ file }}</span>
                   </div>
                 </div>
               </div>
             </div>

             <!-- Key Workflows -->
             <div class="ai-workflows" v-if="aiArchitecture.key_workflows && aiArchitecture.key_workflows.length">
               <h3 class="section-title">Key Workflows & Data Flow</h3>
               <div class="workflows-list">
                 <div v-for="(flow, index) in aiArchitecture.key_workflows" :key="index" class="workflow-card">
                   <div class="workflow-icon">
                     <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
                   </div>
                   <div class="workflow-content">
                     <h4>{{ flow.name }}</h4>
                     <p>{{ flow.description }}</p>
                   </div>
                 </div>
               </div>
             </div>
          </div>
        </div>
        
        <div v-else class="ai-pending">
          <p>No AI analysis available. Please rebuild the project report.</p>
        </div>
      </div>

      <!-- Focused Explorer View (Redesigned) -->
      <div v-show="viewMode === 'visual' && !loading && !error" class="explorer-layout">
        
        <!-- Left Sidebar: File Tree -->
        <div class="explorer-sidebar">
          <div class="sidebar-header">
            <div class="search-wrap">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="search-icon"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <input 
                type="text" 
                v-model="searchQuery" 
                placeholder="Find a file..."
                class="search-input full-width"
              />
            </div>
          </div>
          
          <div class="explorer-list custom-scrollbar">
            <div v-if="filteredSortedFiles.length === 0" class="empty-list">
              No files matched.
            </div>
            
            <button 
              v-for="file in filteredSortedFiles" 
              :key="file.id"
              :class="['file-item', selectedNode && selectedNode.id === file.id ? 'active' : '']"
              @click="focusEcosystem(file.id)"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="file-icon"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>
              <span class="file-name">{{ file.label }}</span>
              <span v-if="getFileIssueCount(file.label) > 0" class="badge badge-danger" style="margin-left:auto; font-size:0.6rem; padding: 0.1rem 0.3rem;">{{ getFileIssueCount(file.label) }} defects</span>
            </button>
          </div>
        </div>

        <!-- Right Side: Active Dependency Map -->
        <div class="explorer-main">
          
          <div v-if="!selectedNode" class="empty-canvas-state">
            <div class="empty-icon-wrap">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>
            </div>
            <h4>Select a File to Inspect</h4>
            <p>Pick a component from the left to visualize its direct imports and dependencies without the clutter.</p>
          </div>

          <div v-show="selectedNode" class="canvas-wrapper">
            <div class="canvas-center">
              <div class="canvas-toolbar">
                <div class="node-title-badge">
                  <span class="badge-label">FOCUSED NODE</span>
                  <strong>{{ selectedNode?.label }}</strong>
                </div>
                <div v-if="selectedNode?.is_circular" class="circular-warning pulse-red">
                   <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                   CIRCULAR DEP
                </div>
                <div class="analysis-mode-selector">
                  <button 
                    :class="['btn-mode', activeAnalysisMode === 'ecosystem' ? 'active' : '']"
                    @click="setAnalysisMode('ecosystem')"
                    title="Show direct dependencies and dependents"
                  >
                    🔍 Local View
                  </button>
                  <button 
                    :class="['btn-mode', activeAnalysisMode === 'blast' ? 'active' : '']"
                    @click="setAnalysisMode('blast')"
                    title="Show downstream blast radius of transitive parents"
                  >
                    💥 Blast Radius
                  </button>
                </div>
                <button class="btn-ghost" @click="toggleLayout">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 10h16M4 14h16M10 6v12M14 6v12"></path></svg>
                  {{ layoutMode === 'physics' ? 'Hierarchy' : 'Exploration' }}
                </button>
                <button class="btn-ghost" @click="resetCamera">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><polyline points="3 3 3 8 8 8"></polyline></svg>
                  Center
                </button>
              </div>

              <!-- Vis Network Container -->
              <div ref="graphCanvas" class="graph-canvas"></div>
            </div>            <!-- Refactor Safety Side-Drawer Dashboard (Blast Radius Mode) -->
            <div class="detail-panel refactor-dashboard" v-if="selectedNode && activeAnalysisMode === 'blast'">
              <!-- Title & Header -->
              <div class="panel-section dashboard-header">
                <div class="header-badge pulse-orange">💥 REFACTOR PLAYGROUND</div>
                <h3>Refactor Risk Assessment</h3>
                <p class="subtitle">Analyzing downstream blast radius and refactoring safety metrics</p>
              </div>

              <!-- Dynamic Risk Gauge Section -->
              <div class="panel-section risk-gauge-section">
                <div class="risk-gauge-container">
                  <svg class="progress-ring" width="120" height="120">
                    <circle 
                      class="progress-ring-bg" 
                      stroke="var(--border-subtle)" 
                      stroke-width="8" 
                      fill="transparent" 
                      r="48" 
                      cx="60" 
                      cy="60"
                    />
                    <circle 
                      class="progress-ring-circle" 
                      :stroke="riskGaugeColor" 
                      stroke-width="8" 
                      stroke-linecap="round"
                      fill="transparent" 
                      r="48" 
                      cx="60" 
                      cy="60"
                      :stroke-dasharray="strokeDashArray"
                      :stroke-dashoffset="strokeDashOffset"
                    />
                  </svg>
                  <div class="risk-gauge-value">
                    <span class="score-number">{{ blastRadiusRiskScore }}%</span>
                    <span :class="['score-rating', riskRatingClass]">{{ riskRatingName }}</span>
                  </div>
                </div>
              </div>

              <!-- Downstream Impact Summary Stats -->
              <div class="panel-section metrics-section">
                <label>Blast Radius Metrics</label>
                <div class="metrics-grid">
                  <div class="metric-card">
                    <div class="metric-val text-orange">{{ transitiveDependents.length }}</div>
                    <div class="metric-lbl">Total Impacted Files</div>
                  </div>
                  <div class="metric-card">
                    <div class="metric-val text-amber">{{ dependents.length }}</div>
                    <div class="metric-lbl">Direct Dependents</div>
                  </div>
                  <div class="metric-card">
                    <div class="metric-val" :class="nodeIssueCount > 0 ? 'text-red font-bold' : 'text-green'">{{ nodeIssueCount }}</div>
                    <div class="metric-lbl">Active Defects</div>
                  </div>
                  <div class="metric-card">
                    <div class="metric-val" :class="selectedNode?.is_circular ? 'text-red' : 'text-blue'">
                      {{ selectedNode?.is_circular ? 'Yes' : 'No' }}
                    </div>
                    <div class="metric-lbl">Circular Imports</div>
                  </div>
                </div>
              </div>

              <!-- Affected Upstream Spine -->
              <div class="panel-section entry-points-section">
                <label>Affected Upstream Spine (Entry Points & Pages)</label>
                <p class="description-small">Critical high-level components and routes that will be affected by code modifications here:</p>
                <div v-if="transitiveDependents.length" class="affected-list custom-scrollbar">
                  <button 
                    v-for="nid in transitiveDependents" 
                    :key="nid" 
                    class="affected-list-item hover-lift"
                    @click="focusEcosystem(nid)"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="item-icon"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    <span class="item-name">{{ graphData.file_map[nid]?.name }}</span>
                    <span v-if="graphData.file_map[nid]?.name.toLowerCase().includes('main') || graphData.file_map[nid]?.name.toLowerCase().includes('app') || graphData.file_map[nid]?.name.toLowerCase().includes('page')" class="entry-tag">Entry</span>
                  </button>
                </div>
                <p v-else class="empty-text">No downstream dependents affected.</p>
              </div>

              <!-- Safe Refactoring Checklist -->
              <div class="panel-section checklist-section">
                <label>Refactor Safety Checklist</label>
                <div class="checklist-items">
                  <label class="checklist-item">
                    <input type="checkbox" class="checklist-checkbox" checked />
                    <span class="checklist-text">Isolate and test local changes independently</span>
                  </label>
                  <label class="checklist-item">
                    <input type="checkbox" class="checklist-checkbox" :disabled="nodeIssueCount === 0" :checked="nodeIssueCount === 0" />
                    <span class="checklist-text" :class="{ 'strike-through-done': nodeIssueCount === 0 }">Resolve the {{ nodeIssueCount }} active component defects first</span>
                  </label>
                  <label class="checklist-item">
                    <input type="checkbox" class="checklist-checkbox" />
                    <span class="checklist-text">Ensure all exported interfaces and props are backward compatible</span>
                  </label>
                  <label class="checklist-item">
                    <input type="checkbox" class="checklist-checkbox" :disabled="!selectedNode?.is_circular" :checked="!selectedNode?.is_circular" />
                    <span class="checklist-text" :class="{ 'strike-through-done': !selectedNode?.is_circular }">Decouple existing import loop/circular reference</span>
                  </label>
                  <label class="checklist-item">
                    <input type="checkbox" class="checklist-checkbox" />
                    <span class="checklist-text">Run regression tests on all {{ transitiveDependents.length }} affected parent components</span>
                  </label>
                </div>
              </div>
            </div>

            <!-- Standard Details Panel (Ecosystem Mode) -->
            <div class="detail-panel" v-if="selectedNode && activeAnalysisMode !== 'blast'">
              <!-- Blast Radius / Issues warning -->
              <div v-if="nodeIssueCount > 0" class="panel-section circular-panel" style="background-color: var(--accent-danger-subtle); border-color: rgba(239,68,68,0.25);">
                <label class="red-label" style="display:flex; align-items:center; gap:0.4rem; color:var(--accent-danger)">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                  Blast Radius: {{ nodeIssueCount }} Issues
                </label>
                <p class="warning-text" style="color:var(--text-secondary); margin-top:0.4rem; font-size: 0.85rem">
                  This file contains active defects. Because it is imported by <strong style="color:var(--accent-danger)">{{ dependents.length }}</strong> component(s), those downstream files are part of the blast radius and could experience side-effects.
                </p>
              </div>

              <div v-if="selectedNode?.is_circular" class="panel-section circular-panel">
                <label class="red-label">Cycle Detected</label>
                <p class="warning-text">This file is part of an import cycle. Circular dependencies can lead to memory leaks and runtime errors.</p>
                <div v-if="relevantCycles.length" class="cycle-display">
                    <div v-for="(cycle, cIdx) in relevantCycles" :key="cIdx" class="cycle-path">
                        {{ cycle.map(id => graphData.file_map[id].name).join(' → ') }}
                    </div>
                </div>
              </div>

              <div class="panel-section">
                <label>Direct Impact ({{ dependents.length }} Parent{{ dependents.length !== 1 ? 's' : '' }})</label>
                <div v-if="dependents.length" class="connection-list">
                  <div v-for="dep in dependents" :key="dep.id" class="connection-item">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    {{ dep.label }}
                  </div>
                </div>
                <p v-else class="empty-text">No downstream dependents.</p>
              </div>

              <div class="panel-section">
                <label>Internal Dependencies ({{ dependencies.length }} Children)</label>
                <div v-if="dependencies.length" class="connection-list">
                  <div v-for="dep in dependencies" :key="dep.id" class="connection-item dependency">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"></polyline></svg>
                    {{ dep.label }}
                  </div>
                </div>
                <p v-else class="empty-text">No internal imports detected.</p>
              </div>

              <!-- Isolation Action -->
              <div class="panel-section action-section">
                <button 
                  v-if="!isIsolationActive"
                  class="btn-primary full-width" 
                  style="justify-content:center; gap:0.5rem; text-transform:uppercase; font-size:0.75rem; letter-spacing:0.04em"
                  @click="isolateUserJourney(selectedNode.id)"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                  Isolate User Journey
                </button>
                <div v-else class="isolation-status">
                  <div class="pulse-dot"></div>
                  Focusing on logical spine
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- Mindmap View (NotebookLM Style) -->
      <div v-show="viewMode === 'mindmap' && !loading && !error" class="mindmap-layout" style="height: 100%; width: 100%; position: relative; overflow: hidden;">
          <div class="mm-toolbar">
            <span class="mm-toolbar-title">🧠 Project Mind Map</span>
            <button class="mm-toolbar-btn" @click="resetMindmapCamera">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="M21 3l-7 7"/><path d="M3 21l7-7"/></svg>
              Fit View
            </button>
            <button class="mm-toolbar-btn" @click="expandAllMindmap">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
              Expand All
            </button>
            <button class="mm-toolbar-btn" @click="collapseAllMindmap">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
              Collapse
            </button>
          </div>
          <div ref="mindmapCanvas" class="mm-canvas"
               @mousedown="mmStartDrag" @mousemove="mmDrag" @mouseup="mmEndDrag" @mouseleave="mmEndDrag"
               @wheel.prevent="mmZoom">
            <div class="mm-transform" :style="mmTransformStyle">
              <svg class="mm-svg" :width="mmSvgWidth" :height="mmSvgHeight" :viewBox="mmSvgViewBox">
                <path v-for="(line, i) in mmLines" :key="'l'+i"
                      :d="line.d" fill="none" :stroke="line.color" :stroke-width="line.width"
                      stroke-linecap="round" :opacity="line.opacity" />
              </svg>
              <div v-for="n in mmRenderedNodes" :key="'n'+n.id"
                   class="mm-node"
                   :class="{ 'mm-node-root': n.isRoot, 'mm-node-leaf': !n.hasChildren, 'mm-node-expanded': n.isExpanded, 'mm-node-issue': n.hasIssues }"
                   :style="n.style"
                   @click.stop="mmToggleNode(n.id)">
                <span class="mm-node-label">{{ n.label }}</span>
                <span v-if="n.hasChildren" class="mm-node-badge">{{ n.childCount }}</span>
              </div>
            </div>
          </div>
      </div>

    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { Network } from 'vis-network';
import 'vis-network/styles/vis-network.css';

export default {
  name: 'DependencyGraph',
  props: {
    selectedReportId: { type: String, default: null }
  },
  data() {
    return {
      graphData: null,
      aiArchitecture: null,
      aiReportData: null,
      aiArchitectureError: null,
      viewMode: 'ai',
      layoutMode: 'physics',
      loading: true,
      error: null,
      selectedNode: null,
      searchQuery: '',
      isIsolationActive: false,
      isolatedNodeId: null,
      activeAnalysisMode: 'ecosystem',
      
      // Mindmap state
      expandedMindmapNodes: [],
      mmRenderedNodes: [],
      mmLines: [],
      mmTree: null,
      mmScale: 1,
      mmPanX: 0,
      mmPanY: 0,
      mmDragging: false,
      mmDragStartX: 0,
      mmDragStartY: 0,
      mmSvgWidth: 4000,
      mmSvgHeight: 4000,
      
      // Keep lists in data for computed filtering but use copies
      rawNodes: [],
      rawEdges: [],
      componentError: null,
      
      options: {
        physics: {
          enabled: true,
          solver: 'barnesHut',
          barnesHut: {
            gravitationalConstant: -2000,
            centralGravity: 0.1,
            springLength: 150,
            springConstant: 0.04,
            damping: 0.2,
            avoidOverlap: 0.2
          }
        },
        interaction: { hover: true, zoomView: true, dragView: true },
        edges: { smooth: { type: 'continuous' }, width: 2 }
      }
    };
  },
  computed: {
    nodeIssueCount() {
      if (!this.selectedNode || !this.aiReportData?.files) return 0;
      const fileReport = this.aiReportData.files.find(f => f.file_name === this.selectedNode.label);
      if (!fileReport) return 0;
      return (fileReport.ui_accessibility_analysis?.filter(i => i.is_real_issue)?.length || 0) +
             (fileReport.ai_analysis?.filter(i => i.is_real_issue)?.length || 0);
    },
    filteredSortedFiles() {
      const q = this.searchQuery.toLowerCase();
      return this.rawNodes
        .filter(n => n.label.toLowerCase().includes(q))
        .sort((a, b) => a.label.localeCompare(b.label));
    },
    dependents() {
      if (!this.selectedNode || !this.graphData) return [];
      const id = this.selectedNode.id;
      const dependentIds = this.graphData.impact_map[id] || [];
      return dependentIds.map(d_id => {
        const info = this.graphData.file_map[d_id];
        return { id: d_id, label: info.name };
      });
    },
    dependencies() {
      if (!this.selectedNode || !this.graphData) return [];
      const id = parseInt(this.selectedNode.id);
      return this.graphData.connections
        .filter(conn => conn.from_id === id)
        .map(conn => {
          const info = this.graphData.file_map[conn.to_id];
          return { id: conn.to_id, label: info.name };
        });
    },
    relevantCycles() {
      if (!this.selectedNode || !this.graphData?.cycles) return [];
      const id = parseInt(this.selectedNode.id);
      return this.graphData.cycles.filter(c => c.includes(id));
    },
    mmTransformStyle() {
      return {
        transform: `translate(${this.mmPanX}px, ${this.mmPanY}px) scale(${this.mmScale})`,
        transformOrigin: '0 0'
      };
    },
    mmSvgViewBox() {
      return `0 0 ${this.mmSvgWidth} ${this.mmSvgHeight}`;
    },
    transitiveDependents() {
      if (!this.selectedNode || !this.graphData) return [];
      return this.getTransitiveDependents(this.selectedNode.id);
    },
    blastRadiusRiskScore() {
      if (!this.selectedNode || !this.graphData) return 0;
      const directCount = this.dependents.length;
      const transitiveCount = this.transitiveDependents.length;
      const hasCycles = this.selectedNode.is_circular ? 1 : 0;
      const issuesCount = this.nodeIssueCount;
      
      let score = 0;
      if (transitiveCount > 0) {
        score += Math.min(40, directCount * 15);
        score += Math.min(40, (transitiveCount - directCount) * 8);
        score += hasCycles * 20;
        score += Math.min(20, issuesCount * 5);
      } else {
        score += Math.min(10, issuesCount * 5);
      }
      return Math.min(100, Math.round(score));
    },
    riskRatingName() {
      const score = this.blastRadiusRiskScore;
      if (score === 0) return 'NO RISK';
      if (score <= 20) return 'LOW RISK';
      if (score <= 60) return 'MEDIUM RISK';
      return 'HIGH RISK';
    },
    riskRatingClass() {
      const score = this.blastRadiusRiskScore;
      if (score === 0) return 'risk-none';
      if (score <= 20) return 'risk-low';
      if (score <= 60) return 'risk-medium';
      return 'risk-high';
    },
    riskGaugeColor() {
      const score = this.blastRadiusRiskScore;
      if (score === 0) return '#10b981';
      if (score <= 20) return '#3b82f6';
      if (score <= 60) return '#f59e0b';
      return '#ef4444';
    },
    strokeDashArray() {
      return 2 * Math.PI * 48;
    },
    strokeDashOffset() {
      const percent = this.blastRadiusRiskScore;
      const circumference = this.strokeDashArray;
      return circumference - (percent / 100) * circumference;
    }
  },
  async mounted() {
    await this.fetchData();
  },
  errorCaptured(err, instance, info) {
    console.error('[DependencyGraph] Component error caught:', err, info);
    this.componentError = `Architecture view encountered an error: ${err.message}`;
    this.error = this.componentError;
    return false;
  },
  methods: {
    async fetchData() {
      this.loading = true;
      this.error = null;
      this.aiArchitectureError = null;
      
      try {
        const reportQuery = this.selectedReportId ? `?id=${this.selectedReportId}&_t=${Date.now()}` : `?_t=${Date.now()}`;
        const [graphRes, aiRes, reportRes] = await Promise.allSettled([
          axios.get('/dependency_graph' + reportQuery),
          axios.get('/ai_architecture' + reportQuery),
          axios.get('/ai_report' + reportQuery)
        ]);
        
        if (reportRes.status === 'fulfilled' && reportRes.value.data) {
          this.aiReportData = reportRes.value.data;
        }
        
        if (graphRes.status === 'fulfilled') {
          if (!graphRes.value.data || !graphRes.value.data.file_map) {
            this.error = 'Graph data is in an invalid format. Run analysis again.';
          } else {
            const fileCount = Object.keys(graphRes.value.data.file_map).length;
            if (fileCount === 0) {
              this.error = 'No files detected in the project. Ensure the target folder is correct.';
            } else {
              this.graphData = graphRes.value.data;
              this.setupRawData();
              
              if (this.rawNodes.length > 0) {
                // Pre-select first item
                this.$nextTick(() => { this.focusEcosystem(this.rawNodes[0].id); });
              }
            }
          }
        } else if (graphRes.status === 'rejected' && graphRes.reason?.response?.status === 404) {
          this.error = 'Historical architecture data is not available for this run.';
        } else {
          this.error = 'Failed to fetch dependency graph. Connect to backend.';
        }

        if (aiRes.status === 'fulfilled' && aiRes.value.data && aiRes.value.data.project_overview) {
          this.aiArchitecture = aiRes.value.data;
        } else if (aiRes.status === 'rejected' && aiRes.reason?.response?.status === 404) {
          this.aiArchitectureError = 'Historical AI Architecture insights are not available for this run.';
          this.viewMode = 'visual'; // Fallback
        } else {
          this.aiArchitectureError = 'AI Architecture insights not available yet for this project.';
          this.viewMode = 'visual'; // Fallback
        }
        
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        this.loading = false;
      }
    },
    getFileIssueCount(fileName) {
      if (!this.aiReportData?.files) return 0;
      const fileReport = this.aiReportData.files.find(f => f.file_name === fileName);
      if (!fileReport) return 0;
      return (fileReport.ui_accessibility_analysis?.filter(i => i.is_real_issue)?.length || 0) +
             (fileReport.ai_analysis?.filter(i => i.is_real_issue)?.length || 0);
    },
    setupRawData() {
      const { file_map, connections } = this.graphData;
      
      this.rawNodes = Object.keys(file_map).map(id => {
        const nid = parseInt(id);
        const data = file_map[id];
        return {
          id: nid,
          label: data.name,
          path: data.path,
          is_circular: data.is_circular || false,
          exports: data.exports || []
        };
      });

      this.rawEdges = connections.map(conn => ({
        from: conn.from_id, 
        to: conn.to_id,
        arrows: { to: { enabled: true, scaleFactor: 0.8 } }
      }));
    },
    getTransitiveDependents(nodeId, visited = new Set()) {
      const nid = parseInt(nodeId);
      if (visited.has(nid)) return [];
      visited.add(nid);
      const direct = this.graphData?.impact_map?.[nid] || [];
      let all = direct.map(id => parseInt(id));
      for (const childId of direct) {
        all = all.concat(this.getTransitiveDependents(parseInt(childId), visited));
      }
      return Array.from(new Set(all));
    },
    setAnalysisMode(mode) {
      this.activeAnalysisMode = mode;
      if (this.selectedNode) {
        this.focusEcosystem(this.selectedNode.id);
      }
    },
    focusEcosystem(nodeId) {
      this.selectedNode = this.rawNodes.find(n => n.id === nodeId);
      if (!this.selectedNode) return;

      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      
      const hasIssues = this.nodeIssueCount > 0;
      
      // Calculate Journey if isolated
      let journey = null;
      if (this.isIsolationActive) {
        journey = this.findUserJourneyPaths(nodeId);
      }
      
      // Color Palette Definition
      const focusColor = hasIssues ? '#ef4444' : '#6366f1';     // Red if issues, else Indigo
      const dependentColor = hasIssues ? '#ef4444' : '#f59e0b'; // Red if affected, else Amber (Who imports me)
      const dependencyColor = '#0ea5e9'; // SkyBlue (What I import)
      const journeyColor = '#a855f7'; // Purple for journey pathway
      
      const textColor = isDark ? '#f0f0f5' : '#111118';
      const nodeBgColor = isDark ? '#1e1e2e' : '#ffffff'; // Opaque backgrounds for isolation
      
      // DEEP COPY edges to prevent Vue reactivity circular crashes
      let safeEdges = [];
      if (this.isIsolationActive && journey) {
        safeEdges = this.rawEdges
          .filter(e => {
            return Array.from(journey.edges).some(je => je.from_id === e.from && je.to_id === e.to);
          })
          .map(e => ({ ...e }));
      } else if (this.activeAnalysisMode === 'blast') {
        const transitiveDependents = this.getTransitiveDependents(nodeId);
        const blastRadiusIds = new Set([nodeId, ...transitiveDependents]);
        safeEdges = this.rawEdges
          .filter(e => blastRadiusIds.has(e.from) && blastRadiusIds.has(e.to))
          .map(e => ({ ...e }));
      } else {
        safeEdges = this.rawEdges
          .filter(e => e.from === nodeId || e.to === nodeId)
          .map(e => ({ ...e })); 
      }
      
      // Build ecosystem node set and apply active colors
      const ecoNodesMap = new Map();

      if (this.activeAnalysisMode === 'blast') {
        const transitiveDependents = this.getTransitiveDependents(nodeId);
        const blastRadiusIds = new Set([nodeId, ...transitiveDependents]);
        
        blastRadiusIds.forEach(nid => {
          const raw = this.rawNodes.find(n => n.id === nid);
          if (raw) {
            const isFocus = nid === nodeId;
            ecoNodesMap.set(nid, {
              ...raw,
              font: { color: textColor, size: isFocus ? 16 : 13, face: 'Inter, system-ui, sans-serif', bold: isFocus },
              shape: 'box',
              borderWidth: isFocus ? 3.5 : 2,
              borderRadius: isFocus ? 8 : 6,
              color: {
                background: isFocus 
                  ? (isDark ? 'rgba(239, 68, 68, 0.2)' : 'rgba(239, 68, 68, 0.1)')
                  : (isDark ? 'rgba(249, 115, 22, 0.12)' : 'rgba(249, 115, 22, 0.06)'),
                border: isFocus ? '#ef4444' : '#f97316',
                highlight: {
                  border: isFocus ? '#ef4444' : '#f97316',
                  background: isFocus ? 'rgba(239, 68, 68, 0.3)' : 'rgba(249, 115, 22, 0.2)'
                }
              },
              shadow: {
                enabled: true,
                color: isFocus ? 'rgba(239, 68, 68, 0.5)' : 'rgba(249, 115, 22, 0.25)',
                size: isFocus ? 12 : 6,
                x: 0, y: 0
              },
              margin: isFocus 
                ? { top: 14, bottom: 14, left: 18, right: 18 }
                : { top: 10, bottom: 10, left: 14, right: 14 }
            });
          }
        });

        safeEdges.forEach(edge => {
          edge.color = { color: '#f97316', opacity: 0.9 };
          edge.width = 2.5;
          edge.dashes = [6, 4];
        });
      } else {
        // Standard and Journey Isolation styling
        ecoNodesMap.set(nodeId, {
          ...this.selectedNode,
          color: {
            background: this.isIsolationActive ? nodeBgColor : (isDark ? 'rgba(99, 102, 241, 0.2)' : 'rgba(99, 102, 241, 0.1)'),
            border: this.isIsolationActive ? journeyColor : focusColor,
            highlight: { border: this.isIsolationActive ? journeyColor : focusColor, background: isDark ? 'rgba(99, 102, 241, 0.3)' : 'rgba(99, 102, 241, 0.2)' },
          },
          font: { color: textColor, size: 16, face: 'Inter, system-ui, sans-serif', bold: true },
          shape: 'box', borderWidth: this.isIsolationActive ? 3 : 3, borderRadius: 8,
          shadow: { enabled: true, color: this.isIsolationActive ? 'rgba(168, 85, 247, 0.4)' : 'rgba(99, 102, 241, 0.4)', size: 10, x: 0, y: 0 },
          margin: { top: 14, bottom: 14, left: 18, right: 18 }
        });

        safeEdges.forEach(edge => {
          const commonStyling = {
            font: { color: textColor, size: 13, face: 'Inter' },
            shape: 'box', borderWidth: 1.5, borderRadius: 6, margin: 10
          };

          if (this.isIsolationActive) {
            [edge.from, edge.to].forEach(nid => {
              if (!ecoNodesMap.has(nid)) {
                const raw = this.rawNodes.find(n => n.id === nid);
                if (raw) {
                  ecoNodesMap.set(nid, {
                    ...raw,
                    ...commonStyling,
                    color: { border: journeyColor, background: nodeBgColor },
                    borderWidth: 2
                  });
                }
              }
            });
            edge.color = { color: journeyColor, opacity: 1.0 };
            edge.width = 3;
          } else {
            if (edge.to === nodeId) {
              if (!ecoNodesMap.has(edge.from)) {
                const raw = this.rawNodes.find(n => n.id === edge.from);
                if (raw) {
                  ecoNodesMap.set(edge.from, {
                    ...raw,
                    ...commonStyling,
                    color: { border: dependentColor, background: isDark ? (hasIssues ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)') : (hasIssues ? 'rgba(239, 68, 68, 0.05)' : 'rgba(245, 158, 11, 0.05)') },
                    borderWidth: hasIssues ? 2 : 1.5
                  });
                }
              }
              edge.color = { color: dependentColor, opacity: hasIssues ? 1.0 : 0.6 };
              if (hasIssues) {
                edge.dashes = [8, 6];
                edge.width = 3;
              }
            }
            if (edge.from === nodeId) {
              if (!ecoNodesMap.has(edge.to)) {
                const raw = this.rawNodes.find(n => n.id === edge.to);
                if (raw) {
                  ecoNodesMap.set(edge.to, {
                    ...raw,
                    ...commonStyling,
                    color: { border: dependencyColor, background: isDark ? 'rgba(14, 165, 233, 0.1)' : 'rgba(14, 165, 233, 0.05)' },
                  });
                }
              }
              edge.color = { color: dependencyColor, opacity: 0.6 };
            }
          }
        });
      }

      // Break Vue proxy references completely
      const finalNodes = JSON.parse(JSON.stringify(Array.from(ecoNodesMap.values())));
      const finalEdges = JSON.parse(JSON.stringify(safeEdges));

      // Persistence: Update existing network instead of destroying
      if (!this.network) {
        this.network = new Network(
          this.$refs.graphCanvas, 
          { nodes: finalNodes, edges: finalEdges }, 
          this.options
        );
        
        this.network.on('click', (params) => {
          if (params.nodes.length > 0) {
            this.focusEcosystem(params.nodes[0]);
          }
        });
      } else {
        this.network.setData({ nodes: finalNodes, edges: finalEdges });
      }

      this.resetCamera();
    },
    resetCamera() {
      if (this.network) {
        setTimeout(() => {
          this.network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
        }, 100);
      }
    },
    findUserJourneyPaths(targetId) {
      if (!this.graphData) return { nodes: new Set(), edges: new Set() };
      
      const journeyNodes = new Set();
      const journeyEdges = new Set();
      
      // 1. Identify Entry Points
      const entryPoints = Object.entries(this.graphData.file_map)
        .filter(([id, data]) => {
           const n = data.name.toLowerCase();
           return n.includes('main') || n.includes('app.vue') || n.includes('router');
        })
        .map(([id]) => parseInt(id));

      const forwardAdj = {}; // from -> [to]
      const backwardAdj = {}; // to -> [from]
      this.graphData.connections.forEach(conn => {
        if (!forwardAdj[conn.from_id]) forwardAdj[conn.from_id] = [];
        forwardAdj[conn.from_id].push(conn.to_id);
        
        if (!backwardAdj[conn.to_id]) backwardAdj[conn.to_id] = [];
        backwardAdj[conn.to_id].push({ from: conn.from_id, edge: conn });
      });

      // 2. Multi-source BFS from all Entry Points to calculate minimum distances
      const distances = {};
      const queue = [];
      entryPoints.forEach(ep => {
        distances[ep] = 0;
        queue.push(ep);
      });

      while (queue.length > 0) {
        const curr = queue.shift();
        const neighbors = forwardAdj[curr] || [];
        neighbors.forEach(next => {
          if (distances[next] === undefined) {
            distances[next] = distances[curr] + 1;
            queue.push(next);
          }
        });
      }

      // 3. Backtrack from targetId along shortest paths
      if (distances[targetId] === undefined) return { nodes: new Set([targetId]), edges: new Set() };

      const backtrackQueue = [targetId];
      journeyNodes.add(targetId);
      const visited = new Set();

      while (backtrackQueue.length > 0) {
        const curr = backtrackQueue.shift();
        if (visited.has(curr)) continue;
        visited.add(curr);

        const parents = backwardAdj[curr] || [];
        parents.forEach(p => {
          // Only follow the edge if it leads to a node closer to the roots
          if (distances[p.from] !== undefined && distances[p.from] < distances[curr]) {
            journeyNodes.add(p.from);
            journeyEdges.add(p.edge);
            backtrackQueue.push(p.from);
          }
        });
      }
      
      return { nodes: journeyNodes, edges: journeyEdges };
    },
    getIsolationOptions() {
      return {
        physics: { enabled: false },
        layout: {
          hierarchical: {
            enabled: true,
            direction: 'LR',
            sortMethod: 'directed',
            levelSeparation: 350,
            nodeSpacing: 250,
            treeSpacing: 250,
            blockShifting: true,
            edgeMinimization: true,
            parentCentralization: true
          }
        },
        edges: {
          smooth: {
            enabled: true,
            type: 'cubicBezier',
            forceDirection: 'horizontal',
            roundness: 0.5
          }
        }
      };
    },
    isolateUserJourney(nodeId) {
      this.isIsolationActive = true;
      this.isolatedNodeId = nodeId;
      
      // Apply clean hierarchical layout options
      if (this.network) {
        this.network.setOptions(this.getIsolationOptions());
      }
      
      this.focusEcosystem(nodeId);
    },
    exitIsolation() {
      this.isIsolationActive = false;
      this.isolatedNodeId = null;
      
      // Restore physics exploration options
      if (this.network) {
        this.network.setOptions({
          ...this.options,
          layout: { hierarchical: { enabled: false } }
        });
      }
      
      if (this.selectedNode) {
        this.focusEcosystem(this.selectedNode.id);
      }
    },
    toggleLayout() {
      this.layoutMode = this.layoutMode === 'physics' ? 'hierarchy' : 'physics';
      const newOptions = { ...this.options };
      
      if (this.layoutMode === 'hierarchy') {
        newOptions.physics = { enabled: false };
        newOptions.layout = {
          hierarchical: {
            direction: 'UD',
            sortMethod: 'directed',
            nodeSpacing: 150,
            levelSeparation: 200
          }
        };
      } else {
        newOptions.layout = { hierarchical: { enabled: false } };
        newOptions.physics = this.options.physics;
      }
      
      if (this.network) {
        this.network.setOptions(newOptions);
        this.resetCamera();
      }
    },
    activateMindmap() {
      this.viewMode = 'mindmap';
      // Reset to collapsed state on each activation
      this.expandedMindmapNodes = [];
      this.$nextTick(() => {
        this.mmBuildTree();
        this.mmLayout();
      });
    },
    
    // --- NotebookLM-style Mindmap Engine ---
    
    mmBranchColors() {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      return isDark ? [
        { bg: 'rgba(129, 140, 248, 0.18)', border: '#818cf8', line: '#818cf8' },
        { bg: 'rgba(52, 211, 153, 0.18)', border: '#34d399', line: '#34d399' },
        { bg: 'rgba(251, 191, 36, 0.18)', border: '#fbbf24', line: '#fbbf24' },
        { bg: 'rgba(244, 114, 182, 0.18)', border: '#f472b6', line: '#f472b6' },
        { bg: 'rgba(167, 139, 250, 0.18)', border: '#a78bfa', line: '#a78bfa' },
        { bg: 'rgba(96, 165, 250, 0.18)', border: '#60a5fa', line: '#60a5fa' },
        { bg: 'rgba(248, 113, 113, 0.18)', border: '#f87171', line: '#f87171' },
        { bg: 'rgba(45, 212, 191, 0.18)', border: '#2dd4bf', line: '#2dd4bf' },
      ] : [
        { bg: '#eef2ff', border: '#6366f1', line: '#6366f1' },
        { bg: '#ecfdf5', border: '#10b981', line: '#10b981' },
        { bg: '#fffbeb', border: '#f59e0b', line: '#f59e0b' },
        { bg: '#fdf2f8', border: '#ec4899', line: '#ec4899' },
        { bg: '#f5f3ff', border: '#8b5cf6', line: '#8b5cf6' },
        { bg: '#eff6ff', border: '#3b82f6', line: '#3b82f6' },
        { bg: '#fef2f2', border: '#ef4444', line: '#ef4444' },
        { bg: '#f0fdfa', border: '#14b8a6', line: '#14b8a6' },
      ];
    },
    
    mmBuildTree() {
      if (!this.rawNodes || this.rawNodes.length === 0) return;
      
      const nodeMap = {};
      this.rawNodes.forEach(n => { nodeMap[n.id] = { ...n, children: [] }; });
      
      const childSet = new Set();
      this.rawEdges.forEach(e => {
        if (nodeMap[e.from] && nodeMap[e.to]) {
          nodeMap[e.from].children.push(nodeMap[e.to]);
          childSet.add(e.to);
        }
      });
      
      // Find root nodes (not imported by anything, or entry points)
      let roots = this.rawNodes.filter(n => !childSet.has(n.id));
      if (roots.length === 0) roots = [this.rawNodes[0]];
      
      // Create a virtual root representing the project
      this.mmTree = {
        id: '__root__',
        label: '📁 Project',
        children: roots.map(r => nodeMap[r.id]),
        isVirtualRoot: true
      };
      
      this.mmNodeMap = nodeMap;
      
      // Initialize expanded: only root is expanded
      if (this.expandedMindmapNodes.length === 0) {
        this.expandedMindmapNodes = ['__root__'];
      }
    },
    
    mmLayout() {
      if (!this.mmTree) return;
      
      const NODE_H = 48;
      const NODE_W_BASE = 11;
      const NODE_W_PAD = 56;
      const LEVEL_GAP = 320;
      const SIBLING_GAP = 22;
      const colors = this.mmBranchColors();
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      
      const renderedNodes = [];
      const lines = [];
      
      // Calculate the subtree height (number of visible leaf slots)
      const getSubtreeSlots = (node, path = new Set()) => {
        if (path.has(node.id)) return 1; // Prevent cycle
        const isExpanded = this.expandedMindmapNodes.includes(node.id);
        if (!node.children || node.children.length === 0 || !isExpanded) return 1;
        
        path.add(node.id);
        let total = 0;
        node.children.forEach(c => { total += getSubtreeSlots(c, path); });
        path.delete(node.id);
        return total;
      };
      
      const totalSlots = getSubtreeSlots(this.mmTree);
      const totalHeight = totalSlots * (NODE_H + SIBLING_GAP);
      
      // Recursively position nodes
      const layoutNode = (node, depth, yStart, yEnd, branchColorIdx, path = new Set()) => {
        const nodeW = Math.max(160, node.label.length * NODE_W_BASE + NODE_W_PAD);
        const x = 200 + depth * LEVEL_GAP;
        const y = (yStart + yEnd) / 2;
        
        const isExpanded = this.expandedMindmapNodes.includes(node.id);
        const hasChildren = node.children && node.children.length > 0;
        const hasIssues = this.getFileIssueCount ? this.getFileIssueCount(node.label) > 0 : false;
        const colorIdx = branchColorIdx % colors.length;
        const color = colors[colorIdx];
        
        const isRoot = node.isVirtualRoot;
        
        renderedNodes.push({
          id: node.id,
          label: node.label,
          isRoot,
          hasChildren,
          isExpanded,
          hasIssues,
          childCount: hasChildren ? node.children.length : 0,
          style: {
            position: 'absolute',
            left: `${x}px`,
            top: `${y - (isRoot ? 30 : NODE_H / 2)}px`,
            width: isRoot ? '240px' : `${nodeW}px`,
            height: isRoot ? '60px' : `${NODE_H}px`,
            background: isRoot
              ? (isDark ? 'linear-gradient(135deg, #312e81 0%, #4338ca 100%)' : 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)')
              : (hasIssues ? (isDark ? 'rgba(239,68,68,0.15)' : '#fef2f2') : color.bg),
            border: isRoot ? '3px solid rgba(255,255,255,0.2)' : `2px solid ${hasIssues ? '#ef4444' : color.border}`,
            borderRadius: isRoot ? '28px' : '999px',
            color: isRoot ? '#fff' : (isDark ? '#e2e8f0' : '#1e293b'),
            zIndex: isRoot ? 10 : 5,
            boxShadow: isRoot ? '0 8px 32px rgba(79,70,229,0.35)' : '',
          },
          _x: x,
          _y: y,
          _w: isRoot ? 240 : nodeW,
          _color: color
        });
        
        if (hasChildren && isExpanded && !path.has(node.id)) {
          path.add(node.id);
          let childYStart = yStart;
          node.children.forEach((child, ci) => {
            const childSlots = getSubtreeSlots(child);
            const childYEnd = childYStart + childSlots * (NODE_H + SIBLING_GAP);
            const childBranchColor = depth === 0 ? ci : branchColorIdx;
            
            const childResult = layoutNode(child, depth + 1, childYStart, childYEnd, childBranchColor, path);
            
            // Draw bezier curve from parent to child
            const px = x + (isRoot ? 240 : nodeW);
            const py = y;
            const cx = childResult.x;
            const cy = childResult.y;
            const midX = (px + cx) / 2;
            
            const childColor = colors[childBranchColor % colors.length];
            
            lines.push({
              d: `M ${px} ${py} C ${midX} ${py}, ${midX} ${cy}, ${cx} ${cy}`,
              color: childColor.line,
              width: depth === 0 ? 3.5 : 2.5,
              opacity: depth === 0 ? 0.65 : 0.45
            });
            
            childYStart = childYEnd;
          });
          path.delete(node.id);
        }
        
        return { x, y, w: isRoot ? 240 : nodeW };
      };
      
      layoutNode(this.mmTree, 0, 0, totalHeight, 0);
      
      // Calculate SVG bounds
      let maxX = 0, maxY = 0;
      renderedNodes.forEach(n => {
        const right = n._x + n._w + 100;
        const bottom = n._y + NODE_H + 50;
        if (right > maxX) maxX = right;
        if (bottom > maxY) maxY = bottom;
      });
      
      this.mmSvgWidth = maxX + 200;
      this.mmSvgHeight = maxY + 200;
      this.mmRenderedNodes = renderedNodes;
      this.mmLines = lines;
      
      // Auto-fit on first render
      this.$nextTick(() => this.resetMindmapCamera());
    },
    
    mmToggleNode(nodeId) {
      const idx = this.expandedMindmapNodes.indexOf(nodeId);
      if (idx > -1) {
        // Collapse: remove this node and all descendants from expanded
        const toRemove = new Set();
        const collectDescendants = (nid) => {
          if (toRemove.has(nid)) return;
          toRemove.add(nid);
          const node = nid === '__root__' ? this.mmTree : (this.mmNodeMap && this.mmNodeMap[nid]);
          if (node && node.children) {
            node.children.forEach(c => collectDescendants(c.id));
          }
        };
        collectDescendants(nodeId);
        this.expandedMindmapNodes = this.expandedMindmapNodes.filter(id => !toRemove.has(id));
      } else {
        this.expandedMindmapNodes.push(nodeId);
      }
      this.mmLayout();
    },
    
    expandAllMindmap() {
      if (!this.mmTree) return;
      const allIds = new Set();
      const collect = (node) => {
        if (allIds.has(node.id)) return;
        allIds.add(node.id);
        if (node.children) node.children.forEach(collect);
      };
      collect(this.mmTree);
      this.expandedMindmapNodes = Array.from(allIds);
      this.mmLayout();
    },
    
    collapseAllMindmap() {
      this.expandedMindmapNodes = ['__root__'];
      this.mmLayout();
    },
    
    // Pan & zoom
    mmStartDrag(e) {
      this.mmDragging = true;
      this.mmDragStartX = e.clientX - this.mmPanX;
      this.mmDragStartY = e.clientY - this.mmPanY;
    },
    mmDrag(e) {
      if (!this.mmDragging) return;
      this.mmPanX = e.clientX - this.mmDragStartX;
      this.mmPanY = e.clientY - this.mmDragStartY;
    },
    mmEndDrag() {
      this.mmDragging = false;
    },
    mmZoom(e) {
      const delta = e.deltaY > 0 ? -0.08 : 0.08;
      this.mmScale = Math.min(3, Math.max(0.15, this.mmScale + delta));
    },
    
    resetMindmapCamera() {
      if (!this.$refs.mindmapCanvas) return;
      const container = this.$refs.mindmapCanvas;
      const cw = container.clientWidth;
      const ch = container.clientHeight;
      if (this.mmSvgWidth <= 0 || this.mmSvgHeight <= 0) return;
      
      const scaleX = cw / this.mmSvgWidth;
      const scaleY = ch / this.mmSvgHeight;
      this.mmScale = Math.min(scaleX, scaleY, 1) * 0.85;
      this.mmPanX = (cw - this.mmSvgWidth * this.mmScale) / 2;
      this.mmPanY = (ch - this.mmSvgHeight * this.mmScale) / 2;
    }
  }
};
</script>

<style scoped>
.graph-root {
  height: calc(100vh - var(--topbar-height) - 3rem);
  min-height: 600px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  position: relative;
}

.graph-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-overlay);
  backdrop-filter: blur(10px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-icon {
  color: var(--accent-primary);
}

.header-titles h3 {
  font-size: 1.1rem;
  margin: 0;
  color: var(--text-primary);
  font-weight: 700;
}

.header-titles p {
  font-size: 0.8rem;
  margin: 2px 0 0 0;
  color: var(--text-tertiary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.view-toggle {
  display: flex;
  background: var(--bg-inset);
  padding: 4px;
  border-radius: var(--radius-md);
}

.btn-toggle {
  background: transparent;
  border: none;
  padding: 0.4rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.btn-toggle.active {
  background: var(--bg-surface);
  color: var(--accent-primary);
  box-shadow: var(--shadow-sm);
}

.graph-container {
  flex: 1;
  position: relative;
  min-height: 0;
  display: flex;
}

/* Redesigned Explorer Layout */
.explorer-layout {
  display: flex;
  width: 100%;
  height: 100%;
  background: var(--bg-surface);
}

.explorer-sidebar {
  width: 320px;
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  background: var(--bg-inset);
}

.sidebar-header {
  padding: 1rem;
  border-bottom: 1px solid var(--border-subtle);
}

.search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  color: var(--text-tertiary);
}

.search-input.full-width {
  width: 100%;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 0.5rem 1rem 0.5rem 2.25rem;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.search-input:focus {
  border-color: var(--accent-primary);
  outline: none;
  box-shadow: 0 0 0 3px var(--accent-primary-subtle);
}

.explorer-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
}



.empty-list {
  padding: 1rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.85rem;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.1s ease;
}

.file-item:hover {
  background: var(--bg-overlay);
  color: var(--text-primary);
}

.file-item.active {
  background: var(--accent-primary-subtle);
  color: var(--accent-primary);
  font-weight: 600;
}

.file-icon {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.file-item.active .file-icon {
  color: var(--accent-primary);
}

.file-name {
  font-size: 0.85rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.explorer-main {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  background: radial-gradient(circle at center, var(--bg-inset) 0%, var(--bg-surface) 100%);
}

.empty-canvas-state {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--text-secondary);
  gap: 1rem;
}

.empty-icon-wrap {
  background: var(--bg-inset);
  padding: 1.5rem;
  border-radius: 50%;
  color: var(--text-tertiary);
}

.empty-canvas-state h4 {
  font-size: 1.2rem;
  margin: 0;
  color: var(--text-primary);
}

.empty-canvas-state p {
  font-size: 0.9rem;
  max-width: 300px;
}

.canvas-wrapper {
  position: absolute;
  inset: 0;
  display: flex;
}

.canvas-center {
  flex: 1;
  position: relative;
  height: 100%;
}

.graph-canvas {
  width: 100%;
  height: 100%;
}

.canvas-toolbar {
  position: absolute;
  top: 1rem;
  left: 1rem;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--bg-overlay);
  backdrop-filter: blur(10px);
  padding: 0.5rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-sm);
}

.node-title-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.badge-label {
  font-size: 0.65rem;
  font-weight: 800;
  color: var(--accent-primary);
  background: var(--accent-primary-subtle);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
}

.node-title-badge strong {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.btn-ghost {
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary);
  padding: 0.3rem 0.6rem;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.btn-ghost:hover {
  background: var(--bg-inset);
  color: var(--text-primary);
}

/* Docked Detail Panel */
.detail-panel {
  width: 320px;
  background: var(--bg-surface);
  border-left: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  z-index: 10;
  overflow-y: auto;
}

.panel-section {
  padding: 1.25rem;
  border-bottom: 1px solid var(--border-subtle);
}

.panel-section:last-child {
  border-bottom: none;
}

.panel-section label {
  display: block;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-tertiary);
  margin-bottom: 0.75rem;
  letter-spacing: 0.05em;
}

.connection-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.connection-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-secondary);
  padding: 0.4rem;
  background: var(--bg-inset);
  border-radius: var(--radius-sm);
}

.detail-panel .connection-item { background: rgba(245, 158, 11, 0.05); color: #f59e0b; border-left: 3px solid #f59e0b; }
.detail-panel .connection-item.dependency { background: rgba(14, 165, 233, 0.05); color: #0ea5e9; border-left: 3px solid #0ea5e9; }

.empty-text {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  margin: 0;
}

/* AI Architecture Styles */
.ai-view-container { width: 100%; height: 100%; overflow-y: auto; padding: 2rem; background: var(--bg-surface); }
.ai-content { max-width: 1000px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem; }
.ai-overview { text-align: center; padding: 3rem 2rem; background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.05) 100%); border: 1px solid var(--border-subtle); border-radius: var(--radius-xl); position: relative; overflow: hidden; }
.pulse-glow::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--accent-primary), transparent); opacity: 0.6; }
.ai-badge { display: inline-block; padding: 0.3rem 0.8rem; background: var(--accent-primary-subtle); color: var(--accent-primary); font-size: 0.75rem; font-weight: 800; border-radius: 20px; letter-spacing: 0.1em; margin-bottom: 1rem; border: 1px solid var(--accent-primary-glow); }
.ai-overview h2 { font-size: 1.8rem; margin-bottom: 1rem; font-weight: 700; color: var(--text-primary); }
.ai-overview p { font-size: 1.1rem; color: var(--text-secondary); max-width: 700px; margin: 0 auto; line-height: 1.6; }
.ai-grid { display: grid; grid-template-columns: 1fr; gap: 2rem; }
.section-title { font-size: 1.2rem; font-weight: 700; color: var(--text-primary); margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem; }
.layers-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
.layer-card { background: var(--bg-overlay); border: 1px solid var(--border-default); border-radius: var(--radius-lg); padding: 1.5rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.layer-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); border-color: var(--accent-primary-glow); }
.layer-card h4 { font-size: 1.1rem; color: var(--accent-primary); margin: 0 0 0.75rem 0; }
.layer-card p { font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 1.5rem; }
.file-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.tag-file { font-family: var(--font-mono); font-size: 0.75rem; padding: 0.25rem 0.5rem; background: var(--bg-inset); color: var(--text-secondary); border: 1px solid var(--border-subtle); border-radius: 4px; }
.workflows-list { display: flex; flex-direction: column; gap: 1rem; }
.workflow-card { display: flex; gap: 1.5rem; background: var(--bg-overlay); border: 1px solid var(--border-default); border-left: 4px solid var(--accent-primary); border-radius: var(--radius-lg); padding: 1.5rem; }
.workflow-icon { color: var(--accent-primary); background: var(--accent-primary-subtle); padding: 0.75rem; border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; height: max-content; }
.workflow-content h4 { margin: 0 0 0.5rem 0; font-size: 1.05rem; color: var(--text-primary); }
.workflow-content p { margin: 0; font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5; }
.ai-warning, .ai-pending { display: flex; align-items: center; justify-content: center; gap: 1rem; padding: 3rem; text-align: center; color: var(--text-secondary); }
.ai-warning { color: var(--accent-danger); }
.graph-loading, .graph-error { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1.5rem; z-index: 10; background: var(--bg-surface); text-align: center; padding: 2rem; }
.graph-error svg { color: var(--accent-danger); width: 48px; height: 48px; }
.graph-error p { color: var(--text-secondary); font-size: 0.95rem; max-width: 300px; }
.spinner { width: 32px; height: 32px; border: 3px solid var(--border-subtle); border-top-color: var(--accent-primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
.circular-warning { display: flex; align-items: center; gap: 0.4rem; padding: 0.2rem 0.6rem; background: var(--accent-danger-subtle); color: var(--accent-danger); border-radius: 4px; font-size: 0.65rem; font-weight: 800; border: 1px solid rgba(239, 68, 68, 0.4); }
.circular-panel { border-bottom: 3px solid var(--accent-danger); background: rgba(239, 68, 68, 0.05); }
.red-label { color: var(--accent-danger) !important; }
.warning-text { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
.cycle-display { display: flex; flex-direction: column; gap: 0.5rem; }
.cycle-path { font-family: var(--font-mono); font-size: 0.7rem; color: var(--accent-danger); padding: 0.4rem; background: rgba(239, 68, 68, 0.1); border-radius: 4px; border: 1px dashed rgba(239, 68, 68, 0.3); }

.pulse-red { animation: pulseRed 2s infinite; }
@keyframes pulseRed { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); } 70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

.isolation-banner {
  margin-left: auto;
  margin-right: 1.5rem;
  padding: 0.4rem 0.75rem;
  background: var(--bg-surface);
  border: 1px solid var(--accent-primary-glow);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: var(--shadow-sm);
  z-index: 20;
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-primary);
}

.banner-content svg {
  color: var(--accent-primary);
}

.btn-exit {
  background: var(--accent-primary);
  color: white;
  border: none;
  border-radius: var(--radius-full);
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-exit:hover {
  background: var(--accent-primary-hover);
  transform: scale(1.05);
}

.isolation-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent-primary);
  padding: 0.5rem;
  background: var(--accent-primary-subtle);
  border-radius: var(--radius-md);
  justify-content: center;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: var(--accent-primary);
  border-radius: 50%;
  animation: pulse-purple 2s infinite;
}

.pulse-purple { animation: pulsePurple 2s infinite; }
@keyframes pulsePurple { 0% { box-shadow: 0 0 0 0 rgba(168, 85, 247, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(168, 85, 247, 0); } 100% { box-shadow: 0 0 0 0 rgba(168, 85, 247, 0); } }

@keyframes spin { to { transform: rotate(360deg); } }

/* ===== NotebookLM-style Mindmap ===== */
.mm-toolbar {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-overlay, rgba(255,255,255,0.85));
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  padding: 6px 10px;
  border-radius: 12px;
  border: 1px solid var(--border-subtle, rgba(0,0,0,0.08));
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.mm-toolbar-title {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-primary);
  padding: 0 8px;
  letter-spacing: -0.01em;
}
.mm-toolbar-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: 1px solid var(--border-subtle, rgba(0,0,0,0.1));
  border-radius: 8px;
  padding: 5px 10px;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}
.mm-toolbar-btn:hover {
  background: var(--accent-primary-subtle, rgba(99,102,241,0.08));
  color: var(--accent-primary, #6366f1);
  border-color: var(--accent-primary, #6366f1);
}

.mm-canvas {
  width: 100%;
  height: 100%;
  cursor: grab;
  position: relative;
  overflow: hidden;
}
.mm-canvas:active {
  cursor: grabbing;
}

.mm-transform {
  position: absolute;
  top: 0;
  left: 0;
  will-change: transform;
}

.mm-svg {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

/* Nodes */
.mm-node {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 18px;
  cursor: pointer;
  font-family: 'Inter', -apple-system, sans-serif;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  white-space: nowrap;
  user-select: none;
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.mm-node:hover {
  transform: scale(1.06);
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  z-index: 10 !important;
}

/* Root node */
.mm-node-root {
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  box-shadow: 0 4px 24px rgba(99,102,241,0.25);
}
.mm-node-root:hover {
  box-shadow: 0 6px 32px rgba(99,102,241,0.35);
}

/* Leaf nodes */
.mm-node-leaf {
  cursor: default;
  opacity: 0.85;
}
.mm-node-leaf:hover {
  opacity: 1;
  transform: scale(1.04);
}

/* Issue nodes */
.mm-node-issue {
  animation: mmPulseIssue 2.5s ease-in-out infinite;
}
@keyframes mmPulseIssue {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.15); }
  50% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
}

/* Node label */
.mm-node-label {
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

/* Child count badge */
.mm-node-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  background: rgba(0,0,0,0.1);
  font-size: 0.65rem;
  font-weight: 800;
  padding: 0 5px;
  flex-shrink: 0;
}
.mm-node-root .mm-node-badge {
  background: rgba(255,255,255,0.25);
}

/* ===== Refactor Playground & Dashboard Styles ===== */
.refactor-dashboard {
  background: var(--bg-overlay, var(--bg-surface));
  border-left: 1px solid var(--border-subtle);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.15);
}

.dashboard-header {
  padding: 1.25rem;
}

.header-badge {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  background: rgba(249, 115, 22, 0.15);
  color: #f97316;
  font-size: 0.65rem;
  font-weight: 800;
  border-radius: var(--radius-full, 99px);
  border: 1px solid rgba(249, 115, 22, 0.3);
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.pulse-orange {
  animation: pulseOrange 2s infinite;
}

@keyframes pulseOrange {
  0% { box-shadow: 0 0 0 0 rgba(249, 115, 22, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(249, 115, 22, 0); }
  100% { box-shadow: 0 0 0 0 rgba(249, 115, 22, 0); }
}

.dashboard-header h3 {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.dashboard-header .subtitle {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  margin: 4px 0 0 0;
  line-height: 1.4;
}

.risk-gauge-section {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1.5rem 1.25rem;
  background: radial-gradient(circle at center, rgba(249, 115, 22, 0.03) 0%, transparent 80%);
}

.risk-gauge-container {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.progress-ring {
  transform: rotate(-90deg);
}

.progress-ring-circle {
  transition: stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.risk-gauge-value {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-number {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.1;
}

.score-rating {
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.05em;
  margin-top: 2px;
}

.risk-none { color: #10b981; }
.risk-low { color: #3b82f6; }
.risk-medium { color: #f59e0b; }
.risk-high { color: #ef4444; }

.metrics-section {
  padding: 1.25rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.metric-card {
  background: var(--bg-inset);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md, 8px);
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.metric-val {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.2;
}

.metric-lbl {
  font-size: 0.65rem;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.text-orange { color: #f97316; }
.text-amber { color: #f59e0b; }
.text-red { color: #ef4444; }
.text-green { color: #10b981; }
.text-blue { color: #3b82f6; }

.description-small {
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin: 0 0 0.75rem 0;
  line-height: 1.4;
}

.affected-list {
  max-height: 180px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding-right: 4px;
}

.affected-list-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.6rem;
  background: var(--bg-inset);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm, 4px);
  width: 100%;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--text-secondary);
}

.affected-list-item:hover {
  background: rgba(249, 115, 22, 0.08);
  border-color: #f97316;
  color: var(--text-primary);
}

.affected-list-item .item-icon {
  color: var(--text-tertiary);
  transition: color 0.2s ease;
}

.affected-list-item:hover .item-icon {
  color: #f97316;
}

.affected-list-item .item-name {
  font-size: 0.8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.entry-tag {
  font-size: 0.6rem;
  font-weight: 800;
  color: #a855f7;
  background: rgba(168, 85, 247, 0.12);
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  letter-spacing: 0.02em;
}

.checklist-items {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 0.5rem;
}

.checklist-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  cursor: pointer;
  user-select: none;
}

.checklist-checkbox {
  margin-top: 0.15rem;
  accent-color: #f97316;
  cursor: pointer;
}

.checklist-text {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.4;
  transition: color 0.2s ease;
}

.checklist-item:hover .checklist-text {
  color: var(--text-primary);
}

.strike-through-done {
  text-decoration: line-through;
  opacity: 0.6;
  color: var(--text-tertiary) !important;
}

/* Tabbed selector styling */
.analysis-mode-selector {
  display: flex;
  background: var(--bg-inset);
  padding: 2px;
  border-radius: var(--radius-sm, 4px);
  border: 1px solid var(--border-subtle);
}

.btn-mode {
  background: transparent;
  border: none;
  padding: 0.3rem 0.75rem;
  border-radius: var(--radius-sm, 4px);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn-mode:hover {
  color: var(--text-secondary);
}

.btn-mode.active {
  background: var(--bg-surface);
  color: #f97316;
  box-shadow: var(--shadow-sm);
}

</style>
