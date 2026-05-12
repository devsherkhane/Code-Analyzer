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
      
      <div class="chat-input-area">
        <input 
          v-model="inputText" 
          @keyup.enter="sendMessage"
          placeholder="Ask about your code..."
          type="text"
        />
        <button class="send-btn" @click="sendMessage" :disabled="loading || !inputText.trim()">
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
  props: {
    activeFile: { type: Object, default: null },
    workspacePath: { type: String, default: '' },
    allFiles: { type: Array, default: () => [] }
  },
  data() {
    return {
      contextType: 'workspace',
      inputText: '',
      messages: [
        { role: 'assistant', content: 'Hello! I am your AI architect. Ask me anything about your project or currently opened file.' }
      ],
      loading: false
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
      if (!this.inputText.trim()) return;
      
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
      this.saveHistory();
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
</style>
