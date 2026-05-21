<template>
  <div class="report-root">

    <!-- Loading / Error States -->
    <transition name="fade" mode="out-in">
      <div v-if="loading" class="state-panel" key="loading">
        <div class="state-spinner"></div>
        <p class="state-text">Generating AI insights...</p>
      </div>
      <div v-else-if="error" class="state-panel state-error" key="error">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        <p class="state-text">{{ error }}</p>
      </div>
    </transition>

    <!-- Component Error Boundary Fallback -->
    <div v-if="componentError" class="state-panel state-error" key="component-error">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
      <p class="state-text">{{ componentError }}</p>
      <button class="btn btn-sm btn-secondary" @click="componentError = null; fetchReport()">Retry</button>
    </div>

    <div v-if="reportData && !loading && !componentError" class="dashboard">
      <!-- Warning Banner -->
      <div v-if="reportData.audit_status === 'partial'" class="analysis-warning">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
        <div>
          <strong>Partial Audit</strong> — AI Analysis encountered a quota limit or error. Full insights may not be available.
          <div v-if="reportData.ai_error" class="error-detail" style="margin-top: 0.5rem; color: var(--accent-danger); font-family: var(--font-mono); font-size: 0.75rem;">
            Error: {{ reportData.ai_error }}
          </div>
        </div>
      </div>

      <!-- ═══ OVERVIEW VIEW ═══ -->
      <div v-if="activeView === 'overview'" class="view-overview" style="animation:fadeIn .3s var(--ease-out)">
        <!-- Quality Gate -->
        <div class="quality-gate" :class="qualityGateClass">
          <div class="quality-gate-icon">
            <svg v-if="reportData.overall_score >= 70" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </div>
          <div class="quality-gate-text">
            <span class="quality-gate-label">Quality Gate</span>
            <span class="quality-gate-status">{{ reportData.overall_score >= 70 ? 'Passed' : 'Failed' }}</span>
          </div>
          <div class="qg-score-wrap">
            <svg viewBox="0 0 36 36" class="qg-ring">
              <path class="qg-ring-bg" d="M18 2.0845a15.9155 15.9155 0 0 1 0 31.831a15.9155 15.9155 0 0 1 0-31.831"/>
              <path class="qg-ring-fill" :class="scoreColor" :stroke-dasharray="`${reportData.overall_score}, 100`" d="M18 2.0845a15.9155 15.9155 0 0 1 0 31.831a15.9155 15.9155 0 0 1 0-31.831"/>
            </svg>
            <div class="qg-score-num">
              <span class="qg-val">{{ reportData.overall_score }}</span>
              <span class="qg-max">/100</span>
            </div>
          </div>
        </div>

        <!-- KPI Strip -->
        <div class="kpi-strip">
          <div class="kpi-card" v-for="kpi in kpiCards" :key="kpi.label">
            <div class="kpi-icon-wrap" :style="{ background: kpi.iconBg }">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :style="{ color: kpi.iconColor }"><component :is="'g'" v-html="kpi.iconPath"></component></svg>
            </div>
            <div class="kpi-data">
              <span class="kpi-value" :style="{ color: kpi.valueColor || 'var(--text-primary)' }">{{ kpi.value }}</span>
              <span class="kpi-label">{{ kpi.label }}</span>
            </div>
          </div>
        </div>

        <!-- Macro Trends / Architectural Insights -->
        <div v-if="aiArchitecture?.macro_trends?.length" class="section-card architecture-highlights">
          <div class="section-header">
            <div class="header-with-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
              <h3>Architectural Insights</h3>
            </div>
            <span class="badge badge-neutral">Macro Audit</span>
          </div>
          <div class="trends-grid">
            <div v-for="(trend, tIdx) in aiArchitecture.macro_trends" :key="tIdx" class="trend-card">
              <div class="trend-header">
                <span class="trend-severity-badge" :class="'sev-' + trend.severity.toLowerCase()">{{ trend.severity }}</span>
                <span class="trend-type">{{ trend.trend_type }}</span>
              </div>
              <h4>{{ trend.title }}</h4>
              <p>{{ trend.description }}</p>
              <div class="trend-footer">
                <span class="footer-label">Impacted:</span>
                <div class="trend-tags">
                  <span v-for="tag in trend.affected_areas" :key="tag" class="trend-tag">{{ tag }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Severity Distribution -->
        <div class="section-card">
          <div class="section-header">
            <h3>Severity Distribution</h3>
          </div>
          <div class="severity-bar-container">
            <div class="severity-bar">
              <div v-for="seg in severitySegments" :key="seg.label" class="severity-segment" :style="{ width: seg.pct + '%', background: seg.color }" :title="seg.label + ': ' + seg.count"></div>
            </div>
            <div class="severity-legend">
              <div v-for="seg in severitySegments" :key="'l-'+seg.label" class="legend-item">
                <span class="legend-dot" :style="{ background: seg.color }"></span>
                <span class="legend-label">{{ seg.label }}</span>
                <span class="legend-count">{{ seg.count }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Issue Breakdown Table -->
        <div class="section-card">
          <div class="section-header">
            <h3>Issue Breakdown by File</h3>
            <button class="btn-ghost btn-sm" @click="$emit('navigate', 'issues')">View all issues →</button>
          </div>
          <div v-if="safeFilesCount > 0" class="safe-files-summary" style="padding: 1rem 1.5rem; background: var(--surface-2); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; gap: 0.75rem; color: var(--text-secondary);">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent-success)" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <span><strong>{{ safeFilesCount }} files</strong> passed the AI audit and are completely clean.</span>
          </div>

          <div class="table-wrap" v-if="filesWithIssues.length > 0">
            <table class="data-table">
              <thead>
                <tr>
                  <th>File</th>
                  <th class="cell-number">UI Issues</th>
                  <th class="cell-number">AI Issues</th>
                  <th class="cell-number">Total</th>
                  <th>Severity</th>
                  <th>Regression Risk</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="f in filesWithIssues" :key="f._origIdx" class="row-clickable" @click="openFile(f._origIdx)">
                  <td class="cell-primary"><span class="file-name-cell">{{ f.file_name }}</span></td>
                  <td class="cell-number">{{ getUICount(f) }}</td>
                  <td class="cell-number">{{ getAICount(f) }}</td>
                  <td class="cell-number"><strong>{{ getIssueCount(f) }}</strong></td>
                  <td><span class="badge" :class="getSeverityBadge(f)">{{ getSeverityLabel(f) }}</span></td>
                  <td>
                    <span class="badge badge-risk" :class="getRiskAssessment(f).class">
                      {{ getRiskAssessment(f).label }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ═══ ISSUES VIEW ═══ -->
      <div v-if="activeView === 'issues'" class="view-issues" style="animation:fadeIn .3s var(--ease-out)">
          <div v-for="(group, fName) in groupedIssues" :key="fName" class="file-issue-group card card-flat">
            <div class="group-header" @click="toggleGroup(fName)">
              <div class="group-title">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                <span>{{ fName }}</span>
              </div>
              <div class="group-badges">
                <span class="badge badge-danger">{{ group.filter(i => i.is_real_issue).length }} issues</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'rotate-180': expandedGroups[fName] }"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </div>
            </div>
            
            <transition name="slide-fade">
              <div v-if="expandedGroups[fName]" class="group-body">
                <table class="data-table">
                  <thead><tr>
                    <th style="width:40px"></th>
                    <th>Type</th>
                    <th>Rule / Defect</th>
                    <th>Status</th>
                  </tr></thead>
                  <tbody>
                    <template v-for="(issue, idx) in group" :key="fName + idx">
                      <tr class="row-clickable" @click="toggleIssueExpand(fName + idx)">
                        <td><span class="severity-dot" :class="'severity-dot-' + issue._severity"></span></td>
                        <td><span class="badge badge-neutral" style="font-size:0.6rem">{{ issue._source }}</span></td>
                        <td class="cell-mono" style="font-size:0.78rem">
                           <span v-if="issue.wcag_rule" class="badge badge-warning" style="margin-right:0.3rem">{{ issue.wcag_rule }}</span>
                           {{ issue.defect_type || issue.problem || 'UI/UX Issue' }}
                        </td>
                        <td><span class="badge" :class="issue.is_real_issue ? 'badge-danger' : 'badge-success'" style="font-size:0.6rem">{{ issue.is_real_issue ? 'Confirmed' : 'False Positive' }}</span></td>
                      </tr>
                      <tr v-if="expandedIssue === (fName + idx)">
                        <td colspan="4" style="padding:0">
                          <div class="expandable-content">
                            <div class="expand-section">
                              <div class="expand-label">AI Rationale</div>
                              <div class="expand-body" v-html="formatMarkdown(issue.rationale || issue.problem)"></div>
                            </div>
                            <div v-if="issue.is_real_issue && (issue.suggestion || issue.explanation)" class="expand-section expand-fix">
                              <div class="expand-label fix-label">Recommended Fix</div>
                              <div class="expand-body" v-html="formatMarkdown(issue.suggestion || issue.explanation)"></div>
                              <div v-if="issue.fixed_code_snippet || issue.fixed_code" class="code-block" style="margin-top:0.75rem">
                                <div class="code-block-header" style="display:flex; justify-content:space-between; align-items:center;">
                                  <span>Suggested Fix</span>
                                  <button class="btn-ghost btn-sm" @click.stop="copyFix(issue.fixed_code_snippet || issue.fixed_code)" style="padding:0.1rem 0.4rem; font-size:0.7rem; display:flex; align-items:center; gap:0.2rem">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>
                                    Copy Fix
                                  </button>
                                </div>
                                <pre><code>{{ issue.fixed_code_snippet || issue.fixed_code }}</code></pre>
                              </div>
                            </div>
                            <div style="display:flex; gap:0.5rem; margin-top:0.75rem;">
                              <button class="btn-ghost btn-sm" @click="inspectCode(issue)">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                                View in Code
                              </button>
                              <button class="btn-discuss btn-sm" @click.stop="discussWithAI(issue)">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                                Discuss with AI
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    </template>
                  </tbody>
                </table>
              </div>
            </transition>
          </div>
          
          <div v-if="Object.keys(groupedIssues).length === 0" class="empty-state">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            <span>No issues match your filter.</span>
          </div>
      </div>

      <!-- ═══ FILE INSPECTOR VIEW ═══ -->
      <div v-if="activeView === 'files'" class="view-files" style="animation:fadeIn .3s var(--ease-out)">
        <div class="inspector-layout">
          <aside class="file-sidebar card card-flat">
            <div class="fs-head">
              <h4>File Explorer</h4>
              <span class="badge badge-neutral">{{ reportData.files.length }}</span>
            </div>
            <div class="fs-search">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
              <input type="text" v-model="searchQuery" placeholder="Filter..." class="fs-input"/>
            </div>
            <div class="fs-list custom-scrollbar">
              <FileTree 
                :treeData="fileTree" 
                :selectedPath="selectedFile?.file_path"
                @select="selectFileByPath"
              />
            </div>
          </aside>

          <div class="file-workspace">
            <div v-if="selectedFile" class="ws-content card card-flat">
              <div class="ws-header">
                <div class="ws-title-row">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--accent-primary);flex-shrink:0"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                  <h3>{{ selectedFile.file_name }}</h3>
                  <span class="badge" :class="getSeverityBadge(selectedFile)">{{ getIssueCount(selectedFile) }} issues</span>
                  <span class="badge badge-risk" :class="getRiskAssessment(selectedFile).class" style="margin-left: 0.5rem">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" style="margin-right: 2px"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    {{ getRiskAssessment(selectedFile).label }}
                  </span>
                </div>
                <code class="ws-path">{{ selectedFile.file_path }}</code>
              </div>
              <div class="ws-body custom-scrollbar">
                <!-- Integrated Source Code Viewer & Refactor Sandbox -->
                <div class="ws-source-v2" :class="{ 'sandbox-mode': activeViewerTab === 'sandbox' }">
                   <div class="source-header">
                      <div class="viewer-tabs">
                         <button 
                           class="tab-btn" 
                           :class="{ active: activeViewerTab === 'source' }" 
                           @click="activeViewerTab = 'source'"
                         >
                           Source Code
                         </button>
                         <button 
                           class="tab-btn sandbox-tab-btn" 
                           :class="{ active: activeViewerTab === 'sandbox' }" 
                           @click="activeViewerTab = 'sandbox'"
                         >
                           Refactor Sandbox
                           <span class="sandbox-pulse-dot"></span>
                         </button>
                      </div>
                      
                      <div v-if="activeViewerTab === 'source' && selectedIssueLines.length" class="highlight-info">
                         <span class="line-dot"></span> Focus: Line {{ selectedIssueLines[0] }}
                      </div>
                      
                      <div v-if="activeViewerTab === 'sandbox'" class="sandbox-actions-panel">
                         <button 
                           class="btn btn-secondary btn-xs btn-sandbox-action" 
                           @click="applySelectedFix" 
                           :disabled="activeFileIssue === null"
                           title="Apply fix for selected issue into sandbox in-memory"
                         >
                           Apply Selected Fix
                         </button>
                         <button 
                           class="btn btn-secondary btn-xs btn-sandbox-action" 
                           @click="applyAllSuggestions"
                           title="Apply all suggested fixes into sandbox in-memory"
                         >
                           Apply All Suggestions
                         </button>
                         <button 
                           class="btn btn-success btn-xs btn-sandbox-action save-btn" 
                           @click="saveSandboxToFile"
                           title="Save current sandbox changes to the physical file on disk"
                         >
                           Write to File
                         </button>
                         <button 
                           class="btn btn-primary btn-xs btn-sandbox-action build-btn" 
                           @click="runBuildCheck"
                           title="Trigger background Vite compilation check"
                         >
                           <span v-if="buildStatus === 'running'" class="btn-spinner"></span>
                           Run Build Check
                         </button>
                      </div>
                   </div>

                   <!-- Pane Contents -->
                   <div class="viewer-panes-container">
                     <!-- Tab 1: Source Viewer -->
                     <SourceViewer 
                       v-if="activeViewerTab === 'source' && selectedFile"
                       :filePath="selectedFile.file_path"
                       :highlightedLines="selectedIssueLines"
                     />

                     <!-- Tab 2: Refactor Sandbox split view -->
                     <div v-if="activeViewerTab === 'sandbox'" class="sandbox-split-layout">
                       <!-- Left Side: Original Disk State -->
                       <div class="sandbox-side original-side">
                         <div class="side-banner">Original File State (Read-Only)</div>
                         <div class="side-pane-wrapper">
                           <SourceViewer 
                             v-if="selectedFile"
                             :filePath="selectedFile.file_path"
                             :highlightedLines="selectedIssueLines"
                           />
                         </div>
                       </div>
                       
                       <!-- Right Side: Editable Sandbox -->
                       <div class="sandbox-side editor-side">
                         <div class="side-banner editable-banner">Sandbox Playground (Fully Editable)</div>
                         <div class="side-pane-wrapper editable-pane-wrapper">
                           <div class="sandbox-editor-wrapper">
                             <div class="sandbox-bgs-container" ref="editorBgsContainer" aria-hidden="true">
                               <div 
                                 v-for="n in sandboxLineCount" 
                                 :key="'sbg'+n" 
                                 class="sandbox-line-bg"
                                 :class="{ 'hl-bg': selectedIssueLines.includes(n) }"
                               ></div>
                             </div>
                             <div class="sandbox-line-numbers" ref="editorLineNumbers">
                               <div 
                                 v-for="n in sandboxLineCount" 
                                 :key="n" 
                                 class="sandbox-num"
                                 :class="{ 'highlight-line': selectedIssueLines.includes(n) }"
                               >{{ n }}</div>
                             </div>
                             <textarea 
                               class="sandbox-textarea"
                               v-model="sandboxSource"
                               ref="sandboxTextarea"
                               @scroll="syncEditorScroll"
                               spellcheck="false"
                             ></textarea>
                           </div>
                         </div>
                       </div>
                     </div>
                   </div>

                   <!-- Glassmorphic Streaming Terminal Console -->
                   <div v-if="activeViewerTab === 'sandbox'" class="glassmorphic-terminal">
                      <div class="terminal-header">
                         <div class="terminal-title">
                            <span class="terminal-dot red-dot"></span>
                            <span class="terminal-dot yellow-dot"></span>
                            <span class="terminal-dot green-dot"></span>
                            <span class="terminal-label">INTEGRATED BUILD CONSOLE</span>
                         </div>
                         <div class="terminal-status-badge">
                            <span class="status-dot" :class="buildStatus"></span>
                            <span class="status-text">{{ buildStatusText }}</span>
                         </div>
                         <button v-if="buildLogs.length" class="btn-ghost btn-xs btn-clear-console" @click="clearBuildLogs">Clear Logs</button>
                      </div>
                      <div class="terminal-body custom-scrollbar" ref="terminalBody">
                         <div v-if="buildLogs.length === 0" class="terminal-placeholder">
                            Console Idle. Ready to capture and stream Vite/Rollup build logs color-coded by severity.
                         </div>
                         <div v-else v-for="(log, idx) in buildLogs" :key="idx" class="terminal-line" :class="getLogLineClass(log)">
                            {{ log }}
                         </div>
                      </div>
                   </div>
                </div>

                <!-- Issues Panel for Selected File -->
                <div v-if="selectedFileIssues.length > 0" class="ws-issues-panel">
                  <div class="issues-panel-header" @click="issuesPanelOpen = !issuesPanelOpen">
                    <div class="iph-left">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                      <span>Detected Issues</span>
                      <span class="badge badge-danger">{{ selectedFileIssues.length }}</span>
                    </div>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'rotate-180': issuesPanelOpen }"><polyline points="6 9 12 15 18 9"></polyline></svg>
                  </div>
                  <transition name="slide-fade">
                    <div v-if="issuesPanelOpen" class="issues-panel-body custom-scrollbar">
                      <div
                        v-for="(issue, idx) in selectedFileIssues"
                        :key="idx"
                        class="ws-issue-item"
                        :class="{ 'ws-issue-active': activeFileIssue === idx }"
                        @click="focusIssue(issue, idx)"
                      >
                        <div class="ws-issue-top">
                          <span class="severity-dot" :class="'severity-dot-' + (issue.severity || 'medium').toLowerCase()"></span>
                          <span class="ws-issue-type">
                             <span v-if="issue.wcag_rule" class="badge badge-warning" style="margin-right:0.3rem">{{ issue.wcag_rule }}</span>
                             {{ issue.defect_type || issue.problem || 'UI/UX Issue' }}
                          </span>
                          <span class="badge" :class="issue._source === 'UI/A11y' ? 'badge-warning' : 'badge-primary'" style="font-size:0.6rem;margin-left:auto">{{ issue._source }}</span>
                        </div>
                        <p class="ws-issue-rationale">{{ issue.rationale || issue.problem }}</p>
                        <div v-if="activeFileIssue === idx" class="ws-issue-expanded">
                          <div v-if="issue.suggestion || issue.explanation" class="ws-issue-fix">
                            <div class="ws-fix-label">Recommended Fix</div>
                            <p>{{ issue.suggestion || issue.explanation }}</p>
                            <div v-if="issue.fixed_code_snippet || issue.fixed_code" class="code-block" style="margin-top:0.5rem">
                              <div class="code-block-header" style="display:flex; justify-content:space-between; align-items:center;">
                                <span>Suggested Fix</span>
                                <button class="btn-ghost btn-sm" @click.stop="copyFix(issue.fixed_code_snippet || issue.fixed_code)" style="padding:0.1rem 0.4rem; font-size:0.7rem; display:flex; align-items:center; gap:0.2rem">
                                   <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>
                                   Copy Fix
                                </button>
                              </div>
                              <pre><code>{{ issue.fixed_code_snippet || issue.fixed_code }}</code></pre>
                            </div>
                          </div>
                          
                          <!-- VS Code Actions -->
                          <div class="ws-issue-actions" style="display:flex; gap:0.75rem; margin-top:1rem; padding-top:1rem; border-top:1px dashed var(--border-default); flex-wrap:wrap;">
                            <button class="btn btn-secondary btn-sm" @click.stop="openInVsCode(issue)">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                              Open in Editor
                            </button>

                            <button class="btn-discuss btn-sm" @click.stop="discussWithAI({ ...issue, _fileName: selectedFile?.file_name })">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                              Discuss with AI
                            </button>
                          </div>

                          <!-- Blast Radius & Interrelated Files Section -->
                          <div class="ws-issue-impact" style="margin-top:1rem; padding-top:1rem; border-top:1px dashed var(--border-default);">
                            <div class="ws-fix-label" style="color:var(--accent-warning); display:flex; align-items:center; gap:0.4rem; margin-bottom:0.8rem;">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                              Architectural Context & Blast Radius
                            </div>
                            
                            <!-- Upstream Dependencies -->
                            <div v-if="selectedFile.upstream_dependencies && selectedFile.upstream_dependencies.length > 0" style="margin-bottom:1rem;">
                              <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-tertiary); margin-bottom:0.3rem;">Interrelated Files (This file depends on)</div>
                              <div class="impact-tags" style="display:flex; flex-wrap:wrap; gap:0.4rem;">
                                <span v-for="dep in selectedFile.upstream_dependencies" :key="dep" class="badge" style="background:rgba(59, 130, 246, 0.1); color:#60a5fa; border:1px solid rgba(59, 130, 246, 0.2); font-size:11px;">{{ dep }}</span>
                              </div>
                            </div>

                            <!-- Downstream Blast Radius -->
                            <div v-if="selectedFile.downstream_impact && selectedFile.downstream_impact.length > 0">
                              <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-tertiary); margin-bottom:0.3rem;">Downstream Impact (Files that depend on this)</div>
                              <div class="impact-tags" style="display:flex; flex-wrap:wrap; gap:0.4rem;">
                                <span v-for="dep in selectedFile.downstream_impact" :key="dep" class="badge" style="background:rgba(245, 158, 11, 0.1); color:#fbbf24; border:1px solid rgba(245, 158, 11, 0.2); font-size:11px;">{{ dep }}</span>
                              </div>
                            </div>

                            <div v-if="(!selectedFile.upstream_dependencies || selectedFile.upstream_dependencies.length === 0) && (!selectedFile.downstream_impact || selectedFile.downstream_impact.length === 0)" style="font-size:12px; color:var(--text-tertiary); font-style:italic; margin-top:0.5rem;">
                              No cross-file dependencies found. Audit suggests this is an isolated component.
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </transition>
                </div>
                <div v-else-if="selectedFile.visual_simulation?.engineering_health_score === 0" class="ws-clean-badge" style="background: var(--accent-warning-subtle); color: var(--accent-warning); border: 1px dashed var(--accent-warning);">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                  <span>AI analysis unavailable due to server timeout. Please re-run analysis.</span>
                </div>
                <div v-else-if="getIssueCount(selectedFile) === 0" class="ws-clean-badge">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                  <span>No issues detected — this file passed AI audit</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeView === 'chat'" class="view-chat" style="animation:fadeIn .3s var(--ease-out); height: 100%; display: flex; flex-direction: column;">
        <ChatWidget :activeFile="selectedFile" :workspacePath="workspacePath" :allFiles="reportData.files" :injectedIssue="chatIssue" :allIssues="confirmedIssues" />
      </div>

      <!-- ═══ FIX STATUS TOAST ═══ -->
      <transition name="slide-up">
        <div v-if="toast.show" class="fix-toast" :class="'fix-toast-' + toast.type" key="toast">
           <div class="fix-toast-icon">
              <svg v-if="toast.type === 'success'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>
              <svg v-else-if="toast.type === 'error'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
              <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
           </div>
           <div class="fix-toast-msg">{{ toast.msg }}</div>
           <button class="fix-toast-close" @click="closeToast">×</button>
        </div>
      </transition>

    </div>
  </div>
</template>

<script>
import axios from "axios";
import SourceViewer from "./SourceViewer.vue";
import FileTree from "./FileTree.vue";
import ChatWidget from "./ChatWidget.vue";

export default {
  name: "AIReport",
  components: { SourceViewer, FileTree, ChatWidget },
  props: { 
    activeView: { type: String, default: 'overview' },
    selectedReportId: { type: String, default: null },
    chatIssue: { type: Object, default: null }
  },
  emits: ['navigate', 'discuss-issue'],
  data() {
    return { 
      reportData: null, 
      loading: true, 
      error: null, 
      componentError: null,
      selectedFileIndex: 0, 
      searchQuery: '', 
      issueFilter: 'all', 
      issueSearch: '', 
      expandedIssue: null,
      expandedGroups: {},
      selectedIssueLines: [],
      aiArchitecture: null,
      issuesPanelOpen: true,
      activeFileIssue: null,
      
      // Sandbox Refactor state
      activeViewerTab: 'source',
      sandboxSource: '',
      sandboxOriginal: '',
      buildJobId: null,
      buildStatus: 'idle',
      buildLogs: [],
      sseSource: null,
      toast: { show: false, msg: '', type: 'success' }
    };
  },
  computed: {
    filesWithIssues() {
      if (!this.reportData?.files) return [];
      return this.reportData.files
        .map((f, idx) => ({ ...f, _origIdx: idx }))
        .filter(f => this.getIssueCount(f) > 0);
    },
    safeFilesCount() {
      if (!this.reportData?.files) return 0;
      return this.reportData.files.length - this.filesWithIssues.length;
    },
    workspacePath() {
       return new URLSearchParams(window.location.search).get('path') || 'Your Project Workspace';
    },
    selectedFile() {
      if (this.reportData?.files?.length > 0) return this.reportData.files[this.selectedFileIndex];
      return null;
    },
    selectedFileIssues() {
      const f = this.selectedFile;
      if (!f) return [];
      const issues = [];
      (f.ui_accessibility_analysis || []).forEach(i => {
        if (i.is_real_issue) issues.push({ ...i, _source: 'UI/A11y' });
      });
      (f.ai_analysis || []).forEach(i => {
        if (i.is_real_issue) issues.push({ ...i, _source: 'AI Logic' });
      });
      return issues;
    },
    scoreColor() {
      const s = this.reportData?.overall_score ?? 0;
      if (s >= 90) return 'ring-success'; if (s >= 70) return 'ring-good'; if (s >= 50) return 'ring-warning'; return 'ring-danger';
    },
    qualityGateClass() {
      const s = this.reportData?.overall_score ?? 0;
      if (s >= 70) return 'quality-gate-passed'; if (s >= 50) return 'quality-gate-warning'; return 'quality-gate-failed';
    },
    kpiCards() {
      const d = this.reportData;
      return [
        { label: 'Files Scanned', value: d.files_analyzed, iconPath: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline>', iconBg: 'var(--accent-primary-subtle)', iconColor: 'var(--accent-primary)' },
        { label: 'Confirmed Issues', value: d.total_real_issues, valueColor: 'var(--accent-danger)', iconPath: '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>', iconBg: 'var(--accent-danger-subtle)', iconColor: 'var(--accent-danger)' },
        { label: 'False Positives', value: d.total_false_positives, valueColor: 'var(--accent-success)', iconPath: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>', iconBg: 'var(--accent-success-subtle)', iconColor: 'var(--accent-success)' },
        { label: 'Issue Density', value: d.files_analyzed > 0 ? (d.total_real_issues / d.files_analyzed).toFixed(1) : '0', iconPath: '<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>', iconBg: 'var(--accent-warning-subtle)', iconColor: 'var(--accent-warning)' }
      ];
    },
    severitySegments() {
      const issues = this.allIssues.filter(i => i.is_real_issue);
      const total = issues.length || 1;
      const counts = { Critical: 0, High: 0, Medium: 0, Low: 0 };
      issues.forEach(i => { const s = this.classifySeverity(i); counts[s]++; });
      return [
        { label: 'Critical', count: counts.Critical, pct: (counts.Critical / total) * 100, color: 'var(--severity-critical)' },
        { label: 'High', count: counts.High, pct: (counts.High / total) * 100, color: 'var(--severity-high)' },
        { label: 'Medium', count: counts.Medium, pct: (counts.Medium / total) * 100, color: 'var(--severity-medium)' },
        { label: 'Low', count: counts.Low, pct: (counts.Low / total) * 100, color: 'var(--severity-low)' }
      ];
    },
    allIssues() {
      if (!this.reportData?.files) return [];
      const issues = [];
      this.reportData.files.forEach(f => {
        (f.ui_accessibility_analysis || []).forEach(i => issues.push({ ...i, _fileName: f.file_name, _source: 'UI/A11y', _severity: this.classifySeverity(i).toLowerCase() }));
        (f.ai_analysis || []).forEach(i => issues.push({ ...i, _fileName: f.file_name, _source: 'AI Logic', _severity: this.classifySeverity(i).toLowerCase() }));
      });
      return issues;
    },
    confirmedIssues() { return this.allIssues.filter(i => i.is_real_issue); },
    fpIssues() { return this.allIssues.filter(i => !i.is_real_issue); },
    filteredIssues() {
      let list = this.issueFilter === 'confirmed' ? this.confirmedIssues : this.issueFilter === 'fp' ? this.fpIssues : this.allIssues;
      const q = this.issueSearch.toLowerCase().trim();
      if (q) list = list.filter(i => i._fileName.toLowerCase().includes(q) || (i.defect_type || '').toLowerCase().includes(q));
      return list;
    },
    groupedIssues() {
      const list = this.filteredIssues;
      const groups = {};
      list.forEach(i => {
        if (!groups[i._fileName]) groups[i._fileName] = [];
        groups[i._fileName].push(i);
      });
      return groups;
    },
    fileTree() {
      if (!this.reportData?.files) return [];
      
      const root = [];
      const files = this.reportData.files;
      const q = this.searchQuery.toLowerCase().trim();

      files.forEach(f => {
        if (q && !f.file_name.toLowerCase().includes(q) && !(f.file_path || '').toLowerCase().includes(q)) return;

        const pathParts = f.file_path.replace(/\\/g, '/').split('/');
        let currentLevel = root;

        pathParts.forEach((part, idx) => {
          const isLast = idx === pathParts.length - 1;
          const fullPath = pathParts.slice(0, idx + 1).join('/');
          
          let existing = currentLevel.find(item => item.name === part);
          if (!existing) {
            existing = {
              name: part,
              path: fullPath,
              absPath: isLast ? f.file_path : null, // Store exact path for files
              isDir: !isLast,
              issueCount: 0,
              children: []
            };
            currentLevel.push(existing);
          }
          
          if (isLast) {
            existing.issueCount = this.getIssueCount(f);
          }
          currentLevel = existing.children;
        });
      });

      // Recursive function to aggregate issue counts for folders
      const aggregateIssues = (node) => {
        if (!node.isDir) return node.issueCount;
        let count = 0;
        node.children.forEach(child => {
          count += aggregateIssues(child);
        });
        node.issueCount = count;
        return count;
      };

      root.forEach(aggregateIssues);

      // Sort: Folders first, then alphabetically
      const sortNodes = (nodes) => {
        nodes.sort((a, b) => {
          if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
          return a.name.localeCompare(b.name);
        });
        nodes.forEach(n => { if (n.children.length) sortNodes(n.children); });
      };
      sortNodes(root);

      return root;
    },
    filteredFiles() {
      if (!this.reportData?.files) return [];
      const q = this.searchQuery.toLowerCase().trim();
      return this.reportData.files.map((f, idx) => ({ ...f, _origIdx: idx })).filter(f => !q || f.file_name.toLowerCase().includes(q) || (f.file_path || '').toLowerCase().includes(q));
    },
    sandboxLineCount() {
      if (!this.sandboxSource) return 1;
      return this.sandboxSource.split('\n').length;
    },
    buildStatusText() {
      switch (this.buildStatus) {
        case 'running': return 'BUILDING...';
        case 'success': return 'COMPILED SUCCESSFULLY';
        case 'failed': return 'COMPILATION FAILED';
        default: return 'IDLE';
      }
    }
  },
  watch: {
    selectedFileIndex() {
      this.selectedIssueLines = [];
      this.activeFileIssue = null;
      this.issuesPanelOpen = true;
      if (this.activeViewerTab === 'sandbox') {
        this.initializeSandbox();
      }
    },
    activeViewerTab(newTab) {
      if (newTab === 'sandbox') {
        this.initializeSandbox();
      }
    },
    selectedIssueLines: {
      handler(newLines) {
        if (this.activeViewerTab === 'sandbox') {
          this.scrollSandboxToFirstHighlight();
        }
      },
      deep: true
    }
  },
  async mounted() {
    await this.fetchReport();
  },
  beforeUnmount() {
    if (this.sseSource) {
      this.sseSource.close();
    }
    if (this.toastTimer) {
      clearTimeout(this.toastTimer);
    }
  },
  errorCaptured(err, instance, info) {
    console.error('[AIReport] Component error caught:', err, info);
    this.componentError = `A rendering error occurred: ${err.message}. Try refreshing the report.`;
    return false; // Prevent the error from propagating further
  },

  methods: {
    async fetchReport() {
      this.loading = true;
      try {
        const reportUrl = this.selectedReportId ? `/ai_report?id=${this.selectedReportId}&_t=${Date.now()}` : `/ai_report?_t=${Date.now()}`;
        const [reportRes, archRes] = await Promise.all([
          axios.get(reportUrl),
          axios.get(`/ai_architecture?_t=${Date.now()}`).catch(() => ({ data: null }))
        ]);
        
        this.reportData = reportRes.data;
        this.aiArchitecture = archRes.data;
        this.error = null;
        
        if (this.reportData?.files?.length > 0) this.selectedFileIndex = 0;
      } catch (err) { 
        this.error = "No AI report found. Ensure analysis has completed."; 
      } finally { 
        this.loading = false; 
      }
    },
    getIssueCount(f) { return (f.ui_accessibility_analysis?.filter?.(i => i.is_real_issue)?.length || 0) + (f.ai_analysis?.filter?.(i => i.is_real_issue)?.length || 0); },
    getUICount(f) { return f.ui_accessibility_analysis?.filter?.(i => i.is_real_issue)?.length || 0; },
    getAICount(f) { return f.ai_analysis?.filter?.(i => i.is_real_issue)?.length || 0; },
    classifySeverity(issue) {
      const t = (issue.defect_type || '').toLowerCase();
      if (t.includes('security') || t.includes('xss') || t.includes('inject')) return 'Critical';
      if (t.includes('error') || t.includes('bug') || t.includes('logic')) return 'High';
      if (t.includes('accessibility') || t.includes('a11y') || t.includes('performance')) return 'Medium';
      if (issue.is_real_issue) return 'Medium';
      return 'Low';
    },
    getSeverityBadge(f) {
      if (f.visual_simulation?.engineering_health_score === 0) return 'badge-warning';
      const c = this.getIssueCount(f);
      if (c === 0) return 'badge-success'; if (c <= 2) return 'severity-low'; if (c <= 5) return 'severity-medium'; return 'severity-high';
    },
    getSeverityLabel(f) {
      if (f.visual_simulation?.engineering_health_score === 0) return 'Timeout';
      const c = this.getIssueCount(f);
      if (c === 0) return 'Clean'; if (c <= 2) return 'Low'; if (c <= 5) return 'Medium'; return 'High';
    },
    selectFileByPath(path) {
      const idx = this.reportData.files.findIndex(f => f.file_path === path);
      if (idx !== -1) {
        this.selectedFileIndex = idx;
        this.selectedIssueLines = [];
        this.activeFileIssue = null;
        this.issuesPanelOpen = true;
      }
    },
    openFile(idx) { 
      this.selectedFileIndex = idx; 
      this.selectedIssueLines = [];
      this.activeFileIssue = null;
      this.issuesPanelOpen = true;
      this.$emit('navigate', 'files'); 
    },
    focusIssue(issue, idx) {
      this.activeFileIssue = this.activeFileIssue === idx ? null : idx;
      const startLine = issue.line_number || issue.line || this.extractLineNumber(issue.rationale) || this.extractLineNumber(issue.suggestion);
      const lines = [];
      if (startLine) {
        const codeToMeasure = issue.original_code || issue.original_code_snippet || issue.fixed_code || issue.fixed_code_snippet;
        let count = 1;
        if (codeToMeasure) {
          count = Math.max(1, codeToMeasure.trim().split('\n').length);
        }
        for (let i = 0; i < count; i++) lines.push(startLine + i);
      }
      this.selectedIssueLines = lines;
    },
    toggleIssueExpand(idx) { this.expandedIssue = this.expandedIssue === idx ? null : idx; },
    toggleGroup(fName) { this.expandedGroups[fName] = !this.expandedGroups[fName]; },
    inspectCode(issue) {
      const idx = this.reportData.files.findIndex(f => f.file_name === issue._fileName);
      if (idx !== -1) {
        this.selectedFileIndex = idx;
        const startLine = issue.line_number || issue.line || this.extractLineNumber(issue.rationale) || this.extractLineNumber(issue.suggestion);
        const lines = [];
        if (startLine) {
          const codeToMeasure = issue.original_code || issue.original_code_snippet || issue.fixed_code || issue.fixed_code_snippet;
          let count = 1;
          if (codeToMeasure) {
            count = Math.max(1, codeToMeasure.trim().split('\n').length);
          }
          for (let i = 0; i < count; i++) lines.push(startLine + i);
        }
        this.selectedIssueLines = lines;
        this.$emit('navigate', 'files');
      }
    },
    extractLineNumber(text) {
      if (!text) return null;
      const m = text.match(/line (\d+)/i) || text.match(/at (\d+)/i);
      return m ? parseInt(m[1]) : null;
    },
    truncatePath(path) { if (!path) return ''; const p = path.replace(/\\/g, '/').split('/'); return p.length <= 3 ? path : '.../' + p.slice(-3).join('/'); },
    formatMarkdown(text) {
      if (!text) return '';
      let h = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      h = h.replace(/```(\w*)\n([\s\S]*?)```/g, (m, lang, code) => `<div class="code-block"><div class="code-block-header">${lang||'code'}</div><pre><code>${code.trim()}</code></pre></div>`);
      h = h.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
      h = h.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      return h.replace(/\n/g, '<br>');
    },
    getRiskAssessment(f) {
      if (!f) return { label: 'Unknown', class: 'badge-neutral' };
      if (f.visual_simulation?.engineering_health_score === 0) return { label: 'Analysis Failed', class: 'badge-warning' };
      const issues = this.getIssueCount(f);
      if (issues === 0) return { label: 'Safe', class: 'badge-success' };
      
      const deps = f.downstream_impact?.length || 0;
      const allFileIssues = [...(f.ai_analysis || []), ...(f.ui_accessibility_analysis || [])].filter(i => i.is_real_issue);
      const hasCritical = allFileIssues.some(i => this.classifySeverity(i) === 'Critical');
      
      if (deps === 0) return { label: 'Low Risk', class: 'badge-success' };
      if (deps <= 2 && !hasCritical) return { label: 'Medium Risk', class: 'badge-warning' };
      if (deps <= 5 || (hasCritical && deps <= 2)) return { label: 'High Risk', class: 'badge-danger' };
      
      return { label: 'CRITICAL RISK', class: 'badge-danger pulse-regression' };
    },
    openInVsCode(issue) {
      if (!this.selectedFile) return;
      const startLine = issue.line_number || issue.line || this.extractLineNumber(issue.rationale) || this.extractLineNumber(issue.suggestion);
      const codeToMeasure = issue.original_code || issue.original_code_snippet || issue.fixed_code || issue.fixed_code_snippet;
      let count = 1;
      if (codeToMeasure) {
        count = Math.max(1, codeToMeasure.trim().split('\n').length);
      }
      
      const payload = {
        command: 'openFile',
        filePath: this.selectedFile.file_path,
        startLine: startLine || 1,
        endLine: (startLine || 1) + count - 1
      };
      
      window.parent.postMessage(payload, '*');
    },

    async copyFix(code) {
      try {
        await navigator.clipboard.writeText(code);
        alert('Fix code copied to clipboard!');
      } catch (err) {
        console.error('Failed to copy', err);
      }
    },
    discussWithAI(issue) {
      // Emit upward to App.vue so the issue survives the component re-key
      this.$emit('discuss-issue', issue);
    },
    // ── Refactor Sandbox & Build Check Methods ────────────────
    async initializeSandbox() {
      if (!this.selectedFile) return;
      try {
        const res = await axios.get(`/file-content?path=${encodeURIComponent(this.selectedFile.file_path)}`);
        this.sandboxOriginal = res.data;
        this.sandboxSource = res.data;
      } catch (err) {
        console.error('Failed to load file content for sandbox', err);
        this.showToast('Failed to load sandbox source code.', 'error');
      }
    },
    toggleSandboxTab() {
      this.activeViewerTab = 'sandbox';
    },
    syncEditorScroll() {
      const textarea = this.$refs.sandboxTextarea;
      const lineNumbers = this.$refs.editorLineNumbers;
      const bgsContainer = this.$refs.editorBgsContainer;
      if (textarea) {
        if (lineNumbers) lineNumbers.scrollTop = textarea.scrollTop;
        if (bgsContainer) bgsContainer.scrollTop = textarea.scrollTop;
      }
    },
    scrollSandboxToFirstHighlight() {
      if (this.selectedIssueLines.length > 0) {
        this.$nextTick(() => {
          const lineNum = this.selectedIssueLines[0];
          const lineNumbersEl = this.$refs.editorLineNumbers;
          if (lineNumbersEl && lineNumbersEl.children) {
            const targetEl = lineNumbersEl.children[lineNum - 1];
            const textarea = this.$refs.sandboxTextarea;
            if (targetEl && textarea) {
              const top = targetEl.offsetTop;
              const height = textarea.clientHeight;
              textarea.scrollTop = top - (height / 2);
              this.syncEditorScroll();
            }
          }
        });
      }
    },
    showToast(msg, type = 'success') {
      this.toast.show = true;
      this.toast.msg = msg;
      this.toast.type = type;
      
      if (this.toastTimer) {
        clearTimeout(this.toastTimer);
      }
      this.toastTimer = setTimeout(() => {
        this.toast.show = false;
      }, 4000);
    },
    closeToast() {
      this.toast.show = false;
    },
    applySelectedFix() {
      if (this.activeFileIssue === null) return;
      const issue = this.selectedFileIssues[this.activeFileIssue];
      if (issue) {
        this.applyIssueFix(issue);
      }
    },
    applyAllSuggestions() {
      let count = 0;
      for (const issue of this.selectedFileIssues) {
        if (issue.is_real_issue) {
          const success = this.applyIssueFixSilent(issue);
          if (success) count++;
        }
      }
      if (count > 0) {
        this.showToast(`Applied ${count} fixes successfully in-memory!`, 'success');
      } else {
        this.showToast('No fixes could be automatically applied.', 'warning');
      }
    },
    applyIssueFix(issue) {
      const originalSnippet = (issue.original_code || issue.original_code_snippet || '').trim();
      const fixedSnippet = (issue.fixed_code || issue.fixed_code_snippet || '').trim();
      
      if (!originalSnippet || !fixedSnippet) {
        this.showToast('Could not find code snippets to apply the fix.', 'error');
        return false;
      }
      
      if (this.sandboxSource.includes(originalSnippet)) {
        this.sandboxSource = this.sandboxSource.replace(originalSnippet, fixedSnippet);
        this.showToast('Successfully applied fix suggestion!', 'success');
        return true;
      }
      
      const lines = this.sandboxSource.split('\n');
      const lineNum = issue.line_number || issue.line || this.extractLineNumber(issue.rationale);
      
      if (lineNum && lineNum <= lines.length) {
        const targetIdx = lineNum - 1;
        const origLines = originalSnippet.split('\n');
        let matched = true;
        for (let i = 0; i < origLines.length; i++) {
          if (targetIdx + i >= lines.length || !lines[targetIdx + i].trim().includes(origLines[i].trim())) {
            matched = false;
            break;
          }
        }
        
        if (matched) {
          lines.splice(targetIdx, origLines.length, fixedSnippet);
          this.sandboxSource = lines.join('\n');
          this.showToast('Successfully applied fix at line ' + lineNum, 'success');
          return true;
        }
      }
      
      const firstOrigLine = originalSnippet.split('\n')[0].trim();
      if (firstOrigLine.length > 5) {
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].trim() === firstOrigLine) {
            const origLines = originalSnippet.split('\n');
            lines.splice(i, origLines.length, fixedSnippet);
            this.sandboxSource = lines.join('\n');
            this.showToast('Successfully applied fix (fuzzy matched lines)', 'success');
            return true;
          }
        }
      }
      
      this.showToast('Could not auto-apply fix. The code may have been modified. Please copy the fix manually.', 'warning');
      return false;
    },
    applyIssueFixSilent(issue) {
      const originalSnippet = (issue.original_code || issue.original_code_snippet || '').trim();
      const fixedSnippet = (issue.fixed_code || issue.fixed_code_snippet || '').trim();
      if (!originalSnippet || !fixedSnippet) return false;
      
      if (this.sandboxSource.includes(originalSnippet)) {
        this.sandboxSource = this.sandboxSource.replace(originalSnippet, fixedSnippet);
        return true;
      }
      
      const lines = this.sandboxSource.split('\n');
      const lineNum = issue.line_number || issue.line || this.extractLineNumber(issue.rationale);
      if (lineNum && lineNum <= lines.length) {
        const targetIdx = lineNum - 1;
        const origLines = originalSnippet.split('\n');
        let matched = true;
        for (let i = 0; i < origLines.length; i++) {
          if (targetIdx + i >= lines.length || !lines[targetIdx + i].trim().includes(origLines[i].trim())) {
            matched = false;
            break;
          }
        }
        if (matched) {
          lines.splice(targetIdx, origLines.length, fixedSnippet);
          this.sandboxSource = lines.join('\n');
          return true;
        }
      }
      
      const firstOrigLine = originalSnippet.split('\n')[0].trim();
      if (firstOrigLine.length > 5) {
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].trim() === firstOrigLine) {
            const origLines = originalSnippet.split('\n');
            lines.splice(i, origLines.length, fixedSnippet);
            this.sandboxSource = lines.join('\n');
            return true;
          }
        }
      }
      return false;
    },
    async saveSandboxToFile() {
      if (!this.selectedFile) return;
      try {
        const res = await axios.post('/api/save-file', {
          path: this.selectedFile.file_path,
          content: this.sandboxSource
        });
        if (res.data.status === 'success') {
          this.sandboxOriginal = this.sandboxSource;
          this.showToast('File saved to disk successfully!', 'success');
        } else {
          this.showToast(res.data.error || 'Failed to save file.', 'error');
        }
      } catch (err) {
        console.error('Failed to save file', err);
        this.showToast(err.response?.data?.error || 'Failed to save file to disk.', 'error');
      }
    },
    async runBuildCheck() {
      if (!this.selectedFile) return;
      this.buildLogs = ['[SYSTEM] Saving playground code to file...'];
      this.buildStatus = 'running';
      
      try {
        const saveRes = await axios.post('/api/save-file', {
          path: this.selectedFile.file_path,
          content: this.sandboxSource
        });
        if (saveRes.data.status === 'success') {
          this.sandboxOriginal = this.sandboxSource;
          this.buildLogs.push('[SYSTEM] File saved successfully.');
        } else {
          this.buildLogs.push('[SYSTEM ERROR] Failed to save sandbox code to disk. Testing last saved state instead.');
        }
      } catch (err) {
        console.error('Auto-save error', err);
        this.buildLogs.push('[SYSTEM WARNING] File write failed. Proceeding check on last saved disk version.');
      }
      
      try {
        const res = await axios.post('/api/run-build', {
          filePath: this.selectedFile.file_path
        });
        const jobId = res.data.job_id;
        this.buildJobId = jobId;
        
        if (this.sseSource) {
          this.sseSource.close();
        }
        
        const sseUrl = `/progress/${jobId}`;
        this.sseSource = new EventSource(sseUrl);
        
        this.sseSource.onmessage = (event) => {
          const line = event.data;
          this.buildLogs.push(line);
          this.$nextTick(() => {
            this.scrollTerminalToBottom();
          });
        };
        
        this.sseSource.onerror = (err) => {
          console.error('SSE Error:', err);
          if (this.sseSource) {
            this.sseSource.close();
            this.sseSource = null;
          }
          this.checkBuildJobStatus(jobId);
        };
      } catch (err) {
        console.error('Failed to run build', err);
        this.buildStatus = 'failed';
        this.buildLogs.push('[SYSTEM ERROR] Failed to trigger build job API.');
        this.showToast('Failed to trigger build check.', 'error');
      }
    },
    async checkBuildJobStatus(jobId) {
      try {
        const res = await axios.get(`/status/${jobId}`);
        const status = res.data.status;
        if (status === 'done') {
          const hasError = this.buildLogs.some(line => {
            const l = line.toLowerCase();
            return l.includes('error') || l.includes('failed') || l.includes('fail');
          });
          this.buildStatus = hasError ? 'failed' : 'success';
          if (hasError) {
            this.showToast('Build check completed with compilation errors.', 'error');
          } else {
            this.showToast('Build check passed! Zero compile errors.', 'success');
          }
        } else if (status === 'error') {
          this.buildStatus = 'failed';
          this.showToast(res.data.error || 'Build process encountered an error.', 'error');
        } else if (status === 'running' || status === 'queued') {
          setTimeout(() => this.checkBuildJobStatus(jobId), 1000);
        }
      } catch (err) {
        console.error('Failed to get job status', err);
        this.buildStatus = 'idle';
      }
    },
    scrollTerminalToBottom() {
      const terminal = this.$refs.terminalBody;
      if (terminal) {
        terminal.scrollTop = terminal.scrollHeight;
      }
    },
    clearBuildLogs() {
      this.buildLogs = [];
      this.buildStatus = 'idle';
    },
    getLogLineClass(log) {
      const l = log.toLowerCase();
      if (l.includes('error') || l.includes('failed') || l.includes('fail') || l.includes('err:')) {
        return 'log-error';
      }
      if (l.includes('built') || l.includes('success') || l.includes('done') || l.includes('compiled')) {
        return 'log-success';
      }
      if (l.includes('vite') || l.includes('rollup') || l.includes('building')) {
        return 'log-info';
      }
      return 'log-normal';
    }
  }
};
</script>

<style scoped>
.report-root { animation: slideUp 0.4s var(--ease-out); }

/* States */
.state-panel { display:flex; flex-direction:column; align-items:center; gap:1rem; padding:4rem 2rem; text-align:center; }
.state-text { color:var(--text-secondary); font-size:1rem; }
.state-error svg { color:var(--accent-danger); }
.state-spinner { width:36px; height:36px; border:3px solid var(--border-default); border-radius:50%; border-top-color:var(--accent-primary); animation:spin 0.9s linear infinite; }

/* Warning Banner */
.analysis-warning { display:flex; align-items:center; gap:0.75rem; padding:0.85rem 1.25rem; background:var(--accent-warning-subtle); border:1px solid var(--accent-warning); border-radius:var(--radius-md); margin-bottom:1.5rem; font-size:0.85rem; color:var(--text-secondary); }
.analysis-warning svg { color:var(--accent-warning); flex-shrink:0; }
.analysis-warning strong { color:var(--accent-warning); }

/* ═══ OVERVIEW ═══ */
.view-overview { display:flex; flex-direction:column; gap:1.5rem; }

/* Quality Gate */
.quality-gate { display:flex; align-items:center; gap:1.25rem; padding:1.25rem 1.5rem; border-radius:var(--radius-lg); border:1px solid; }
.quality-gate-passed { background:var(--accent-success-subtle); border-color:rgba(16,185,129,0.25); }
.quality-gate-failed { background:var(--accent-danger-subtle); border-color:rgba(239,68,68,0.25); }
.quality-gate-warning { background:var(--accent-warning-subtle); border-color:rgba(245,158,11,0.25); }
.quality-gate-icon { width:44px; height:44px; border-radius:var(--radius-md); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.quality-gate-passed .quality-gate-icon { background:var(--accent-success); color:white; }
.quality-gate-failed .quality-gate-icon { background:var(--accent-danger); color:white; }
.quality-gate-warning .quality-gate-icon { background:var(--accent-warning); color:white; }
.quality-gate-text { display:flex; flex-direction:column; gap:0.1rem; }
.quality-gate-label { font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-tertiary); }
.quality-gate-status { font-size:1.15rem; font-weight:700; }
.quality-gate-passed .quality-gate-status { color:var(--accent-success); }
.quality-gate-failed .quality-gate-status { color:var(--accent-danger); }
.quality-gate-warning .quality-gate-status { color:var(--accent-warning); }
.qg-score-wrap { position:relative; width:64px; height:64px; margin-left:auto; flex-shrink:0; }
.qg-ring { display:block; width:100%; height:100%; }
.qg-ring-bg { fill:none; stroke:var(--border-subtle); stroke-width:3; }
.qg-ring-fill { fill:none; stroke-width:3; stroke-linecap:round; animation:ringDraw 1s var(--ease-out) forwards; }
.ring-success { stroke:var(--accent-success); }
.ring-good { stroke:#22d3ee; }
.ring-warning { stroke:var(--accent-warning); }
.ring-danger { stroke:var(--accent-danger); }
.qg-score-num { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.qg-val { font-size:1.3rem; font-weight:800; color:var(--text-primary); line-height:1; }
.qg-max { font-size:0.55rem; color:var(--text-tertiary); }

/* KPI Strip */
.kpi-strip { display:grid; grid-template-columns:repeat(4, 1fr); gap:1rem; }
.kpi-card { display:flex; align-items:center; gap:1rem; padding:1.25rem; background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); transition:all var(--duration-normal) var(--ease-out); }
.kpi-card:hover { box-shadow:var(--shadow-md); transform:translateY(-1px); }
.kpi-icon-wrap { width:40px; height:40px; border-radius:var(--radius-md); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.kpi-data { display:flex; flex-direction:column; gap:0.15rem; }
.kpi-value { font-size:1.5rem; font-weight:800; line-height:1.1; animation:countUp .4s var(--ease-out); }
.kpi-label { font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.04em; color:var(--text-tertiary); }

/* Section Card */
.section-card { background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); overflow:hidden; }
.section-header { display:flex; justify-content:space-between; align-items:center; padding:1rem 1.25rem; border-bottom:1px solid var(--border-subtle); }
.section-header h3 { font-size:0.92rem; margin:0; }

/* Severity Bar */
.severity-bar-container { padding:1.25rem; }
.severity-bar { display:flex; height:10px; border-radius:5px; overflow:hidden; gap:2px; margin-bottom:1rem; }
.severity-segment { transition:width .6s var(--ease-out); min-width:2px; border-radius:2px; }
.severity-legend { display:flex; gap:1.5rem; flex-wrap:wrap; }
.legend-item { display:flex; align-items:center; gap:0.4rem; font-size:0.78rem; }
.legend-dot { width:8px; height:8px; border-radius:5  0%; flex-shrink:0; }
.legend-label { color:var(--text-secondary); }
.legend-count { font-weight:700; color:var(--text-primary); }

/* Architectural Insights */
.architecture-highlights { border: 1px solid var(--accent-primary-subtle) !important; background: var(--bg-surface); padding-bottom: 1.5rem; }
.header-with-icon { display: flex; align-items: center; gap: 0.75rem; color: var(--accent-primary); }
.trends-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; padding: 0 1.25rem; margin-top: 1.25rem; }
.trend-card { background: var(--bg-inset); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1.25rem; display: flex; flex-direction: column; gap: 0.75rem; transition: all var(--duration-normal); }
.trend-card:hover { border-color: var(--accent-primary); transform: translateY(-2px); box-shadow: var(--shadow-sm); }
.trend-header { display: flex; justify-content: space-between; align-items: center; }
.trend-type { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; color: var(--text-tertiary); letter-spacing: 0.05em; }
.trend-severity-badge { font-size: 0.6rem; font-weight: 800; padding: 0.15rem 0.5rem; border-radius: 4px; text-transform: uppercase; }
.sev-high { background: var(--accent-danger-subtle); color: var(--accent-danger); }
.sev-medium { background: var(--accent-warning-subtle); color: var(--accent-warning); }
.sev-low { background: var(--accent-primary-subtle); color: var(--accent-primary); }
.trend-card h4 { font-size: 0.95rem; font-weight: 700; margin: 0; color: var(--text-primary); }
.trend-card p { font-size: 0.82rem; line-height: 1.5; color: var(--text-secondary); margin: 0; }
.trend-footer { display: flex; flex-direction: column; gap: 0.5rem; margin-top: auto; padding-top: 0.5rem; }
.footer-label { font-size: 0.65rem; color: var(--text-tertiary); font-weight: 600; }
.trend-tags { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.trend-tag { background: var(--bg-overlay); border: 1px solid var(--border-subtle); border-radius: 4px; padding: 0.1rem 0.4rem; font-size: 0.65rem; color: var(--text-tertiary); }


/* Table */
.table-wrap { overflow-x:auto; }
.file-name-cell { font-family:var(--font-mono); font-size:0.82rem; }

/* ═══ ISSUES VIEW ═══ */
.view-issues { display:flex; flex-direction:column; gap:1rem; }
.issues-toolbar { display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap; }
.search-box { display:flex; align-items:center; gap:0.5rem; background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:0.4rem 0.75rem; color:var(--text-tertiary); }
.search-input { background:none; border:none; outline:none; font-family:var(--font-sans); font-size:0.82rem; color:var(--text-primary); width:200px; }
.search-input::placeholder { color:var(--text-tertiary); }
.issues-table-wrap { background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); overflow:hidden; }
.empty-state { display:flex; align-items:center; justify-content:center; gap:0.6rem; padding:3rem; color:var(--text-tertiary); font-size:0.9rem; }
.empty-state svg { color:var(--accent-success); }

/* Expandable */
.expand-section { margin-bottom:1rem; }
.expand-section:last-child { margin-bottom:0; }
.expand-label { font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-tertiary); margin-bottom:0.35rem; }
.expand-body { font-size:0.85rem; line-height:1.7; color:var(--text-secondary); }
.expand-fix { background:var(--bg-surface); padding:1rem; border-radius:var(--radius-md); border-left:3px solid var(--accent-warning); }
.fix-label { color:var(--accent-warning); }

/* ═══ FILE INSPECTOR ═══ */
.inspector-layout { display:grid; grid-template-columns:280px 1fr; gap:1rem; height:calc(100vh - var(--topbar-height) - 80px); min-height:500px; }
.file-sidebar { display:flex; flex-direction:column; overflow:hidden; height:100%; border:1px solid var(--border-subtle); border-radius:var(--radius-lg); }
.fs-head { padding:1rem 1.25rem; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-subtle); flex-shrink:0; }
.fs-head h4 { font-size:0.88rem; margin:0; }
.fs-search { padding:0.5rem 0.75rem; display:flex; align-items:center; gap:0.l5rem; border-bottom:1px solid var(--border-subtle); flex-shrink:0; color:var(--text-tertiary); }
.fs-input { flex:1; background:none; border:none; outline:none; font-family:var(--font-sans); font-size:0.82rem; color:var(--text-primary); }
.fs-input::placeholder { color:var(--text-tertiary); }
.fs-list { flex:1; overflow-y:auto; padding:0.35rem; }
.fs-item { display:flex; justify-content:space-between; align-items:center; padding:0.6rem 0.75rem; border-radius:var(--radius-sm); cursor:pointer; transition:all var(--duration-fast); margin-bottom:1px; border:1px solid transparent; }
.fs-item:hover { background:var(--bg-surface-hover); }
.fs-item.active { background:var(--accent-primary-subtle); border-color:var(--accent-primary-glow); }
.fs-item-info { display:flex; flex-direction:column; min-width:0; }
.fs-filename { font-size:0.82rem; font-weight:500; color:var(--text-primary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.fs-path { font-size:0.68rem; color:var(--text-tertiary); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.fs-badges { display:flex; gap:0.3rem; flex-shrink:0; }
.mini-badge { font-size:0.65rem; font-weight:700; padding:0.1rem 0.35rem; border-radius:var(--radius-sm); line-height:1.3; }
.mini-issue { background:var(--accent-danger-subtle); color:var(--accent-danger); }
.mini-clean { background:var(--accent-success-subtle); color:var(--accent-success); font-size:0.6rem; }

/* Workspace */
.file-workspace { height:100%; min-width:0; }
.ws-content { height:100%; display:flex; flex-direction:column; overflow:hidden; border:1px solid var(--border-subtle); border-radius:var(--radius-lg); }
.ws-header { padding:1rem 1.25rem; border-bottom:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center; flex-shrink:0; flex-wrap:wrap; gap:0.5rem; }
.ws-title-row { display:flex; align-items:center; gap:0.6rem; }
.ws-header h3 { font-size:0.95rem; margin:0; }
.ws-path { font-family:var(--font-mono); font-size:0.72rem; color:var(--text-tertiary); background:var(--bg-inset); padding:0.2rem 0.6rem; border-radius:var(--radius-sm); }
.ws-body { flex:1; overflow-y:auto; padding:1.25rem; }
.ws-empty { display:flex; align-items:center; gap:0.6rem; padding:2rem; justify-content:center; color:var(--text-tertiary); font-size:0.9rem; }
.ws-empty svg { color:var(--accent-success); }

/* Audit Sections */
.audit-section { margin-bottom:1.5rem; border:1px solid var(--border-subtle); border-radius:var(--radius-md); overflow:hidden; }
.audit-section:last-child { margin-bottom:0; }
.audit-header { display:flex; justify-content:space-between; align-items:center; padding:0.75rem 1rem; border-bottom:1px solid var(--border-subtle); }
.audit-header-left { display:flex; align-items:center; gap:0.5rem; }
.audit-header h4 { font-size:0.85rem; margin:0; }
.ui-header { background:var(--accent-danger-subtle); }
.ui-header svg { color:var(--accent-danger); }
.ai-header { background:var(--accent-primary-subtle); }
.ai-header svg { color:var(--accent-primary); }

/* Issue Items */
.issue-item { padding:1.1rem; border-bottom:1px solid var(--border-subtle); transition:background var(--duration-fast); }
.issue-item:last-child { border-bottom:none; }
.issue-item:hover { background:var(--bg-surface-hover); }
.issue-real { border-left:3px solid var(--accent-danger); }
.issue-fp { border-left:3px solid var(--accent-success); opacity:0.7; }
.issue-top { display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap; margin-bottom:0.6rem; }
.rule-tag { font-family:var(--font-mono); font-size:0.78rem; font-weight:600; color:var(--text-primary); text-transform:uppercase; letter-spacing:0.03em; }
.issue-detail, .issue-fix { margin-bottom:0.6rem; }
.issue-fix:last-child, .issue-detail:last-child { margin-bottom:0; }
.detail-label { font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:var(--text-tertiary); margin-bottom:0.3rem; }
.detail-body { font-size:0.85rem; line-height:1.7; color:var(--text-secondary); }
.issue-fix { background:var(--bg-inset); padding:0.85rem; border-radius:var(--radius-md); border-left:3px solid var(--accent-warning); }
/* Issues Grouping */
.file-issue-group { margin-bottom: 1rem; border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); overflow: hidden; }
.group-header { padding: 0.85rem 1.25rem; background: var(--bg-overlay); display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: background 0.2s; }
.group-header:hover { background: var(--bg-surface-hover); }
.group-title { display: flex; align-items: center; gap: 0.75rem; font-family: var(--font-mono); font-size: 0.9rem; font-weight: 700; color: var(--text-primary); }
.group-badges { display: flex; align-items: center; gap: 1rem; }
.rotate-180 { transform: rotate(180deg); }
.slide-fade-enter-active, .slide-fade-leave-active { transition: all 0.3s ease; }
.slide-fade-enter-from, .slide-fade-leave-to { opacity: 0; transform: translateY(-10px); }

/* Source Viewer Integration */
.ws-source-v2 { flex: 1; display: flex; flex-direction: column; min-height: 350px; max-height: 450px; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); margin-bottom: 0; background: var(--bg-inset); overflow: hidden; }
.source-header { padding: 0.6rem 1rem; border-bottom: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--text-tertiary); background: var(--bg-surface); }
.highlight-info { display: flex; align-items: center; gap: 0.4rem; color: var(--accent-danger); }
.line-dot { width: 6px; height: 6px; background: var(--accent-danger); border-radius: 50%; }

/* File Inspector Issues Panel */
.ws-issues-panel { border: 1px solid var(--border-subtle); border-radius: var(--radius-md); margin-top: 1rem; overflow: hidden; background: var(--bg-surface); }
.issues-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; cursor: pointer; background: var(--bg-overlay); transition: background 0.2s; border-bottom: 1px solid var(--border-subtle); }
.issues-panel-header:hover { background: var(--bg-surface-hover); }
.iph-left { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; font-weight: 700; color: var(--text-primary); }
.issues-panel-body { padding: 0.5rem; max-height: 400px; overflow-y: auto; }

.ws-issue-item { padding: 0.85rem 1rem; margin: 0.35rem 0; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); cursor: pointer; transition: all 0.2s ease; background: var(--bg-surface); }
.ws-issue-item:hover { border-color: var(--accent-primary); box-shadow: 0 0 0 1px var(--accent-primary-subtle); }
.ws-issue-item.ws-issue-active { border-color: var(--accent-primary); background: var(--accent-primary-subtle); box-shadow: 0 0 0 2px var(--accent-primary-subtle); }
.ws-issue-top { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem; }
.ws-issue-type { font-size: 0.82rem; font-weight: 700; color: var(--text-primary); }
.ws-issue-rationale { font-size: 0.78rem; color: var(--text-secondary); line-height: 1.5; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.ws-issue-active .ws-issue-rationale { -webkit-line-clamp: unset; }
.ws-issue-fix { margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px dashed var(--border-subtle); }
.ws-fix-label { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: var(--accent-success); margin-bottom: 0.35rem; letter-spacing: 0.03em; }
.ws-issue-fix p { font-size: 0.78rem; color: var(--text-secondary); line-height: 1.5; margin: 0; }

.severity-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.severity-dot-blocking, .severity-dot-critical { background: #ef4444; }
.severity-dot-fragile, .severity-dot-high { background: #f97316; }
.severity-dot-confusing, .severity-dot-medium { background: #eab308; }
.severity-dot-accessibility, .severity-dot-low { background: #3b82f6; }

.ws-clean-badge { display: flex; align-items: center; gap: 0.6rem; padding: 1rem 1.25rem; margin-top: 1rem; border-radius: var(--radius-md); background: var(--accent-success-subtle, rgba(34,197,94,0.08)); color: var(--accent-success, #22c55e); font-size: 0.85rem; font-weight: 600; border: 1px solid rgba(34,197,94,0.15); }

/* ── Discuss with AI Button ──────────────────────── */
.btn-discuss {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.85rem;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.12), rgba(99, 102, 241, 0.12));
  color: #a78bfa;
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: var(--radius-md, 8px);
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
}
.btn-discuss:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.22), rgba(99, 102, 241, 0.22));
  border-color: rgba(139, 92, 246, 0.5);
  color: #c4b5fd;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
}
.btn-discuss svg { opacity: 0.85; }
.btn-discuss:hover svg { opacity: 1; }

.rich-content strong { color:var(--text-primary); font-weight:700; }
.rich-content .inline-code { background:var(--bg-inset); padding:0.1em 0.35em; border-radius:4px; font-family:var(--font-mono); font-size:0.84em; color:var(--accent-primary); }

/* Regression Risk Pulse */
.pulse-regression {
  animation: pulse-reg 2s infinite;
  box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
}

@keyframes pulse-reg {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
  70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.badge-risk {
  display: flex !important;
  align-items: center;
  gap: 0.25rem;
  font-weight: 800 !important;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.65rem !important;
}

/* ═══ FIX STATUS TOAST ═══ */
.fix-toast {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1.5rem;
  border-radius: var(--radius-lg, 12px);
  font-size: 0.85rem;
  font-weight: 600;
  box-shadow: 0 8px 32px rgba(0,0,0,0.35);
  backdrop-filter: blur(12px);
  min-width: 340px;
  max-width: 600px;
  border: 1px solid;
}
.fix-toast-success { background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.35); color: #34d399; }
.fix-toast-error   { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.35); color: #f87171; }
.fix-toast-warning { background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.35); color: #fbbf24; }
.fix-toast-rolledback { background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.35); color: #818cf8; }
.fix-toast-cancelled { background: rgba(107, 114, 128, 0.15); border-color: rgba(107, 114, 128, 0.35); color: #9ca3af; }
.fix-toast-icon { flex-shrink: 0; display: flex; align-items: center; }
.fix-toast-msg { flex: 1; line-height: 1.4; }
.fix-toast-close { background: none; border: none; color: inherit; opacity: 0.6; cursor: pointer; font-size: 1.3rem; padding: 0 0.2rem; line-height: 1; transition: opacity 0.2s; }
.fix-toast-close:hover { opacity: 1; }

/* Toast transition */
.slide-up-enter-active { transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.slide-up-leave-active { transition: all 0.3s ease-in; }
.slide-up-enter-from { opacity: 0; transform: translateX(-50%) translateY(20px); }
.slide-up-leave-to { opacity: 0; transform: translateX(-50%) translateY(10px); }

/* Button spinner */
.btn-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

/* ── Refactor Sandbox & Custom Code Editor ── */
.ws-source-v2.sandbox-mode {
  max-height: 800px;
  height: 800px;
  min-height: 600px;
}

.viewer-tabs {
  display: flex;
  gap: 4px;
  background: var(--bg-inset, #0b0f19);
  padding: 2px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
}

.tab-btn {
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.35rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--bg-surface);
  color: var(--accent-primary);
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.sandbox-tab-btn {
  position: relative;
  display: flex;
  align-items: center;
}

.sandbox-pulse-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--accent-primary);
  border-radius: 50%;
  margin-left: 5px;
  box-shadow: 0 0 8px var(--accent-primary);
  animation: pulse-dot 1.5s infinite;
}

@keyframes pulse-dot {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.7); }
  70% { transform: scale(1.1); box-shadow: 0 0 0 5px rgba(139, 92, 246, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(139, 92, 246, 0); }
}

.sandbox-actions-panel {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.btn-sandbox-action {
  font-size: 0.72rem !important;
  padding: 0.25rem 0.6rem !important;
  font-weight: 600 !important;
}

.btn-sandbox-action.save-btn {
  background: linear-gradient(135deg, #10b981, #059669);
  border-color: #059669;
}

.btn-sandbox-action.build-btn {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  border-color: #4f46e5;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.viewer-panes-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.sandbox-split-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--border-subtle);
  overflow: hidden;
  height: 100%;
}

.sandbox-side {
  display: flex;
  flex-direction: column;
  background: var(--bg-inset);
  overflow: hidden;
  height: 100%;
}

.side-banner {
  padding: 0.4rem 0.8rem;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-secondary);
  background: var(--bg-overlay);
  border-bottom: 1px solid var(--border-subtle);
  letter-spacing: 0.05em;
}

.editable-banner {
  color: var(--accent-primary);
  border-left: 2px solid var(--accent-primary);
}

.side-pane-wrapper {
  flex: 1;
  overflow: hidden;
  height: 100%;
}

.editable-pane-wrapper {
  background: var(--bg-surface);
}

.sandbox-editor-wrapper {
  display: flex;
  height: 100%;
  position: relative;
  font-family: var(--font-mono);
  font-size: 0.82rem;
  background: #0f1420;
}

.sandbox-bgs-container {
  position: absolute;
  top: 0;
  left: 40px;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 1;
  padding: 1rem 0;
}

.sandbox-line-bg {
  height: 1.6em;
  width: 100%;
}

.sandbox-line-bg.hl-bg {
  background: var(--accent-danger-subtle, rgba(239, 68, 68, 0.15));
}

.sandbox-line-numbers {
  width: 40px;
  background: #0b0e17;
  border-right: 1px solid var(--border-subtle);
  padding: 1rem 0;
  display: flex;
  flex-direction: column;
  text-align: right;
  user-select: none;
  overflow-y: hidden;
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

.sandbox-num {
  padding: 0 0.75rem;
  color: var(--text-tertiary);
  height: 1.6em;
  line-height: 1.6;
  border-right: 3px solid transparent;
  transition: all var(--duration-fast) var(--ease-out);
}

.sandbox-num.highlight-line {
  background: var(--accent-danger-subtle, rgba(239, 68, 68, 0.15));
  color: var(--accent-danger, #ef4444);
  border-right: 3px solid var(--accent-danger, #ef4444);
  font-weight: 700;
}

.sandbox-textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  padding: 1rem;
  color: #e2e8f0;
  font-family: inherit;
  font-size: inherit;
  line-height: 1.6;
  white-space: pre;
  overflow-x: auto;
  overflow-y: auto;
  position: relative;
  z-index: 2;
}

/* Glassmorphic Streaming Terminal Console */
.glassmorphic-terminal {
  height: 220px;
  border-top: 1px solid var(--border-subtle);
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.terminal-header {
  padding: 0.5rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  background: rgba(9, 15, 29, 0.8);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.terminal-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.terminal-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.red-dot { background: #ef4444; }
.yellow-dot { background: #eab308; }
.green-dot { background: #22c55e; }

.terminal-label {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  margin-left: 0.4rem;
  letter-spacing: 0.05em;
}

.terminal-status-badge {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(255,255,255,0.04);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  border: 1px solid rgba(255,255,255,0.06);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-tertiary);
}

.status-dot.running {
  background: #eab308;
  box-shadow: 0 0 8px #eab308;
  animation: pulse-dot-yellow 1.5s infinite;
}

.status-dot.success {
  background: #22c55e;
  box-shadow: 0 0 8px #22c55e;
}

.status-dot.failed {
  background: #ef4444;
  box-shadow: 0 0 8px #ef4444;
  animation: pulse-dot-red 1.5s infinite;
}

@keyframes pulse-dot-yellow {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(234, 179, 8, 0.7); }
  70% { transform: scale(1.1); box-shadow: 0 0 0 5px rgba(234, 179, 8, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(234, 179, 8, 0); }
}

@keyframes pulse-dot-red {
  0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
  70% { transform: scale(1.1); box-shadow: 0 0 0 5px rgba(239, 68, 68, 0); }
  100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.status-text {
  font-size: 0.65rem;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--text-secondary);
}

.btn-clear-console {
  font-size: 0.65rem !important;
  color: var(--text-tertiary) !important;
  background: transparent !important;
  border: none !important;
  cursor: pointer;
}

.btn-clear-console:hover {
  color: var(--text-primary) !important;
}

.terminal-body {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  font-family: var(--font-mono);
  font-size: 0.76rem;
  line-height: 1.5;
  color: #cbd5e1;
  background: rgba(9, 13, 22, 0.4);
}

.terminal-placeholder {
  color: var(--text-tertiary);
  font-style: italic;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.terminal-line {
  white-space: pre-wrap;
  margin-bottom: 0.2rem;
}

.log-error {
  color: #f87171;
  font-weight: 600;
  background: rgba(239, 68, 68, 0.08);
  padding: 0.1rem 0.25rem;
  border-left: 2px solid #ef4444;
  animation: pulse-danger-line 2s infinite;
}

@keyframes pulse-danger-line {
  0% { background: rgba(239, 68, 68, 0.08); }
  50% { background: rgba(239, 68, 68, 0.15); }
  100% { background: rgba(239, 68, 68, 0.08); }
}

.log-success {
  color: #34d399;
  font-weight: 600;
  background: rgba(16, 185, 129, 0.06);
  padding: 0.1rem 0.25rem;
}

.log-info {
  color: #22d3ee;
}

.log-normal {
  color: #cbd5e1;
}

/* Print Styles */
@media print {
  .header-actions, .file-sidebar, .topbar, .issues-toolbar, .btn-ghost, .sidebar-search { display: none !important; }
  .report-root { border: none !important; margin: 0 !important; width: 100% !important; background: white !important; color: black !important; }
  .view-overview, .view-issues { padding: 0 !important; }
  .file-issue-group { border: 1px solid #eee !important; page-break-inside: avoid; margin-bottom: 2rem !important; }
  .group-header { background: #f9f9f9 !important; border-bottom: 1px solid #eee !important; -webkit-print-color-adjust: exact; }
  .workspace-layout { display: block !important; }
  .file-workspace { width: 100% !important; border: none !important; }
  .card { box-shadow: none !important; border: 1px solid #eee !important; }
  body { background: white !important; }
  .badge-danger { color: #d00 !important; border: 1px solid #d00 !important; }
  * { overflow: visible !important; }
}
</style>
