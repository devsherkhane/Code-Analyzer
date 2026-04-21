<template>
  <div class="upload-root">
    <div class="upload-card card card-elevated">
      <!-- Workspace Info -->
      <div class="workspace-info card card-flat">
        <div class="workspace-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
        </div>
        <div class="workspace-details">
          <span class="workspace-label">Connected Workspace</span>
          <span class="workspace-path">{{ vscodePath || 'No workspace connected' }}</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="upload-actions">
        <!-- Direct Workspace Analysis for VS Code -->
        <button class="btn-primary btn-lg upload-btn" @click="analyzeWorkspace" :disabled="!isVSCode || status === 'running' || status === 'queued'">
          <svg v-if="status === 'idle'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
          <span v-else class="spinner"></span>
          {{ status === 'idle' ? 'Start Project Audit' : 'Analyzing...' }}
        </button>
        
        <button class="btn-ghost btn-lg" @click="$emit('analysis-complete')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
          View Last Report
        </button>
      </div>

      <!-- Pipeline Steps -->
      <transition name="fade">
        <div v-if="status !== 'idle'" class="pipeline">
          <div class="pipeline-steps">
            <div class="pipeline-step" :class="getStepClass(0)">
              <div class="step-indicator">
                <span v-if="getStepClass(0) === 'step-done'" class="step-check">✓</span>
                <span v-else-if="getStepClass(0) === 'step-active'" class="step-spinner"></span>
                <span v-else class="step-num">1</span>
              </div>
              <span class="step-label">Initialize</span>
            </div>
            <div class="pipeline-line" :class="{ 'line-active': pipelineStage >= 1 }"></div>
            <div class="pipeline-step" :class="getStepClass(1)">
              <div class="step-indicator">
                <span v-if="getStepClass(1) === 'step-done'" class="step-check">✓</span>
                <span v-else-if="getStepClass(1) === 'step-active'" class="step-spinner"></span>
                <span v-else class="step-num">2</span>
              </div>
              <span class="step-label">Analysis</span>
            </div>
            <div class="pipeline-line" :class="{ 'line-active': pipelineStage >= 2 }"></div>
            <div class="pipeline-step" :class="getStepClass(2)">
              <div class="step-indicator">
                <span v-if="getStepClass(2) === 'step-done'" class="step-check">✓</span>
                <span v-else-if="getStepClass(2) === 'step-active'" class="step-spinner"></span>
                <span v-else class="step-num">3</span>
              </div>
              <span class="step-label">AI Report</span>
            </div>
          </div>
          <p class="pipeline-message" :class="status">{{ message }}</p>

          <!-- Real-time Log Viewer -->
          <div v-if="logs.length > 0" class="log-viewer card card-flat" ref="logContainer">
            <div class="log-header">
                <div class="log-dot"></div>
                <span class="log-title">Live Pipeline Logs</span>
            </div>
            <div class="log-body custom-scrollbar">
              <div v-for="(log, idx) in logs" :key="idx" class="log-line" :class="{ 'log-err': log.includes('[ERROR]') }">
                <span class="log-timestamp">{{ formatTime(new Date()) }}</span>
                <span class="log-text">{{ log }}</span>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <!-- Feature Showcase -->
    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon" style="background:var(--accent-primary-subtle);color:var(--accent-primary)">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
        </div>
        <h4>AI-Powered Analysis</h4>
        <p>Gemini AI detects logic flaws, architectural anti-patterns, and semantic issues beyond static rules.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon" style="background:var(--accent-danger-subtle);color:var(--accent-danger)">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        </div>
        <h4>Accessibility Audit</h4>
        <p>Markuplint-based structural checks with AI false-positive filtering for real-world accuracy.</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon" style="background:var(--accent-success-subtle);color:var(--accent-success)">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        </div>
        <h4>Architecture Map</h4>
        <p>Interactive dependency graph with AI-generated architectural layer analysis and workflow detection.</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
export default {
  name: "Upload",
  data() {
    return { 
      message: "Ready to analyze current workspace.", 
      status: "idle", 
      pollInterval: null, 
      pipelineStage: 0,
      logs: [],
      sse: null,
      isVSCode: false,
      vscodePath: ""
    };
  },
  mounted() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('vscode') === 'true') {
      this.isVSCode = true;
      this.vscodePath = params.get('path');
      this.message = `VS Code Workspace: ${this.vscodePath}`;
    }
  },
  methods: {
    formatTime(date) { return date.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }); },
    getStepClass(stepIdx) {
      if (this.status === 'error') return stepIdx <= this.pipelineStage ? 'step-error' : 'step-pending';
      if (stepIdx < this.pipelineStage) return 'step-done';
      if (stepIdx === this.pipelineStage) return 'step-active';
      return 'step-pending';
    },
    async analyzeWorkspace() {
      if (!this.vscodePath) {
        this.status = "error";
        this.message = "Workspace path not provided by VS Code.";
        return;
      }
      this.message = "Preparing project fingerprint..."; this.status = "queued"; this.pipelineStage = 0;
      try {
        const res = await axios.post("/api/analyze-workspace", { path: this.vscodePath });
        this.message = res.data.msg; this.pipelineStage = 1;
        if (res.data.job_id) {
          this.pollStatus(res.data.job_id);
          this.startSSE(res.data.job_id);
        } else {
          this.$emit('analysis-complete');
        }
      } catch (err) { 
        this.status = "error"; 
        this.message = "Workspace analysis failed: " + (err.response?.data?.error || "Check server."); 
      }
    },
    pollStatus(jobId) {
      this.pollInterval = setInterval(async () => {
        try {
          const res = await axios.get(`/status/${jobId}`);
          const s = res.data.status;
          if (s === "running") { this.status = "running"; this.message = "AST parsing & AI analysis in progress..."; this.pipelineStage = 1; }
          else if (s === "done") { 
              clearInterval(this.pollInterval); 
              this.pipelineStage = 2; 
              this.message = "Analysis complete. Generating report..."; 
              this.status = "done"; 
              if (this.sse) this.sse.close();
              setTimeout(() => { this.pipelineStage = 3; this.$emit('analysis-complete'); }, 1200); 
          }
          else if (s === "error") { 
              clearInterval(this.pollInterval); 
              this.status = "error"; 
              this.message = "Analysis failed: " + (res.data.error || res.data.error_msg); 
              if (this.sse) this.sse.close();
          }
        } catch (err) { clearInterval(this.pollInterval); this.status = "error"; this.message = "Lost connection to backend."; }
      }, 2000);
    },
    startSSE(jobId) {
      if (this.sse) this.sse.close();
      this.logs = [];
      this.sse = new EventSource(`/progress/${jobId}`);
      this.sse.onmessage = (event) => {
        this.logs.push(event.data);
        this.$nextTick(() => { this.scrollToBottom(); });
      };
      this.sse.onerror = (e) => { console.log('SSE connection closed or error', e); };
    },
    scrollToBottom() {
      const container = this.$refs.logContainer;
      if (container) {
        const body = container.querySelector('.log-body');
        if (body) body.scrollTop = body.scrollHeight;
      }
    }
  },
  beforeUnmount() { if (this.pollInterval) clearInterval(this.pollInterval); }
};
</script>

<style scoped>
.upload-root { max-width:640px; margin:0 auto; animation:slideUp 0.5s var(--ease-out); }
.upload-card { padding:2rem; display:flex; flex-direction:column; gap:1.25rem; }

/* Workspace Info */
.workspace-info { padding:1.25rem; display:flex; align-items:center; gap:1rem; background:var(--bg-raised); border:1px solid var(--border-default); border-radius:var(--radius-lg); margin-bottom:0.5rem; }
.workspace-icon { width:40px; height:40px; border-radius:var(--radius-md); background:var(--accent-primary-subtle); color:var(--accent-primary); display:flex; align-items:center; justify-content:center; }
.workspace-details { display:flex; flex-direction:column; gap:0.25rem; overflow:hidden; }
.workspace-label { font-size:0.75rem; font-weight:600; color:var(--text-tertiary); text-transform:uppercase; letter-spacing:0.02em; }
.workspace-path { font-size:0.9rem; color:var(--text-primary); font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

/* Actions */
.upload-actions { display:flex; gap:0.75rem; }
.upload-btn { flex:1; }

/* Spinner */
.spinner { width:16px; height:16px; border:2px solid rgba(255,255,255,0.3); border-radius:50%; border-top-color:#fff; animation:spin 0.8s linear infinite; display:inline-block; }

/* Pipeline */
.pipeline { padding:1.25rem 0 0.25rem; display:flex; flex-direction:column; align-items:center; gap:1rem; animation:fadeIn 0.3s var(--ease-out); }
.pipeline-steps { display:flex; align-items:center; gap:0; width:100%; max-width:360px; }
.pipeline-step { display:flex; flex-direction:column; align-items:center; gap:0.4rem; flex-shrink:0; }
.step-indicator { width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700; border:2px solid var(--border-default); color:var(--text-tertiary); background:var(--bg-surface); transition:all var(--duration-normal) var(--ease-out); }
.step-label { font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.04em; color:var(--text-tertiary); transition:color var(--duration-normal); }
.pipeline-line { flex:1; height:2px; background:var(--border-default); margin:0 -0.25rem; margin-bottom:1.2rem; border-radius:1px; transition:background var(--duration-normal); }
.line-active { background:var(--accent-primary); }
.step-active .step-indicator { border-color:var(--accent-primary); color:var(--accent-primary); background:var(--accent-primary-subtle); box-shadow:0 0 0 4px var(--accent-primary-glow); }
.step-active .step-label { color:var(--accent-primary); }
.step-done .step-indicator { border-color:var(--accent-success); background:var(--accent-success); color:white; }
.step-done .step-label { color:var(--accent-success); }
.step-check { font-size:0.8rem; }
.step-error .step-indicator { border-color:var(--accent-danger); background:var(--accent-danger-subtle); color:var(--accent-danger); }
.step-error .step-label { color:var(--accent-danger); }
.step-spinner { width:14px; height:14px; border:2px solid var(--accent-primary-glow); border-radius:50%; border-top-color:var(--accent-primary); animation:spin 0.8s linear infinite; display:inline-block; }
.pipeline-message { font-size:0.85rem; font-weight:500; text-align:center; padding:0.6rem 1rem; border-radius:var(--radius-md); width:100%; }
.pipeline-message.queued, .pipeline-message.running { color:var(--accent-primary); background:var(--accent-primary-subtle); }
.pipeline-message.done { color:var(--accent-success); background:var(--accent-success-subtle); }
.pipeline-message.error { color:var(--accent-danger); background:var(--accent-danger-subtle); }

/* Log Viewer */
.log-viewer { width:100%; margin-top:1.5rem; background:var(--bg-inset); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); overflow:hidden; display:flex; flex-direction:column; max-height:300px; animation:slideUp 0.3s var(--ease-out); }
.log-header { padding:0.6rem 1rem; background:var(--bg-overlay); border-bottom:1px solid var(--border-subtle); display:flex; align-items:center; gap:0.6rem; }
.log-dot { width:8px; height:8px; background:var(--accent-primary); border-radius:50%; animation:pulse 2s infinite; }
.log-title { font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-tertiary); }
.log-body { flex:1; overflow-y:auto; padding:0.75rem; font-family:var(--font-mono); font-size:0.78rem; display:flex; flex-direction:column; gap:0.25rem; background:#0c0c12; }
.log-line { display:flex; gap:0.75rem; line-height:1.5; color:#a5a5b1; }
.log-timestamp { color:#5c5c6b; flex-shrink:0; pointer-events:none; }
.log-text { word-break:break-all; }
.log-err { color:var(--accent-danger-glow) !important; }

@keyframes pulse { 0% { opacity:1; } 50% { opacity:0.4; } 100% { opacity:1; } }

/* Feature Cards */
.features-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:1rem; margin-top:2rem; }
.feature-card { background:var(--bg-surface); border:1px solid var(--border-subtle); border-radius:var(--radius-lg); padding:1.5rem; transition:all var(--duration-normal) var(--ease-out); }
.feature-card:hover { box-shadow:var(--shadow-md); transform:translateY(-2px); border-color:var(--border-strong); }
.feature-icon { width:44px; height:44px; border-radius:var(--radius-md); display:flex; align-items:center; justify-content:center; margin-bottom:1rem; }
.feature-card h4 { font-size:0.95rem; margin-bottom:0.5rem; color:var(--text-primary); }
.feature-card p { font-size:0.82rem; color:var(--text-tertiary); line-height:1.5; margin:0; }
</style>