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
        <div v-for="(msg, i) in messages" :key="i" :class="['msg-item', msg.role]">
          <div v-if="msg.role === 'assistant'" class="msg-avatar assistant">
            <div class="avatar-inner">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12a10 10 0 0 1 10-10z"/>
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 2v2M12 20v2M2 12h2M20 12h2"/>
              </svg>
            </div>
          </div>
          <div v-if="msg.role === 'user'" class="msg-avatar user">
            <div class="avatar-inner">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
          </div>
          <div class="msg-content-wrapper">
            <div class="msg-meta-header">
              <span class="role-name">{{ msg.role === 'assistant' ? 'PrismAI Architect' : 'You' }}</span>
              <span class="role-badge" v-if="msg.role === 'assistant'">AI Co-Pilot</span>
            </div>
            <div class="msg-bubble markdown-body" v-html="renderMarkdown(msg.content)"></div>
          </div>
        </div>
        <div v-if="loading" class="msg-item assistant loading">
          <div class="msg-avatar assistant">
            <div class="avatar-inner">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12a10 10 0 0 1 10-10z"/>
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 2v2M12 20v2M2 12h2M20 12h2"/>
              </svg>
            </div>
          </div>
          <div class="msg-content-wrapper">
            <div class="msg-meta-header">
              <span class="role-name">PrismAI Architect</span>
              <span class="role-badge pulse">Thinking...</span>
            </div>
            <div class="msg-bubble">
              <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>
          </div>
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
        <button class="attach-btn" :class="{ active: issuePickerOpen }" @click="toggleIssuePicker" title="Attach an issue">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" class="plus-icon"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        </button>
        <input 
          v-model="inputText" 
          @keyup.enter="sendMessage"
          :placeholder="attachedIssue ? 'Ask about this issue or press Enter to discuss...' : 'Ask about your code...'"
          type="text"
          ref="chatInput"
        />
        <button class="send-btn" @click="sendMessage" :disabled="loading || (!inputText.trim() && !attachedIssue)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
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
        this.inputText = 'Please analyze this issue. Explain the root cause, suggest the best approach to resolve it, and evaluate whether the provided fix code is reliable.';
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
        const attachedIssue = this.attachedIssue ? { ...this.attachedIssue } : null;

        if (this.contextType !== 'workspace') {
           const selected = this.allFiles.find(f => f.file_path === this.contextType);
           if (selected) {
             activeFileName = selected.file_name;
             const res = await axios.get(`http://127.0.0.1:8081/file-content?path=${encodeURIComponent(selected.file_path)}`);
             if (attachedIssue && attachedIssue.original_code) {
               activeContent = attachedIssue.original_code;
             } else {
               activeContent = res.data;
             }
           }
        }

        const payload = {
          message: userMsg,
          contextType: this.contextType === 'workspace' ? 'workspace' : 'file',
          workspacePath: this.workspacePath,
          activeFileName: activeFileName,
          activeContent: activeContent,
          history: historyPayload,
          issueContext: attachedIssue
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
      const parts = [
        'Please analyze this issue. Explain the root cause, suggest the best approach to resolve it, and evaluate whether the provided fix code is reliable.',
        `**Issue type**: ${issue.defect_type || issue.problem || 'Unknown'}`,
      ];
      if (issue._fileName) parts.push(`**File**: ${issue._fileName}`);
      if (issue.line_number || issue.line) parts.push(`**Line**: ${issue.line_number || issue.line}`);
      if (issue.wcag_rule) parts.push(`**Rule**: ${issue.wcag_rule}`);
      if (issue.suggestion || issue.explanation) parts.push(`**Suggested Fix**:\n${issue.suggestion || issue.explanation}`);
      if (issue.fixed_code_snippet || issue.fixed_code) parts.push(`**Fix Code**:\n\`\`\`vue\n${issue.fixed_code_snippet || issue.fixed_code}\n\`\`\``);
      return parts.join('\n\n');
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
  font-family: var(--font-sans, sans-serif);
  box-sizing: border-box;
}

.chat-window {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  height: 100%;
  box-shadow: var(--shadow-xl), var(--shadow-glow);
  animation: slideUp 0.3s forwards cubic-bezier(0.16, 1, 0.3, 1);
  backdrop-filter: blur(24px);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-header {
  padding: 1.25rem 1.25rem;
  background: linear-gradient(to right, rgba(99, 102, 241, 0.05), rgba(236, 72, 153, 0.03));
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.chat-header h4 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--text-primary);
  font-weight: 700;
  letter-spacing: -0.015em;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chat-header h4::before {
  content: '';
  display: inline-block;
  width: 8px;
  height: 8px;
  background: var(--accent-primary);
  border-radius: 50%;
  box-shadow: 0 0 10px var(--accent-primary);
  animation: pulse-glow 2s infinite ease-in-out;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.context-toggle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.btn-ghost {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.65rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s var(--ease-out);
}

.btn-ghost:hover {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.25);
  color: var(--accent-danger, #ef4444);
}

.modern-select {
  background: var(--bg-inset);
  color: var(--text-primary);
  border: 1px solid var(--border-subtle);
  padding: 0.35rem 0.65rem;
  border-radius: var(--radius-md);
  font-size: 0.78rem;
  font-weight: 500;
  outline: none;
  flex: 1;
  transition: all 0.2s var(--ease-out);
  cursor: pointer;
}

.modern-select:hover {
  border-color: var(--border-default);
  background: var(--bg-surface-hover);
}

.modern-select:focus {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 2px var(--accent-primary-subtle);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  background: radial-gradient(circle at top right, rgba(99, 102, 241, 0.02), transparent 400px);
}

/* Custom Scrollbar for Chat Messages */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}
.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}
.chat-messages::-webkit-scrollbar-thumb {
  background: var(--border-default);
  border-radius: var(--radius-full);
}
.chat-messages::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

/* Message Item Layout */
.msg-item {
  display: flex;
  gap: 0.75rem;
  width: 100%;
  animation: messageFadeIn 0.25s var(--ease-out) forwards;
}

@keyframes messageFadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.msg-item.user {
  flex-direction: row-reverse;
}

/* Avatars styling */
.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.msg-avatar.assistant .avatar-inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.msg-avatar.user .avatar-inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03));
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Message Contents */
.msg-content-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 82%;
  gap: 0.25rem;
}

.msg-item.user .msg-content-wrapper {
  align-items: flex-end;
}

.msg-meta-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0 0.25rem;
}

.role-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.msg-item.user .role-name {
  color: var(--accent-primary-hover);
}

.role-badge {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  background: var(--accent-primary-subtle);
  border: 1px solid var(--accent-primary-glow);
  color: var(--accent-primary);
  padding: 0.08rem 0.35rem;
  border-radius: 4px;
}

.role-badge.pulse {
  animation: pulse-badge 1.5s infinite ease-in-out;
}

@keyframes pulse-badge {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

.msg-bubble {
  padding: 0.85rem 1.1rem;
  border-radius: var(--radius-lg);
  font-size: 0.88rem;
  line-height: 1.55;
  word-wrap: break-word;
  box-shadow: var(--shadow-sm);
}

.msg-item.user .msg-bubble {
  background: linear-gradient(135deg, var(--accent-primary), #4f46e5);
  color: #ffffff !important;
  border-top-right-radius: 2px;
  box-shadow: 0 4px 15px rgba(79, 70, 229, 0.2);
}

.msg-item.user .msg-bubble :deep(*) {
  color: #ffffff !important;
}

.msg-item.assistant .msg-bubble {
  background: var(--bg-glass-card);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  border-top-left-radius: 2px;
  backdrop-filter: blur(8px);
}

.msg-item.assistant.loading .msg-bubble {
  padding: 0.65rem 1rem;
}

/* Ensure markdown renders beautifully */
.markdown-body :deep(pre) {
    background: #09090e !important;
    border: 1px solid var(--border-subtle) !important;
    padding: 0.85rem !important;
    border-radius: var(--radius-md) !important;
    overflow-x: auto;
    font-size: 0.82em;
    margin: 0.75rem 0;
    box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);
    font-family: var(--font-mono);
}
.markdown-body :deep(code) {
    background: rgba(255, 255, 255, 0.06) !important;
    color: #e2e8f0 !important;
    padding: 0.15rem 0.35rem;
    border-radius: var(--radius-xs);
    font-family: var(--font-mono);
    font-size: 0.85em;
    border: 1px solid rgba(255, 255, 255, 0.04);
}
.markdown-body :deep(pre code) {
    background: transparent !important;
    border: none !important;
    color: inherit !important;
    padding: 0 !important;
}
.markdown-body :deep(p) { margin: 0 0 0.6rem 0; }
.markdown-body :deep(p:last-child) { margin: 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) {
  margin: 0 0 0.6rem 0;
  padding-left: 1.25rem;
}
.markdown-body :deep(li) {
  margin-bottom: 0.25rem;
}
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) {
  font-size: 1rem;
  font-weight: 600;
  margin: 0.85rem 0 0.4rem 0;
  color: var(--text-primary);
}

.chat-input-area {
  padding: 1.1rem;
  background: var(--bg-chat-input);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  gap: 0.75rem;
  align-items: center;
  backdrop-filter: blur(12px);
}

.chat-input-area input {
  flex: 1;
  background: var(--bg-inset);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  padding: 0.7rem 1.1rem;
  border-radius: var(--radius-xl);
  outline: none;
  font-size: 0.9rem;
  font-family: var(--font-sans);
  transition: all 0.25s var(--ease-out);
}

.chat-input-area input:focus {
  border-color: var(--accent-primary);
  background: var(--bg-surface);
  box-shadow: 0 0 0 3px var(--accent-primary-subtle);
}

.send-btn {
  background: linear-gradient(135deg, var(--accent-primary), #4f46e5);
  color: #fff;
  border: none;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s var(--ease-spring);
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.25);
}
.send-btn svg {
  width: 18px !important;
  height: 18px !important;
  min-width: 18px !important;
  min-height: 18px !important;
  display: block;
}

.send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  transform: scale(0.92);
  box-shadow: none;
}

.send-btn:not(:disabled):hover {
  filter: brightness(1.1);
  transform: scale(1.08) translateY(-1px);
  box-shadow: 0 6px 14px rgba(99, 102, 241, 0.4);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0.35rem 0.2rem;
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
  0%, 80%, 100% { transform: scale(0.2); }
  40% { transform: scale(1); }
}

/* ── Attached Issue Card ─────────────────────────── */
.attached-issue-card {
  margin: 0.5rem 1.1rem;
  padding: 0.75rem 1rem;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(236, 72, 153, 0.06));
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  animation: slideUp 0.25s forwards var(--ease-out);
}
.aic-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.7rem;
  font-weight: 750;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #a5b4fc;
  margin-bottom: 0.35rem;
}
.aic-dismiss {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 1.15rem;
  line-height: 1;
  padding: 0 0.2rem;
  transition: color 0.2s;
}
.aic-dismiss:hover { color: var(--accent-danger); }
.aic-body {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.aic-type {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-primary);
}
.aic-file {
  font-size: 0.72rem;
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  background: var(--bg-inset);
  padding: 0.08rem 0.35rem;
  border-radius: 4px;
  border: 1px solid var(--border-subtle);
}

/* Transition for attached card */
.slide-fade-enter-active { transition: all 0.3s var(--ease-out); }
.slide-fade-leave-active { transition: all 0.2s var(--ease-out); }
.slide-fade-enter-from { opacity: 0; transform: translateY(8px); }
.slide-fade-leave-to { opacity: 0; transform: translateY(-4px); }

/* ── Attach Button (+) ──────────────────────────── */
.attach-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1px solid var(--border-subtle);
  background: var(--bg-inset);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s var(--ease-spring);
  flex-shrink: 0;
  box-shadow: var(--shadow-xs);
}
.attach-btn.active {
  transform: rotate(45deg);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
  background: var(--bg-surface);
  box-shadow: 0 0 10px var(--accent-primary-glow);
}
.attach-btn:not(.active):hover {
  background: var(--accent-primary-subtle);
  border-color: var(--accent-primary);
  color: var(--accent-primary);
  transform: scale(1.08);
}
.attach-btn svg {
  width: 20px !important;
  height: 20px !important;
  min-width: 20px !important;
  min-height: 20px !important;
  stroke-width: 3.5px !important;
  display: block;
}
.plus-icon {
  transition: transform 0.25s var(--ease-spring);
}

/* ── Issue Picker Dropdown ──────────────────────── */
.issue-picker {
  position: absolute;
  bottom: 74px;
  left: 1.1rem;
  right: 1.1rem;
  background: var(--bg-issue-picker);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-issue-picker);
  z-index: 100;
  display: flex;
  flex-direction: column;
  max-height: 340px;
  overflow: hidden;
  backdrop-filter: blur(16px);
}
.picker-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.85rem 1.1rem;
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
  font-size: 0.88rem;
  font-family: inherit;
}
.picker-search::placeholder { color: var(--text-tertiary); }
.picker-list {
  overflow-y: auto;
  padding: 0.5rem;
}
/* Custom Scrollbar for Issue Picker */
.picker-list::-webkit-scrollbar {
  width: 5px;
}
.picker-list::-webkit-scrollbar-track {
  background: transparent;
}
.picker-list::-webkit-scrollbar-thumb {
  background: var(--border-subtle);
  border-radius: var(--radius-full);
}
.picker-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}

.picker-empty {
  padding: 2rem 1.5rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.85rem;
}
.picker-group-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
  padding: 0.65rem 0.75rem 0.3rem;
  font-family: var(--font-mono);
  border-bottom: 1px solid rgba(255, 255, 255, 0.02);
}
.picker-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.6rem 0.75rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s var(--ease-out);
  border: 1px solid transparent;
  margin-top: 2px;
}
.picker-item:hover {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(236, 72, 153, 0.06));
  border-color: rgba(99, 102, 241, 0.2);
  transform: translateX(2px);
}
.picker-sev {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 6px currentColor;
}
.picker-sev.sev-critical { background: var(--severity-critical); color: var(--severity-critical); }
.picker-sev.sev-high { background: var(--severity-high); color: var(--severity-high); }
.picker-sev.sev-medium { background: var(--severity-medium); color: var(--severity-medium); }
.picker-sev.sev-low { background: var(--severity-low); color: var(--severity-low); }

.picker-issue-text {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.picker-source {
  font-size: 0.62rem;
  font-weight: 750;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  flex-shrink: 0;
  padding: 0.12rem 0.45rem;
  background: var(--bg-inset);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
}
</style>
