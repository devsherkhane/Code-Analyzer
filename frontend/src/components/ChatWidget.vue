<template>
  <div class="chat-widget">
    <button class="chat-toggle btn btn-primary" @click="isOpen = !isOpen">
      <svg v-if="!isOpen" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
      <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
    </button>
    
    <div v-if="isOpen" class="chat-window">
      <div class="chat-header">
        <h4>AI Workspace Assistant</h4>
        
        <div class="context-toggle">
          <label class="switch-label">Context:</label>
          <select v-model="contextType" class="modern-select">
            <option value="workspace">Entire Workspace</option>
            <option value="file" :disabled="!activeFile">Current File ({{ activeFile ? activeFile.file_name : 'None Selected' }})</option>
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
    workspacePath: { type: String, default: '' }
  },
  data() {
    return {
      isOpen: false,
      contextType: 'workspace',
      inputText: '',
      messages: [
        { role: 'assistant', content: 'Hello! I am your AI architect. Ask me anything about your project or currently opened file.' }
      ],
      loading: false
    };
  },
  watch: {
    activeFile: {
      handler(val) {
        if (!val && this.contextType === 'file') {
          this.contextType = 'workspace';
        }
      },
      deep: true
    }
  },
  methods: {
    renderMarkdown(text) {
      return marked.parse(text);
    },
    async sendMessage() {
      if (!this.inputText.trim()) return;
      
      const userMsg = this.inputText.trim();
      this.messages.push({ role: 'user', content: userMsg });
      this.inputText = '';
      this.loading = true;
      
      this.scrollToBottom();
      
      try {
        const payload = {
          message: userMsg,
          contextType: this.contextType,
          workspacePath: this.workspacePath,
          activeFileName: this.activeFile ? this.activeFile.file_name : '',
          activeContent: ''
        };
        
        if (this.contextType === 'file' && this.activeFile) {
           const res = await axios.get(`http://127.0.0.1:8081/file-content?path=${encodeURIComponent(this.activeFile.file_path)}`);
           payload.activeContent = res.data;
        }

        const response = await axios.post('http://127.0.0.1:7891/chat', payload);
        this.messages.push({ role: 'assistant', content: response.data.response });
      } catch (e) {
        this.messages.push({ role: 'assistant', content: `**Error**: ${e.response?.data?.error || e.message}` });
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
    }
  }
};
</script>

<style scoped>
.chat-widget {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-family: var(--font-primary);
}

.chat-toggle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  background: var(--accent-primary);
  color: white;
  border: none;
  cursor: pointer;
}
.chat-toggle:hover {
  transform: scale(1.05);
  filter: brightness(1.1);
}

.chat-window {
  width: 400px;
  height: 550px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: 0 12px 40px rgba(0,0,0,0.5);
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.3s forwards cubic-bezier(0.16, 1, 0.3, 1);
  transform-origin: bottom right;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
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
  color: #fff;
  border-bottom-right-radius: 4px;
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
    background: var(--bg-surface);
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
    font-family: var(--font-mono);
    font-size: 0.9em;
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
