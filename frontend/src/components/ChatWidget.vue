<template>
  <div class="chat-section">
    <div class="chat-window">
      <div class="chat-header">
        <h4>AI Workspace Assistant</h4>
        
        <div class="context-toggle">
          <button class="btn-ghost btn-sm" @click="clearHistory" title="Clear Chat History">
             <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6V20a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
             Clear
          </button>
          <label class="switch-label" style="margin-left: 10px;">Context:</label>
          <select v-model="contextType" class="modern-select">
            <option value="workspace">Entire Workspace</option>
            <optgroup label="Files">
              <option v-for="f in allFiles" :key="f.file_path" :value="f.file_path">
                {{ f.file_name }}
              </option>
            </optgroup>
          </select>
        </div>
      </div>
      
      <div class="chat-messages" ref="msgContainer">
        <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
          <div class="msg-bubble markdown-body" v-html="renderMarkdown(msg.content)"></div>
        </div>
        <div v-if="loading" class="msg assistant loading">
          <div class="msg-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>
        </div>
      </div>
      
      <!-- Attached Issue Context Card -->
      <transition name="slide-fade">
        <div v-if="attachedIssue" class="attached-issue-card">
          <div class="aic-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            <span>Issue Attached</span>
            <button class="aic-dismiss" @click="dismissAttachedIssue" title="Remove attached issue">&times;</button>
          </div>
          <div class="aic-body">
            <span class="aic-type">{{ attachedIssue.defect_type || attachedIssue.problem || 'Issue' }}</span>
            <span class="aic-file" v-if="attachedIssue._fileName">in {{ attachedIssue._fileName }}</span>
          </div>
        </div>
      </transition>

      <!-- Issue Picker Dropdown -->
      <transition name="slide-fade">
        <div v-if="issuePickerOpen" class="issue-picker" v-click-outside="closeIssuePicker">
          <div class="picker-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
            <input type="text" v-model="issuePickerSearch" placeholder="Search issues..." class="picker-search" ref="pickerSearch" />
          </div>
          <div class="picker-list">
            <div v-if="filteredPickerIssues.length === 0" class="picker-empty">No issues found</div>
            <template v-for="(issues, fileName) in groupedPickerIssues" :key="fileName">
              <div class="picker-group-label">{{ fileName }}</div>
              <div v-for="(issue, idx) in issues" :key="fileName + idx" class="picker-item" @click="attachIssueFromPicker(issue)">
                <span class="picker-sev" :class="'sev-' + (issue._severity || 'medium')"></span>
                <span class="picker-issue-text">{{ issue.defect_type || issue.problem || 'Issue' }}</span>
                <span class="picker-source">{{ issue._source }}</span>
              </div>
            </template>
          </div>
        </div>
      </transition>

      <div class="chat-input-area">
        <button class="attach-btn" @click="toggleIssuePicker" title="Attach an issue">
          <span style="font-size: 28px; line-height: 1; font-weight: 400; color: inherit; display: inline-block; transform: translateY(-1px);">+</span>
        </button>
        <input 
          v-model="inputText" 
          @keyup.enter="sendMessage"
          :placeholder="attachedIssue ? 'Ask about this issue or press Enter to discuss...' : 'Ask about your code...'"
          type="text"
          ref="chatInput"
        />
        <button class="send-btn" @click="sendMessage" :disabled="loading || (!inputText.trim() && !attachedIssue)">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { marked } from 'marked';

export default {
  name: 'ChatWidget',
  directives: {
    'click-outside': {
      mounted(el, binding) {
        el._clickOutside = (e) => {
          if (!el.contains(e.target) && !e.target.closest('.attach-btn')) {
            binding.value();
          }
        };
        document.addEventListener('click', el._clickOutside);
      },
      unmounted(el) {
        document.removeEventListener('click', el._clickOutside);
      }
    }
  },
  props: {
    activeFile: { type: Object, default: null },
    workspacePath: { type: String, default: '' },
    allFiles: { type: Array, default: () => [] },
    injectedIssue: { type: Object, default: null },
    allIssues: { type: Array, default: () => [] }
  },
  data() {
    return {
      contextType: 'workspace',
      inputText: '',
      messages: [
        { role: 'assistant', content: 'Hello! I am your AI architect. Ask me anything about your project or currently opened file.' }
      ],
      loading: false,
      attachedIssue: null,
      issuePickerOpen: false,
      issuePickerSearch: ''
    };
  },
  mounted() {
    this.loadHistory();
  },
  watch: {
    activeFile: {
      handler(val) {
        if (val) {
          this.contextType = val.file_path;
        } else if (this.allFiles && this.allFiles.length === 0) {
          this.contextType = 'workspace';
        }
      },
      immediate: true,
      deep: true
    },
    injectedIssue: {
      handler(issue) {
        if (issue) {
          this.attachedIssue = { ...issue };
          // Set context to the file containing the issue
          if (issue._fileName) {
            const matchedFile = this.allFiles.find(f => f.file_name === issue._fileName);
            if (matchedFile) this.contextType = matchedFile.file_path;
          }
          // Auto-send the issue discussion prompt
          this.$nextTick(() => {
            this.sendIssueToChat(issue);
          });
        }
      },
      immediate: true,
      deep: true
    }
  },
  computed: {
    filteredPickerIssues() {
      if (!this.allIssues) return [];
      const q = this.issuePickerSearch.toLowerCase().trim();
      if (!q) return this.allIssues;
      return this.allIssues.filter(i =>
        (i.defect_type || '').toLowerCase().includes(q) ||
        (i.problem || '').toLowerCase().includes(q) ||
        (i._fileName || '').toLowerCase().includes(q) ||
        (i._source || '').toLowerCase().includes(q)
      );
    },
    groupedPickerIssues() {
      const groups = {};
      this.filteredPickerIssues.forEach(i => {
        const fn = i._fileName || 'Unknown';
        if (!groups[fn]) groups[fn] = [];
        groups[fn].push(i);
      });
      return groups;
    }
  },
  methods: {
    loadHistory() {
      try {
        const key = `uiux_chat_${this.workspacePath || 'global'}`;
        const saved = localStorage.getItem(key);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed && parsed.length > 0) {
            this.messages = parsed;
            this.scrollToBottom();
          }
        }
      } catch (e) {
        console.warn("Could not load chat history");
      }
    },
    saveHistory() {
      try {
        const key = `uiux_chat_${this.workspacePath || 'global'}`;
        localStorage.setItem(key, JSON.stringify(this.messages));
      } catch (e) {}
    },
    renderMarkdown(text) {
      return marked.parse(text);
    },
    async sendMessage() {
      // Allow sending with attached issue even if input is empty
      if (!this.inputText.trim() && !this.attachedIssue) return;
      
      // If there's an attached issue and no custom text, build a default prompt
      if (!this.inputText.trim() && this.attachedIssue) {
        this.inputText = 'Can you explain this issue in detail and suggest the best way to fix it?';
      }
      
      const userMsg = this.inputText.trim();
      this.messages.push({ role: 'user', content: userMsg });
      this.saveHistory();
      this.inputText = '';
      this.loading = true;
      
      this.scrollToBottom();
      
      try {
        const historyPayload = this.messages.slice(1, -1).map(m => ({ role: m.role, content: m.content }));
        let activeFileName = '';
        let activeContent = '';

        if (this.contextType !== 'workspace') {
           const selected = this.allFiles.find(f => f.file_path === this.contextType);
           if (selected) {
             activeFileName = selected.file_name;
             const res = await axios.get(`http://127.0.0.1:8081/file-content?path=${encodeURIComponent(selected.file_path)}`);
             activeContent = res.data;
           }
        }

        const payload = {
          message: userMsg,
          contextType: this.contextType === 'workspace' ? 'workspace' : 'file',
          workspacePath: this.workspacePath,
          activeFileName: activeFileName,
          activeContent: activeContent,
          history: historyPayload
        };

        const response = await axios.post('http://127.0.0.1:7891/chat', payload);
        this.messages.push({ role: 'assistant', content: response.data.response });
        this.saveHistory();
      } catch (e) {
        this.messages.push({ role: 'assistant', content: `**Error**: ${e.response?.data?.error || e.message}` });
        this.saveHistory();
      } finally {
        this.loading = false;
        this.scrollToBottom();
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.msgContainer) {
           this.$refs.msgContainer.scrollTop = this.$refs.msgContainer.scrollHeight;
        }
      });
    },
    clearHistory() {
      this.messages = [
        { role: 'assistant', content: 'History cleared. How can I assist you now?' }
      ];
      this.attachedIssue = null;
      this.saveHistory();
    },
    dismissAttachedIssue() {
      this.attachedIssue = null;
    },
    toggleIssuePicker() {
      this.issuePickerOpen = !this.issuePickerOpen;
      if (this.issuePickerOpen) {
        this.issuePickerSearch = '';
        this.$nextTick(() => {
          if (this.$refs.pickerSearch) this.$refs.pickerSearch.focus();
        });
      }
    },
    closeIssuePicker() {
      this.issuePickerOpen = false;
    },
    attachIssueFromPicker(issue) {
      this.attachedIssue = { ...issue };
      this.issuePickerOpen = false;
      // Set context to the file containing the issue
      if (issue._fileName) {
        const matchedFile = this.allFiles.find(f => f.file_name === issue._fileName);
        if (matchedFile) this.contextType = matchedFile.file_path;
      }
      // Auto-send the issue prompt — same as "Discuss with AI"
      this.$nextTick(() => {
        this.sendIssueToChat(issue);
      });
    },
    buildIssuePrompt(issue) {
      let prompt = `I found this issue in my code and need help understanding and fixing it:\n\n`;
      prompt += `**Issue Type:** ${issue.defect_type || issue.problem || 'Unknown'}\n`;
      if (issue._fileName) prompt += `**File:** ${issue._fileName}\n`;
      if (issue.line_number || issue.line) prompt += `**Line:** ${issue.line_number || issue.line}\n`;
      if (issue.wcag_rule) prompt += `**WCAG Rule:** ${issue.wcag_rule}\n`;
      if (issue._source) prompt += `**Detected By:** ${issue._source}\n`;
      if (issue.rationale) prompt += `\n**AI Rationale:** ${issue.rationale}\n`;
      if (issue.suggestion || issue.explanation) prompt += `\n**Suggested Fix:** ${issue.suggestion || issue.explanation}\n`;
      if (issue.original_code_snippet || issue.original_code) prompt += `\n**Original Code:**\n\`\`\`\n${issue.original_code_snippet || issue.original_code}\n\`\`\`\n`;
      if (issue.fixed_code_snippet || issue.fixed_code) prompt += `\n**Proposed Fix:**\n\`\`\`\n${issue.fixed_code_snippet || issue.fixed_code}\n\`\`\`\n`;
      prompt += `\nPlease explain this issue in detail, why it matters, and provide the best approach to fix it.`;
      return prompt;
    },
    async sendIssueToChat(issue) {
      const prompt = this.buildIssuePrompt(issue);
      this.inputText = prompt;
      await this.$nextTick();
      this.sendMessage();
    }
  }
};
</script>

<style scoped>
.chat-section {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  font-family: var(--font-primary);
  box-sizing: border-box;
}

.chat-window {
  flex: 1;
  width: 100%;
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  animation: slideUp 0.3s forwards cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-header {
  padding: 1.25rem 1rem;
  background: var(--bg-inset);
  border-bottom: 1px solid var(--border-subtle);
}
.chat-header h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1.05rem;
  color: var(--text-primary);
  font-weight: 600;
  letter-spacing: -0.01em;
}
.context-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.modern-select {
  background: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--border-subtle);
  padding: 0.3rem 0.5rem;
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  outline: none;
  flex: 1;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.msg {
  display: flex;
  flex-direction: column;
  max-width: 90%;
}
.msg.user {
  align-self: flex-end;
}
.msg.assistant {
  align-self: flex-start;
}
.msg-bubble {
  padding: 0.75rem 1rem;
  border-radius: 14px;
  font-size: 0.9rem;
  line-height: 1.5;
  word-wrap: break-word;
}
.msg.user .msg-bubble {
  background: var(--accent-primary);
  color: #ffffff !important;
  border-bottom-right-radius: 4px;
}
.msg.user .msg-bubble :deep(*) {
  color: #ffffff !important;
}
.msg.assistant .msg-bubble {
  background: var(--bg-inset);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
}

/* Ensure markdown renders clean */
.markdown-body :deep(pre) {
    background: #1e1e1e !important;
    color: #d4d4d4 !important;
    padding: 0.75rem !important;
    border-radius: var(--radius-sm) !important;
    overflow-x: auto;
    font-size: 0.85em;
    margin: 0.5rem 0;
}
.markdown-body :deep(code) {
    background: var(--bg-inset) !important;
    color: var(--text-primary) !important;
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
    font-family: var(--font-mono);
    font-size: 0.9em;
}
.markdown-body :deep(pre code) {
    background: transparent !important;
    color: inherit !important;
}
.markdown-body :deep(p) { margin: 0 0 0.5rem 0; }
.markdown-body :deep(p:last-child) { margin: 0; }

.chat-input-area {
  padding: 1rem;
  background: var(--bg-surface);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  gap: 0.5rem;
  align-items: center;
}
.chat-input-area input {
  flex: 1;
  background: var(--bg-inset);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.75rem 1rem;
  border-radius: 20px;
  outline: none;
  font-size: 0.95rem;
  transition: border-color 0.2s;
}
.chat-input-area input:focus {
  border-color: var(--accent-primary);
}
.send-btn {
  background: var(--accent-primary);
  color: #fff;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: scale(0.95);
}
.send-btn:not(:disabled):hover {
  filter: brightness(1.1);
  transform: scale(1.05);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0.2rem;
}
.typing-indicator span {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--text-tertiary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* ── Attached Issue Card ─────────────────────────── */
.attached-issue-card {
  margin: 0 1rem;
  padding: 0.65rem 0.85rem;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.08), rgba(59, 130, 246, 0.08));
  border: 1px solid rgba(139, 92, 246, 0.25);
  border-radius: var(--radius-md, 8px);
  animation: slideUp 0.3s forwards cubic-bezier(0.16, 1, 0.3, 1);
}
.aic-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #a78bfa;
  margin-bottom: 0.3rem;
}
.aic-dismiss {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
  padding: 0 0.2rem;
  transition: color 0.2s;
}
.aic-dismiss:hover { color: var(--accent-danger, #ef4444); }
.aic-body {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.aic-type {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
}
.aic-file {
  font-size: 0.72rem;
  color: var(--text-tertiary);
  font-family: var(--font-mono, monospace);
}

/* Transition for attached card */
.slide-fade-enter-active { transition: all 0.3s ease; }
.slide-fade-leave-active { transition: all 0.2s ease; }
.slide-fade-enter-from { opacity: 0; transform: translateY(8px); }
.slide-fade-leave-to { opacity: 0; transform: translateY(-4px); }

/* ── Attach Button (+) ──────────────────────────── */
.attach-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border-subtle);
  background: var(--bg-inset);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.attach-btn:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(59, 130, 246, 0.15));
  border-color: rgba(139, 92, 246, 0.4);
  color: #a78bfa;
  transform: scale(1.08);
}

/* ── Issue Picker Dropdown ──────────────────────── */
.issue-picker {
  position: absolute;
  bottom: 70px;
  left: 1rem;
  right: 1rem;
  background: var(--bg-surface, #1e1e2e);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg, 12px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
  z-index: 100;
  display: flex;
  flex-direction: column;
  max-height: 340px;
  overflow: hidden;
}
.picker-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-tertiary);
  flex-shrink: 0;
}
.picker-search {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 0.85rem;
  font-family: inherit;
}
.picker-search::placeholder { color: var(--text-tertiary); }
.picker-list {
  overflow-y: auto;
  padding: 0.4rem;
}
.picker-empty {
  padding: 1.5rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.82rem;
}
.picker-group-label {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  padding: 0.5rem 0.75rem 0.25rem;
  font-family: var(--font-mono, monospace);
}
.picker-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 0.75rem;
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid transparent;
}
.picker-item:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.08), rgba(59, 130, 246, 0.08));
  border-color: rgba(139, 92, 246, 0.2);
}
.picker-sev {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.picker-sev.sev-critical { background: #ef4444; }
.picker-sev.sev-high { background: #f97316; }
.picker-sev.sev-medium { background: #eab308; }
.picker-sev.sev-low { background: #3b82f6; }
.picker-issue-text {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.picker-source {
  font-size: 0.62rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-tertiary);
  flex-shrink: 0;
  padding: 0.1rem 0.4rem;
  background: var(--bg-inset);
  border-radius: 4px;
}
</style>
