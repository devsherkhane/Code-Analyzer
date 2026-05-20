<template>
  <div class="dashboard-root">
    <!-- ── Hero Section ─────────────────────────────────────────── -->
    <header class="dashboard-hero">
      <div class="hero-content">
        <div class="hero-label">Software Quality Intelligence</div>
        <h1 class="hero-title">Engineering Health <br/><span class="text-accent">Simplified with AI</span></h1>
        <p class="hero-desc">
          Connect your codebase for an automated architectural audit, accessibility check, 
          and structural triage powered by Gemma.
        </p>
        <div class="hero-actions">
          <button class="btn btn-primary btn-lg" @click="$emit('launch-upload')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
            Start New Analysis
          </button>
          <button class="btn btn-secondary btn-lg" @click="scrollToList">
            Browse History
          </button>
        </div>
      </div>
      <div class="hero-visual">
          <!-- Abstract AI Visual -->
          <div class="abstract-ring"></div>
          <div class="abstract-dot"></div>
      </div>
    </header>

    <!-- ── Vitals / KPI Cards ────────────────────────────────────── -->
    <section class="vitals-grid">
      <div class="vital-card card card-elevated">
        <div class="vital-icon vit-blue">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
        </div>
        <div class="vital-data">
          <span class="vital-label">Average Code Health</span>
          <div class="vital-value-row">
            <span class="vital-value">{{ averageScore }}%</span>
            <span class="vital-trend trend-up">+2.4%</span>
          </div>
        </div>
      </div>

      <div class="vital-card card card-elevated">
        <div class="vital-icon vit-purple">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
        </div>
        <div class="vital-data">
          <span class="vital-label">Audits Completed</span>
          <div class="vital-value-row">
            <span class="vital-value">{{ history.length }}</span>
            <span class="vital-sub">This Quarter</span>
          </div>
        </div>
      </div>

      <div class="vital-card card card-elevated">
        <div class="vital-icon vit-red">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        </div>
        <div class="vital-data">
          <span class="vital-label">Critical Defects Found</span>
          <div class="vital-value-row">
            <span class="vital-value">{{ totalIssues }}</span>
            <span class="vital-trend trend-down">-12% vs last mo</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Main History Table ────────────────────────────────────── -->
    <section id="history-list" class="history-section">
      <div class="section-head">
        <div class="head-left">
          <h3>Recent Analysis Reports</h3>
          <p>Access and compare your previous architectural audits.</p>
        </div>
        <div class="head-actions">
           <button class="btn btn-sm btn-ghost" @click="fetchHistory">
             <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'spin': loading }"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
             Refresh
           </button>
        </div>
      </div>

      <div v-if="loading" class="table-loading">
        <div class="skeleton-row" v-for="i in 5" :key="i"></div>
      </div>

      <div v-else-if="history.length > 0" class="history-table-wrap card">
        <table class="data-table">
          <thead>
            <tr>
              <th>Project Name</th>
              <th class="cell-number">Score</th>
              <th class="cell-number">Defects</th>
              <th>Date Analyzed</th>
              <th style="width: 100px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="report in paginatedHistory" :key="report.report_id" class="row-clickable" @click="$emit('load-report', report.report_id)">
              <td class="cell-primary">
                <div class="project-cell">
                   <div class="proj-icon">
                     <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
                   </div>
                   <span>{{ report.project_name || 'Unnamed Project' }}</span>
                </div>
              </td>
              <td class="cell-number">
                <span class="score-pill" :class="getScoreClass(report.overall_score)">
                  {{ report.overall_score }}
                </span>
              </td>
              <td class="cell-number">
                 <span class="issue-count">{{ report.total_issues }}</span>
              </td>
              <td class="cell-date">{{ formatDate(report.timestamp) }}</td>
              <td>
                <button class="btn btn-sm btn-ghost load-btn">Open →</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="hasMoreHistory" style="text-align:center; padding:1.25rem 0;">
          <button class="btn btn-sm btn-ghost" @click="visibleCount += 10">
            Show More ({{ history.length - visibleCount }} remaining)
          </button>
        </div>
      </div>

      <div v-else class="empty-history card card-flat">
        <div class="empty-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline><polyline points="7.5 19.79 7.5 14.6 3 12"></polyline><polyline points="21 12 16.5 14.6 16.5 19.79"></polyline><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
        </div>
        <h4>No Reports Found</h4>
        <p>You haven't conducted any architectural audits yet. <br/>Upload a project to generate your first report.</p>
        <button class="btn btn-primary" style="margin-top: 1.5rem" @click="$emit('launch-upload')">
          New Analysis
        </button>
      </div>
    </section>

    <!-- ── Enterprise CTA ────────────────────────────────────────── -->
    <section class="enterprise-cta card">
       <div class="cta-inner">
          <div class="cta-text">
             <h3>GitHub & CI Integration</h3>
             <p>Enable automatic audits on every Pull Request. Connect your repository to get instant feedback in your development workflow.</p>
          </div>
          <button class="btn btn-secondary disabled" title="Coming Soon">
            Connect GitHub
            <span class="badge badge-warning" style="margin-left: 0.5rem">Soon</span>
          </button>
       </div>
    </section>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Dashboard',
  emits: ['launch-upload', 'load-report'],
  data() {
    return {
      history: [],
      loading: true,
      error: null,
      visibleCount: 10
    };
  },
  computed: {
    averageScore() {
      if (!this.history.length) return 0;
      const sum = this.history.reduce((acc, curr) => acc + (curr.overall_score || 0), 0);
      return Math.round(sum / this.history.length);
    },
    totalIssues() {
      return this.history.reduce((acc, curr) => acc + (curr.total_issues || 0), 0);
    },
    paginatedHistory() {
      return this.history.slice(0, this.visibleCount);
    },
    hasMoreHistory() {
      return this.visibleCount < this.history.length;
    }
  },
  async mounted() {
    await this.fetchHistory();
  },
  methods: {
    async fetchHistory() {
      this.loading = true;
      try {
        const res = await axios.get('/api/history?_t=' + Date.now());
        // Sort by timestamp descending
        this.history = (res.data || []).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      } catch (err) {
        console.error('Failed to fetch history:', err);
        this.error = 'Failed to load report history.';
      } finally {
        this.loading = false;
      }
    },
    getScoreClass(score) {
      if (score >= 80) return 'sc-high';
      if (score >= 60) return 'sc-mid';
      return 'sc-low';
    },
    formatDate(ts) {
      if (!ts) return 'Unknown';
      const d = new Date(ts);
      return d.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    scrollToList() {
      document.getElementById('history-list')?.scrollIntoView({ behavior: 'smooth' });
    }
  }
};
</script>

<style scoped>
.dashboard-root {
  display: flex;
  flex-direction: column;
  gap: 3.5rem;
  padding-bottom: 4rem;
  animation: slideUp 0.6s var(--ease-out);
}

/* ── Hero ────────────────────────────────────────────── */
.dashboard-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3rem 0;
  gap: 2rem;
  position: relative;
}
.hero-content {
  flex: 1;
  max-width: 640px;
}
.hero-label {
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--accent-primary);
  margin-bottom: 1rem;
}
.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 1.5rem;
  letter-spacing: -0.04em;
  color: var(--text-primary);
}
.text-accent {
  background: linear-gradient(135deg, var(--accent-primary), #ec4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-desc {
  font-size: 1.125rem;
  color: var(--text-secondary);
  margin-bottom: 2.5rem;
  max-width: 520px;
  line-height: 1.6;
}
.hero-actions {
  display: flex;
  gap: 1rem;
}

.hero-visual {
  flex-shrink: 0;
  width: 400px;
  height: 400px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
}
.abstract-ring {
  width: 280px;
  height: 280px;
  border: 40px solid var(--accent-primary-subtle);
  border-radius: 50%;
  filter: blur(20px);
  animation: pulse 4s infinite ease-in-out;
}
.abstract-dot {
  position: absolute;
  width: 40px;
  height: 40px;
  background: var(--accent-primary);
  border-radius: 50%;
  box-shadow: 0 0 30px var(--accent-primary-glow);
  animation: orbit 8s infinite linear;
}

@keyframes orbit {
  from { transform: rotate(0deg) translateX(160px) rotate(0deg); }
  to { transform: rotate(360deg) translateX(160px) rotate(-360deg); }
}

/* ── Vitals ──────────────────────────────────────────── */
.vitals-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}
.vital-card {
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.25rem;
}
.vital-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.vit-blue { background: rgba(59, 130, 246, 0.1); color: #3b82f6; }
.vit-purple { background: rgba(139, 92, 246, 0.1); color: #8b5cf6; }
.vit-red { background: rgba(239, 68, 68, 0.1); color: #ef4444; }

.vital-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-tertiary);
  letter-spacing: 0.05em;
  display: block;
}
.vital-value-row {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-top: 0.25rem;
}
.vital-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-primary);
}
.vital-trend {
  font-size: 0.75rem;
  font-weight: 700;
}
.trend-up { color: var(--accent-success); }
.trend-down { color: var(--accent-danger); }
.vital-sub { font-size: 0.7rem; color: var(--text-tertiary); }

/* ── History Table ───────────────────────────────────── */
.history-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}
.section-head h3 {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}
.head-left p {
  font-size: 0.9375rem;
  color: var(--text-secondary);
}

.project-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.proj-icon {
  width: 28px;
  height: 28px;
  background: var(--bg-inset);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  transition: all 0.2s;
}
.row-clickable:hover .proj-icon {
  background: var(--accent-primary-subtle);
  color: var(--accent-primary);
}

.score-pill {
  display: inline-flex;
  padding: 0.25rem 0.75rem;
  border-radius: 99px;
  font-weight: 700;
  font-size: 0.8rem;
}
.sc-high { background: var(--accent-success-subtle); color: var(--accent-success); }
.sc-mid { background: var(--accent-warning-subtle); color: var(--accent-warning); }
.sc-low { background: var(--accent-danger-subtle); color: var(--accent-danger); }

.cell-date {
  font-size: 0.85rem;
  color: var(--text-tertiary);
}
.load-btn {
  opacity: 0;
  transform: translateX(-10px);
  transition: all 0.2s var(--ease-out);
}
.row-clickable:hover .load-btn {
  opacity: 1;
  transform: translateX(0);
}

/* ── Empty State ─────────────────────────────────────── */
.empty-history {
  padding: 5rem 2rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--bg-surface);
  border: 1px dashed var(--border-default);
}
.empty-icon {
  width: 80px;
  height: 80px;
  background: var(--bg-inset);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  margin-bottom: 2rem;
}
.empty-history h4 {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
}
.empty-history p {
  max-width: 320px;
}

/* ── Enterprise CTA ──────────────────────────────────── */
.enterprise-cta {
  padding: 2.5rem;
  background: linear-gradient(90deg, var(--bg-surface), var(--bg-raised));
  border-color: var(--accent-primary-glow);
}
.cta-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}
.cta-text h3 {
  margin-bottom: 0.5rem;
  color: var(--accent-primary);
}
.cta-text p {
  max-width: 600px;
  font-size: 0.9375rem;
}

.spin {
  animation: spin 1s linear infinite;
}

@media (max-width: 1024px) {
  .vitals-grid { grid-template-columns: 1fr; }
  .dashboard-hero { flex-direction: column; text-align: center; padding-top: 1rem; }
  .hero-content { max-width: 100%; }
  .hero-actions { justify-content: center; }
  .hero-visual { width: 300px; height: 300px; }
  .cta-inner { flex-direction: column; text-align: center; }
}
</style>
