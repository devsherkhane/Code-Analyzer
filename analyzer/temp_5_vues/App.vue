<script>
import Upload from './components/Upload.vue';
import AIReport from './components/AIReport.vue';
import DependencyGraph from './components/DependencyGraph.vue';
import Dashboard from './components/Dashboard.vue';

export default {
  components: { Upload, AIReport, DependencyGraph, Dashboard },
  data() {
    return {
      analysisDone: false,
      activeView: 'dashboard', // 'dashboard' | 'overview' | 'issues' | 'files' | 'architecture'
      theme: 'dark'
    }
  },
  created() {
    const saved = localStorage.getItem('va-theme');
    this.theme = saved || 'dark';
    document.documentElement.setAttribute('data-theme', this.theme);
  },
  computed: {
    breadcrumb() {
      const labels = {
        dashboard: 'Enterprise Dashboard',
        overview: 'Overview',
        issues: 'Issues',
        files: 'File Inspector',
        architecture: 'Architecture Map'
      };
      return labels[this.activeView] || 'Overview';
    }
  },
  methods: {
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', this.theme);
      localStorage.setItem('va-theme', this.theme);
    },
    goHome() {
      this.analysisDone = false;
      this.activeView = 'dashboard';
    },
    loadReport(reportId) {
        // Logic to point the app to a specific historical report
        // For now, our app always reads ai_report.json which is a copy of Latest.
        // In a full implementation, we'd pass the reportId to components.
        this.analysisDone = true;
        this.activeView = 'overview';
    },
    printReport() {
      window.print();
    }
  }
}
</script>

<template>
  <div class="app-shell">
    <!-- ── Top Navigation Bar ─────────────────────────────────────── -->
    <nav class="topbar">
      <div class="topbar-inner">
        <div class="topbar-left">
          <div class="topbar-brand" @click="goHome" style="cursor:pointer;">
            <div class="brand-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polygon>
                <line x1="12" y1="22" x2="12" y2="15.5"></line>
                <polyline points="22 8.5 12 15.5 2 8.5"></polyline>
                <polyline points="2 15.5 12 8.5 22 15.5"></polyline>
                <line x1="12" y1="2" x2="12" y2="8.5"></line>
              </svg>
            </div>
            <span class="brand-name">Vue<span class="brand-accent">Analyzer</span></span>
          </div>

          <!-- Breadcrumb in report mode -->
          <div v-if="analysisDone" class="breadcrumb">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
            <span class="breadcrumb-text">{{ breadcrumb }}</span>
          </div>
        </div>

        <div class="topbar-actions">
          <div class="topbar-status" v-if="analysisDone">
            <span class="status-dot"></span>
            Report Active
          </div>
          <button v-if="analysisDone" class="btn-ghost btn-pdf" @click="printReport" title="Export PDF">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9V2h12v7"></path><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><rect x="6" y="14" width="12" height="8"></rect></svg>
            <span class="btn-label">Export PDF</span>
          </button>
          <button class="btn-ghost theme-toggle" @click="toggleTheme" :title="theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'">
            <!-- Sun icon -->
            <svg v-if="theme === 'dark'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="5"></circle>
              <line x1="12" y1="1" x2="12" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="23"></line>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
              <line x1="1" y1="12" x2="3" y2="12"></line>
              <line x1="21" y1="12" x2="23" y2="12"></line>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
            </svg>
            <!-- Moon icon -->
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
            </svg>
          </button>
        </div>
      </div>
    </nav>

    <!-- ── Main Layout ───────────────────────────────────────────── -->
    <div class="app-body">
      <transition name="fade" mode="out-in">
        <!-- Dashboard / Upload View -->
        <div v-if="!analysisDone" key="dashboard" class="upload-view">
          <Dashboard v-if="activeView === 'dashboard'" @load-report="loadReport" @launch-upload="activeView = 'upload'" />
          
          <template v-else>
            <div class="hero-section">
                <div class="hero-badge">AI-Powered Analysis</div>
                <h1 class="hero-title">Start New Analysis</h1>
                <p class="hero-subtitle">Upload your Vue.js project for AI-powered architectural insights and accessibility audits.</p>
            </div>
            <Upload @analysis-complete="analysisDone = true; activeView = 'overview'" />
          </template>
        </div>

        <!-- Report View with Sidebar -->
        <div v-else key="report" class="report-layout">
          <!-- Sidebar Navigation -->
          <aside class="sidebar-nav">
            <div class="nav-section">
              <div class="nav-section-label">Enterprise</div>
              <button
                class="nav-item"
                :class="{ active: activeView === 'dashboard' }"
                @click="goHome"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
                <span>Dashboard</span>
              </button>
            </div>

            <div class="nav-section">
              <div class="nav-section-label">Analysis</div>
              <button
                class="nav-item"
                :class="{ active: activeView === 'overview' }"
                @click="activeView = 'overview'"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
                <span>Overview</span>
              </button>
              <button
                class="nav-item"
                :class="{ active: activeView === 'issues' }"
                @click="activeView = 'issues'"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                <span>Issues</span>
              </button>
              <button
                class="nav-item"
                :class="{ active: activeView === 'files' }"
                @click="activeView = 'files'"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                <span>File Inspector</span>
              </button>
            </div>

            <div class="nav-section">
              <div class="nav-section-label">Visualization</div>
              <button
                class="nav-item"
                :class="{ active: activeView === 'architecture' }"
                @click="activeView = 'architecture'"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                <span>Architecture</span>
              </button>
            </div>

            <!-- Sidebar Footer -->
            <div class="nav-footer">
              <button class="nav-item nav-item-back" @click="goHome">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                <span>New Analysis</span>
              </button>
            </div>
          </aside>

          <!-- Main Content -->
          <main class="report-main">
            <transition name="fade" mode="out-in">
              <AIReport
                v-if="activeView === 'overview' || activeView === 'issues' || activeView === 'files'"
                :activeView="activeView"
                @navigate="activeView = $event"
                :key="activeView"
              />
              <DependencyGraph v-else-if="activeView === 'architecture'" key="dep-graph" />
            </transition>
          </main>
        </div>
      </transition>
    </div>

    <!-- ── Footer ─────────────────────────────────────────────────── -->
    <footer class="app-footer">
      <span>VueAnalyzer v2.0 · Built with Vue 3 · Gemini AI · Markuplint</span>
    </footer>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ── Topbar ──────────────────────────────────────────── */
.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  background: var(--bg-overlay);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-subtle);
}
.topbar-inner {
  margin: 0 auto;
  padding: 0 1.5rem;
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.topbar-brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.brand-icon {
  color: var(--accent-primary);
  display: flex;
}
.brand-name {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}
.brand-accent {
  color: var(--accent-primary);
}

/* Breadcrumb */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--text-tertiary);
}
.breadcrumb-text {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.topbar-status {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--accent-success);
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-success);
  animation: pulse 2s ease-in-out infinite;
}
.theme-toggle {
  padding: 0.45rem;
  border-radius: var(--radius-md);
}

/* ── App Body ────────────────────────────────────────── */
.app-body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* ── Upload View ─────────────────────────────────────── */
.upload-view {
  max-width: 1280px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}
.hero-section {
  text-align: center;
  margin-bottom: 2.5rem;
  padding-top: 1.5rem;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.9rem;
  background: var(--accent-primary-subtle);
  border: 1px solid var(--accent-primary-glow);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent-primary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 1.25rem;
}
.hero-title {
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 0.6rem;
  background: linear-gradient(135deg, var(--text-primary), var(--accent-primary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-subtitle {
  font-size: 1.0625rem;
  color: var(--text-secondary);
  max-width: 540px;
  margin: 0 auto;
  font-weight: 400;
}

/* ── Report Layout (Sidebar + Main) ──────────────────── */
.report-layout {
  display: flex;
  flex: 1;
  min-height: calc(100vh - var(--topbar-height) - 40px);
}

/* ── Sidebar Nav ─────────────────────────────────────── */
.sidebar-nav {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  padding: 1rem 0.75rem;
  gap: 0.5rem;
  position: sticky;
  top: var(--topbar-height);
  height: calc(100vh - var(--topbar-height));
  overflow-y: auto;
}
.nav-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-section-label {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
  padding: 0.5rem 0.75rem 0.35rem;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.6rem 0.75rem;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  width: 100%;
  text-align: left;
}
.nav-item:hover {
  background: var(--bg-surface-hover);
  color: var(--text-primary);
  border-color: transparent;
}
.nav-item.active {
  background: var(--accent-primary-subtle);
  color: var(--accent-primary);
  border-color: var(--accent-primary-glow);
  font-weight: 600;
}
.nav-item.active svg {
  color: var(--accent-primary);
}
.nav-item svg {
  flex-shrink: 0;
  opacity: 0.7;
}
.nav-item:hover svg {
  opacity: 1;
}
.nav-item.active svg {
  opacity: 1;
}
.nav-footer {
  margin-top: auto;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-subtle);
}
.nav-item-back {
  color: var(--text-tertiary);
  font-size: 0.8rem;
}

/* ── Report Main ─────────────────────────────────────── */
.report-main {
  flex: 1;
  min-width: 0;
  padding: 1.5rem 2rem;
  overflow-y: auto;
  max-height: calc(100vh - var(--topbar-height));
}

/* ── Footer ──────────────────────────────────────────── */
.app-footer {
  text-align: center;
  padding: 1rem;
  font-size: 0.72rem;
  color: var(--text-tertiary);
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
  letter-spacing: 0.02em;
}
</style>
