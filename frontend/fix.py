import sys

with open('c:\\Users\\Lenovo\\Desktop\\Projects\\code-analyzer\\frontend\\src\\components\\ChatWidget.vue', 'r', encoding='utf-8') as f:
    content = f.read()

bad_str = """      this.attachedIssue = { ...issue };
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
        'Please explain this attached issue, why it matters, and how I should fix it.',
        `Issue type: ${issue.defect_type || issue.problem || 'Unknown'}`,
      ];
  background: var(--bg-surface);"""

good_str = """      this.attachedIssue = { ...issue };
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
        'Please explain this attached issue, why it matters, and how I should fix it.',
        `Issue type: ${issue.defect_type || issue.problem || 'Unknown'}`,
      ];
      if (issue._fileName) parts.push(`File: ${issue._fileName}`);
      if (issue.line_number || issue.line) parts.push(`Line: ${issue.line_number || issue.line}`);
      if (issue.wcag_rule) parts.push(`Rule: ${issue.wcag_rule}`);
      if (issue.suggestion || issue.explanation) parts.push(`Suggested Fix: ${issue.suggestion || issue.explanation}`);
      if (issue.fixed_code_snippet || issue.fixed_code) parts.push(`Fix Code:\\n${issue.fixed_code_snippet || issue.fixed_code}`);
      return parts.join(' | ');
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
  background: var(--bg-surface);"""

content = content.replace(bad_str, good_str)
with open('c:\\Users\\Lenovo\\Desktop\\Projects\\code-analyzer\\frontend\\src\\components\\ChatWidget.vue', 'w', encoding='utf-8') as f:
    f.write(content)
print("done")
