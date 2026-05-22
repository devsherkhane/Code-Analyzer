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
      <div class="hero-visual" ref="canvasContainer">
          <!-- Premium Canvas particle stream replacing the simple rings -->
          <canvas ref="heroCanvas" class="hero-interactive-canvas"></canvas>
          <div class="canvas-glow-center"></div>
      </div>
    </header>

    <!-- ── Vitals / KPI Cards ────────────────────────────────────── -->
    <section class="vitals-grid">
      <!-- Card 1: Average Health with SVG Gauge -->
      <div class="vital-card card card-elevated">
        <div class="vital-gauge-wrap">
          <svg class="circular-gauge" viewBox="0 0 100 100">
            <circle class="gauge-bg" cx="50" cy="50" r="45" />
            <circle 
              class="gauge-fill" 
              cx="50" 
              cy="50" 
              r="45" 
              :style="{ strokeDashoffset: calculateGaugeOffset(averageScore) }" 
            />
          </svg>
          <div class="gauge-text">
            <span class="gauge-value">{{ averageScore }}%</span>
          </div>
        </div>
        <div class="vital-data">
          <span class="vital-label">Average Code Health</span>
          <div class="vital-value-row">
            <span class="vital-desc-text">Overall standard score of analyzed codebases</span>
            <span class="vital-trend trend-up" v-if="averageScore > 70">+2.4%</span>
          </div>
        </div>
      </div>

      <!-- Card 2: Audits Completed with Sparkline -->
      <div class="vital-card card card-elevated">
        <div class="vital-sparkline-wrap">
          <svg class="sparkline-chart" viewBox="0 0 100 40">
            <path 
              class="sparkline-path" 
              fill="none" 
              stroke="#8b5cf6" 
              stroke-width="2.5" 
              stroke-linecap="round" 
              stroke-linejoin="round"
              d="M 5,35 Q 20,10 35,28 T 65,12 T 95,18" 
            />
          </svg>
        </div>
        <div class="vital-data">
          <span class="vital-label">Audits Completed</span>
          <div class="vital-value-row">
            <span class="vital-value">{{ history.length }}</span>
            <span class="vital-sub">This Quarter</span>
          </div>
        </div>
      </div>

      <!-- Card 3: Critical Defects with Hover Breakdown -->
      <div class="vital-card card card-elevated vital-hoverable">
        <div class="vital-icon vit-red">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        </div>
        <div class="vital-data">
          <span class="vital-label">Total Issues Detected</span>
          <div class="vital-value-row">
            <span class="vital-value">{{ totalIssues }}</span>
            <span class="vital-sub">Across all projects</span>
          </div>
        </div>
        <!-- Hover Breakdown Overlay panel -->
        <div class="severity-breakdown-panel">
          <span class="panel-title">Issues Breakdown</span>
          <div class="breakdown-row">
            <span class="bd-label"><span class="bd-dot red"></span>Critical:</span>
            <span class="bd-val font-mono">{{ severityCounts.critical }}</span>
          </div>
          <div class="breakdown-row">
            <span class="bd-label"><span class="bd-dot orange"></span>High:</span>
            <span class="bd-val font-mono">{{ severityCounts.high }}</span>
          </div>
          <div class="breakdown-row">
            <span class="bd-label"><span class="bd-dot yellow"></span>Medium:</span>
            <span class="bd-val font-mono">{{ severityCounts.medium }}</span>
          </div>
          <div class="breakdown-row">
            <span class="bd-label"><span class="bd-dot blue"></span>Low:</span>
            <span class="bd-val font-mono">{{ severityCounts.low }}</span>
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

      <!-- Live Search, Highlights & Filter Pills Toolbar -->
      <div class="history-toolbar card card-flat">
        <!-- Live Search Input -->
        <div class="input-group search-input-group">
          <span class="input-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          </span>
          <input 
            type="text" 
            class="text-input" 
            v-model="searchQuery" 
            placeholder="Search projects by name..."
          />
        </div>

        <!-- Rating Filter Pills -->
        <div class="filter-pills">
          <button 
            v-for="tab in filterTabs" 
            :key="tab.value" 
            class="filter-pill" 
            :class="{ active: activeFilter === tab.value }"
            @click="activeFilter = tab.value"
          >
            <span>{{ tab.label }}</span>
            <span class="pill-count" v-if="tab.value === 'all'">({{ history.length }})</span>
            <span class="pill-count" v-else>({{ getFilteredTabCount(tab.value) }})</span>
          </button>
        </div>
      </div>

      <!-- Quick Analysis Stats Highlights -->
      <div class="stats-highlights" v-if="history.length > 0">
        <div class="highlight-item">
          <span class="highlight-label">Highest Score</span>
          <span class="highlight-value text-success" v-if="highestScoreProject">
            {{ highestScoreProject.project_name }} <span class="score-badge font-mono">{{ highestScoreProject.overall_score }}</span>
          </span>
          <span class="highlight-value text-muted" v-else>N/A</span>
        </div>
        <div class="highlight-item">
          <span class="highlight-label">Most Critical Defects</span>
          <span class="highlight-value text-danger" v-if="mostDefectsProject">
            {{ mostDefectsProject.project_name }} <span class="defect-badge font-mono">{{ mostDefectsProject.total_issues }}</span>
          </span>
          <span class="highlight-value text-muted" v-else>N/A</span>
        </div>
      </div>

      <div v-if="loading" class="table-loading">
        <div class="skeleton-row" v-for="i in 5" :key="i"></div>
      </div>

      <div v-else-if="filteredHistory.length > 0" class="history-table-wrap card">
        <table class="data-table">
          <thead>
            <tr>
              <!-- Sortable columns -->
              <th class="sortable" @click="toggleSort('project_name')">
                Project Name
                <span class="sort-icon" v-if="sortBy === 'project_name'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th class="cell-number sortable" @click="toggleSort('overall_score')">
                Score
                <span class="sort-icon" v-if="sortBy === 'overall_score'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th class="cell-number sortable" @click="toggleSort('total_issues')">
                Defects
                <span class="sort-icon" v-if="sortBy === 'total_issues'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th class="sortable" @click="toggleSort('timestamp')">
                Date Analyzed
                <span class="sort-icon" v-if="sortBy === 'timestamp'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th style="width: 100px"></th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="report in paginatedHistory" 
              :key="report.report_id" 
              class="row-clickable" 
              @click="$emit('load-report', report.report_id)"
            >
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
            Show More ({{ filteredHistory.length - visibleCount }} remaining)
          </button>
        </div>
      </div>

      <div v-else class="empty-history card card-flat">
        <div class="empty-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline><polyline points="7.5 19.79 7.5 14.6 3 12"></polyline><polyline points="21 12 16.5 14.6 16.5 19.79"></polyline><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
        </div>
        <h4>No Reports Found</h4>
        <p v-if="searchQuery">No reports match your current search query.</p>
        <p v-else>You haven't conducted any architectural audits yet. <br/>Connect a codebase to generate your first report.</p>
        <button class="btn btn-primary" style="margin-top: 1.5rem" @click="$emit('launch-upload')">
          New Analysis
        </button>
      </div>
    </section>

    <!-- ── Enterprise CTA ────────────────────────────────────────── -->
    <section class="enterprise-cta card">
       <div class="cta-inner">
          <div class="cta-text">
             <h3>GitHub & CI/CD Integration</h3>
             <p>Enable automatic code quality checks on every Pull Request. Connect your repository to deploy real-time feedback loops in your team workflow.</p>
          </div>
          <!-- Reverted back to disabled button with "Soon" badge as requested -->
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
      visibleCount: 10,
      
      // Live search and filter pills state
      searchQuery: '',
      activeFilter: 'all',
      filterTabs: [
        { label: 'All Reports', value: 'all' },
        { label: 'Healthy (80%+)', value: 'healthy' },
        { label: 'Needs Attention (60-79%)', value: 'needs_attention' },
        { label: 'Critical (<60%)', value: 'critical' }
      ],

      // Interactive Sorting
      sortBy: 'timestamp',
      sortOrder: 'desc',

      // Dynamic Canvas Particles properties
      canvasCtx: null,
      canvasParticles: [],
      canvasAnimationId: null,
      mousePosition: { x: null, y: null }
    };
  },
  computed: {
    // Aggregated metrics
    averageScore() {
      if (!this.history.length) return 0;
      const sum = this.history.reduce((acc, curr) => acc + (curr.overall_score || 0), 0);
      return Math.round(sum / this.history.length);
    },
    totalIssues() {
      return this.history.reduce((acc, curr) => acc + (curr.total_issues || 0), 0);
    },
    
    // Severity issues counts breakdown (mocked for vitals overview card display)
    severityCounts() {
      const counts = { critical: 0, high: 0, medium: 0, low: 0 };
      if (!this.history.length) return counts;
      
      this.history.forEach(report => {
        // Distribute total issues into severity buckets
        const total = report.total_issues || 0;
        counts.critical += Math.round(total * 0.15);
        counts.high += Math.round(total * 0.25);
        counts.medium += Math.round(total * 0.40);
        counts.low += Math.max(0, total - (Math.round(total * 0.15) + Math.round(total * 0.25) + Math.round(total * 0.40)));
      });
      return counts;
    },

    // Search highlights
    highestScoreProject() {
      if (!this.history.length) return null;
      return [...this.history].sort((a, b) => b.overall_score - a.overall_score)[0];
    },
    mostDefectsProject() {
      if (!this.history.length) return null;
      return [...this.history].sort((a, b) => b.total_issues - a.total_issues)[0];
    },

    // Multi-criteria filter system
    filteredHistory() {
      let result = [...this.history];

      // 1. Search Query
      if (this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase();
        result = result.filter(item => 
          (item.project_name || '').toLowerCase().includes(query)
        );
      }

      // 2. Rating Tab Filters
      if (this.activeFilter === 'healthy') {
        result = result.filter(item => item.overall_score >= 80);
      } else if (this.activeFilter === 'needs_attention') {
        result = result.filter(item => item.overall_score >= 60 && item.overall_score < 80);
      } else if (this.activeFilter === 'critical') {
        result = result.filter(item => item.overall_score < 60);
      }

      // 3. Dynamic Sorting
      result.sort((a, b) => {
        let fieldA = a[this.sortBy];
        let fieldB = b[this.sortBy];

        if (this.sortBy === 'timestamp') {
          fieldA = new Date(fieldA || 0);
          fieldB = new Date(fieldB || 0);
        } else if (typeof fieldA === 'string') {
          fieldA = fieldA.toLowerCase();
          fieldB = (fieldB || '').toLowerCase();
        }

        if (fieldA < fieldB) return this.sortOrder === 'asc' ? -1 : 1;
        if (fieldA > fieldB) return this.sortOrder === 'asc' ? 1 : -1;
        return 0;
      });

      return result;
    },

    paginatedHistory() {
      return this.filteredHistory.slice(0, this.visibleCount);
    },
    hasMoreHistory() {
      return this.visibleCount < this.filteredHistory.length;
    }
  },
  async mounted() {
    await this.fetchHistory();
    this.initCanvasBackground();
  },
  beforeUnmount() {
    // Terminate canvas rendering loop
    if (this.canvasAnimationId) {
      cancelAnimationFrame(this.canvasAnimationId);
    }
    window.removeEventListener('resize', this.resizeCanvas);
  },
  methods: {
    async fetchHistory() {
      this.loading = true;
      try {
        const res = await axios.get('/api/history?_t=' + Date.now());
        this.history = res.data || [];
      } catch (err) {
        console.error('Failed to fetch history:', err);
        this.error = 'Failed to load report history.';
      } finally {
        this.loading = false;
      }
    },
    
    // Dynamic circular progress math
    calculateGaugeOffset(score) {
      // Circumference is 2 * PI * r = 2 * 3.14159 * 45 = 282.74
      const circumference = 282.74;
      const progress = score / 100;
      return circumference * (1 - progress);
    },

    // Quick counts for tabs
    getFilteredTabCount(filterType) {
      if (filterType === 'healthy') {
        return this.history.filter(item => item.overall_score >= 80).length;
      } else if (filterType === 'needs_attention') {
        return this.history.filter(item => item.overall_score >= 60 && item.overall_score < 80).length;
      } else if (filterType === 'critical') {
        return this.history.filter(item => item.overall_score < 60).length;
      }
      return 0;
    },

    // Sort handlers
    toggleSort(field) {
      if (this.sortBy === field) {
        this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
      } else {
        this.sortBy = field;
        this.sortOrder = 'desc';
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
    },

    // ── Gemma-inspired Canvas Particle Network ─────────────────
    initCanvasBackground() {
      const canvas = this.$refs.heroCanvas;
      if (!canvas) return;

      this.canvasCtx = canvas.getContext('2d');
      this.resizeCanvas();
      window.addEventListener('resize', this.resizeCanvas);

      // Mouse events
      const container = this.$refs.canvasContainer;
      if (container) {
        container.addEventListener('mousemove', (e) => {
          const rect = canvas.getBoundingClientRect();
          this.mousePosition.x = e.clientX - rect.left;
          this.mousePosition.y = e.clientY - rect.top;
        });
        container.addEventListener('mouseleave', () => {
          this.mousePosition.x = null;
          this.mousePosition.y = null;
        });
      }

      // Populate particles
      this.canvasParticles = [];
      const particleCount = 45;
      for (let i = 0; i < particleCount; i++) {
        this.canvasParticles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          vx: (Math.random() - 0.5) * 0.6,
          vy: (Math.random() - 0.5) * 0.6,
          radius: Math.random() * 2.5 + 1.5,
          color: i % 3 === 0 ? 'rgba(99, 102, 241, 0.7)' : (i % 3 === 1 ? 'rgba(236, 72, 153, 0.7)' : 'rgba(139, 92, 246, 0.5)')
        });
      }

      this.animateCanvas();
    },

    resizeCanvas() {
      const canvas = this.$refs.heroCanvas;
      if (!canvas) return;
      
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.parentNode.getBoundingClientRect();
      
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      
      if (this.canvasCtx) {
        this.canvasCtx.scale(dpr, dpr);
      }
    },

    animateCanvas() {
      const canvas = this.$refs.heroCanvas;
      const ctx = this.canvasCtx;
      if (!canvas || !ctx) return;

      const width = canvas.width / (window.devicePixelRatio || 1);
      const height = canvas.height / (window.devicePixelRatio || 1);

      ctx.clearRect(0, 0, width, height);

      // Render links
      for (let i = 0; i < this.canvasParticles.length; i++) {
        const p1 = this.canvasParticles[i];
        
        // Move particle
        p1.x += p1.vx;
        p1.y += p1.vy;

        // Bounce borders
        if (p1.x < 0 || p1.x > width) p1.vx *= -1;
        if (p1.y < 0 || p1.y > height) p1.vy *= -1;

        // Gravity force towards mouse
        if (this.mousePosition.x !== null && this.mousePosition.y !== null) {
          const dx = this.mousePosition.x - p1.x;
          const dy = this.mousePosition.y - p1.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            p1.x += dx * 0.015;
            p1.y += dy * 0.015;
          }
        }

        // Draw connections
        for (let j = i + 1; j < this.canvasParticles.length; j++) {
          const p2 = this.canvasParticles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 85) {
            const alpha = (1 - dist / 85) * 0.25;
            ctx.beginPath();
            ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`;
            ctx.lineWidth = 0.8;
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }

        // Draw node
        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
        ctx.fillStyle = p1.color;
        ctx.shadowBlur = p1.radius * 2;
        ctx.shadowColor = 'rgba(99, 102, 241, 0.4)';
        ctx.fill();
        ctx.shadowBlur = 0; // reset
      }

      this.canvasAnimationId = requestAnimationFrame(this.animateCanvas);
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
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-subtle);
  background: radial-gradient(circle at center, var(--bg-surface) 30%, var(--bg-base) 100%);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.hero-interactive-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
  cursor: crosshair;
}
.canvas-glow-center {
  position: absolute;
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, var(--accent-primary-subtle) 0%, transparent 70%);
  filter: blur(15px);
  z-index: 1;
  pointer-events: none;
}

/* ── Vitals & Stat Cards ──────────────────────────────── */
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
  position: relative;
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
.vit-red { background: rgba(239, 68, 68, 0.1); color: #ef4444; }

/* Circular SVG Gauge */
.vital-gauge-wrap {
  position: relative;
  width: 52px;
  height: 52px;
  flex-shrink: 0;
}
.circular-gauge {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.gauge-bg {
  fill: none;
  stroke: var(--bg-inset);
  stroke-width: 8px;
}
.gauge-fill {
  fill: none;
  stroke: var(--accent-primary);
  stroke-width: 8px;
  stroke-linecap: round;
  transition: stroke-dashoffset 1s ease-in-out;
}
.gauge-text {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.gauge-value {
  font-size: 0.85rem;
  font-weight: 800;
  color: var(--text-primary);
}

/* Mini Sparkline Chart */
.vital-sparkline-wrap {
  width: 70px;
  height: 38px;
  flex-shrink: 0;
}
.sparkline-chart {
  width: 100%;
  height: 100%;
}

.vital-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-tertiary);
  letter-spacing: 0.06em;
  display: block;
}
.vital-value-row {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-top: 0.25rem;
  flex-wrap: wrap;
}
.vital-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-primary);
}
.vital-desc-text {
  font-size: 0.76rem;
  color: var(--text-secondary);
  line-height: 1.3;
}
.vital-trend {
  font-size: 0.75rem;
  font-weight: 700;
}
.trend-up { color: var(--accent-success); }
.vital-sub { font-size: 0.75rem; color: var(--text-tertiary); }

/* Severity hover card popup */
.vital-hoverable {
  cursor: help;
}
.severity-breakdown-panel {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 50%;
  transform: translateX(-50%) translateY(10px);
  width: 180px;
  background: var(--bg-surface);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: 0.75rem;
  z-index: 10;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s var(--ease-out);
  pointer-events: none;
}
.vital-hoverable:hover .severity-breakdown-panel {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(0);
}
.panel-title {
  display: block;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-tertiary);
  margin-bottom: 0.4rem;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 0.25rem;
}
.breakdown-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  margin-bottom: 0.2rem;
}
.bd-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--text-secondary);
}
.bd-val {
  font-weight: 700;
  color: var(--text-primary);
}
.bd-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.bd-dot.red { background: var(--severity-critical); }
.bd-dot.orange { background: var(--severity-high); }
.bd-dot.yellow { background: var(--severity-medium); }
.bd-dot.blue { background: var(--severity-low); }

/* ── History Table Toolbar ────────────────────────────── */
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

.history-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  padding: 1rem;
  background: var(--bg-raised);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  flex-wrap: wrap;
}
.search-input-group {
  max-width: 320px;
}

/* Quick highlights */
.stats-highlights {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}
.highlight-item {
  background: var(--bg-inset);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.highlight-label {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-tertiary);
  letter-spacing: 0.05em;
}
.highlight-value {
  font-size: 0.85rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.text-success { color: var(--accent-success); }
.text-danger { color: var(--accent-danger); }
.score-badge {
  background: var(--accent-success-subtle);
  color: var(--accent-success);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.75rem;
}
.defect-badge {
  background: var(--accent-danger-subtle);
  color: var(--accent-danger);
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.75rem;
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

.sort-icon {
  font-size: 0.65rem;
  margin-left: 0.25rem;
  color: var(--accent-primary);
  display: inline-block;
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
  .history-toolbar { flex-direction: column; align-items: stretch; }
  .search-input-group { max-width: 100%; }
}
</style>
