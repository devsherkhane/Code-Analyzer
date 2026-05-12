<template>
  <div class="source-viewer">
    <div v-if="loading" class="viewer-state">
      <div class="spinner-sm"></div>
      <span>Loading source...</span>
    </div>
    <div v-else-if="error" class="viewer-state error-state">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
      <span>{{ error }}</span>
    </div>
    <div v-else class="code-container custom-scrollbar" ref="codeContainer">
      <div class="line-numbers">
        <div v-for="n in lineCount" :key="n" :id="'L'+n" class="line-number" :class="{ 'highlight-line': highlightedLines.includes(n) }">
          {{ n }}
        </div>
      </div>
      <div class="code-content-wrapper">
        <div class="code-line-bgs" aria-hidden="true">
          <div v-for="n in lineCount" :key="'bg'+n" class="line-bg" :class="{ 'hl-bg': highlightedLines.includes(n) }"></div>
        </div>
        <pre class="code-content"><code ref="codeBlock" :class="languageClass" v-html="highlightedHtml"></code></pre>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import Prism from 'prismjs';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-markup'; // For HTML/Vue

export default {
  name: 'SourceViewer',
  props: {
    filePath: { type: String, required: true },
    highlightedLines: { type: Array, default: () => [] }
  },
  data() {
    return {
      sourceCode: '',
      loading: true,
      error: null,
      lineCount: 0
    };
  },
  computed: {
    languageClass() {
      const ext = this.filePath.split('.').pop().toLowerCase();
      const map = {
        'vue': 'language-markup',
        'html': 'language-markup',
        'js': 'language-javascript',
        'ts': 'language-typescript',
        'css': 'language-css',
        'json': 'language-json'
      };
      return map[ext] || 'language-javascript';
    },
    highlightedHtml() {
      if (!this.sourceCode) return '';
      const ext = this.filePath.split('.').pop().toLowerCase();
      const map = {
        'vue': 'markup',
        'html': 'markup',
        'js': 'javascript',
        'ts': 'typescript',
        'css': 'css',
        'json': 'json'
      };
      const lang = map[ext] || 'javascript';
      const grammar = Prism.languages[lang] || Prism.languages.javascript;
      try {
        return Prism.highlight(this.sourceCode, grammar, lang);
      } catch (e) {
        return this.sourceCode.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      }
    }
  },
  watch: {
    filePath: {
      handler: 'fetchSource',
      immediate: true
    },
    highlightedLines: {
      handler: 'scrollToFirstHighlight',
      deep: true
    }
  },
  methods: {
    async fetchSource() {
      if (!this.filePath) return;
      this.loading = true;
      this.error = null;
      try {
        const res = await axios.get(`/file-content?path=${encodeURIComponent(this.filePath)}`);
        this.sourceCode = res.data;
        this.lineCount = this.sourceCode.split('\n').length;
        this.scrollToFirstHighlight();
      } catch (err) {
        this.error = 'Failed to load file content.';
      } finally {
        this.loading = false;
      }
    },
    scrollToFirstHighlight() {
      if (this.highlightedLines.length > 0) {
        this.$nextTick(() => {
          const el = document.getElementById('L' + this.highlightedLines[0]);
          if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        });
      }
    }
  }
};
</script>

<style scoped>
.source-viewer {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-inset);
  font-family: var(--font-mono);
  font-size: 0.82rem;
  line-height: 1.6;
  overflow: hidden;
  border-radius: var(--radius-md);
}

.viewer-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: var(--text-tertiary);
}

.error-state { color: var(--accent-danger); }

.code-container {
  display: flex;
  overflow: auto;
  height: 100%;
  position: relative;
}

.line-numbers {
  position: sticky;
  left: 0;
  z-index: 2;
  padding: 1rem 0;
  background: var(--bg-surface);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  text-align: right;
  user-select: none;
  flex-shrink: 0;
  min-width: 40px;
}

.line-number {
  padding: 0 0.75rem;
  color: var(--text-tertiary);
  font-size: inherit;
  height: 1.6em;
  line-height: inherit;
}

.highlight-line {
  background: var(--accent-danger-subtle);
  color: var(--accent-danger);
  font-weight: 700;
  border-left: 3px solid var(--accent-danger);
  padding-left: calc(0.75rem - 3px);
}

.code-content-wrapper {
  position: relative;
  flex: 1;
  min-width: max-content;
  display: flex;
}

.code-line-bgs {
  position: absolute;
  top: 1rem;
  left: 0;
  right: 0;
  z-index: 0;
  pointer-events: none;
}

.line-bg {
  height: 1.6em;
  width: 100%;
}

.hl-bg {
  background: var(--accent-danger-subtle);
}

.code-content {
  position: relative;
  z-index: 1;
  margin: 0;
  padding: 1rem;
  flex: 1;
}

.code-content code {
  color: var(--text-primary);
}

pre[class*="language-"] {
  background: transparent !important;
  margin: 0 !important;
  padding: 0 !important;
  line-height: inherit !important;
  font-size: inherit !important;
}

code[class*="language-"] {
  text-shadow: none !important;
  font-family: inherit !important;
  line-height: inherit !important;
  font-size: inherit !important;
}

.spinner-sm {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-subtle);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>
