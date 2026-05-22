<template>
  <div class="file-tree">
    <div v-for="item in treeData" :key="item.path" class="tree-item">
      <div 
        class="item-row" 
        :class="{ 'active': selectedPath === item.absPath, 'is-folder': item.isDir }"
        :style="{ paddingLeft: depth * 12 + 'px' }"
        @click="handleClick(item)"
      >
        <span class="chevron" v-if="item.isDir">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" :class="{ 'rotate-90': expanded[item.path] }">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </span>
        <span v-else class="file-bullet"></span>
        
        <svg v-if="item.isDir" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-folder"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
        <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon-file" :class="'icon-file-' + getFileType(item.name)"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path><polyline points="13 2 13 9 20 9"></polyline></svg>
        
        <span class="item-name">{{ item.name }}</span>
        <span v-if="item.issueCount > 0" class="issue-badge">{{ item.issueCount }}</span>
      </div>
      
      <transition name="expand">
        <div v-if="item.isDir && expanded[item.path]" class="tree-children">
          <FileTree 
            :treeData="item.children" 
            :depth="depth + 1" 
            :selectedPath="selectedPath"
            @select="$emit('select', $event)"
          />
        </div>
      </transition>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FileTree',
  props: {
    treeData: { type: Array, required: true },
    depth: { type: Number, default: 0 },
    selectedPath: { type: String, default: '' }
  },
  emits: ['select'],
  data() {
    return {
      expanded: {}
    };
  },
  watch: {
    treeData: {
      immediate: true,
      handler(newTree) {
        if (!newTree) return;
        const expandAll = (nodes) => {
          nodes.forEach(node => {
            if (node.isDir) {
              this.expanded[node.path] = true;
              if (node.children) expandAll(node.children);
            }
          });
        };
        expandAll(newTree);
      }
    }
  },
  methods: {
    handleClick(item) {
      if (item.isDir) {
        this.expanded[item.path] = !this.expanded[item.path];
      } else {
        this.$emit('select', item.absPath);
      }
    },
    getFileType(name) {
      if (!name) return 'default';
      const ext = name.split('.').pop().toLowerCase();
      if (ext === 'vue') return 'vue';
      if (['js', 'ts', 'jsx', 'tsx'].includes(ext)) return 'js';
      if (ext === 'json') return 'json';
      if (['css', 'scss', 'sass', 'html'].includes(ext)) return 'style';
      return 'default';
    }
  }
};
</script>

<style scoped>
.file-tree { display: flex; flex-direction: column; }
.tree-item { display: flex; flex-direction: column; }
.item-row { display: flex; align-items: center; gap: 0.6rem; padding: 0.45rem 0.75rem; cursor: pointer; border-radius: var(--radius-sm, 6px); transition: all var(--duration-fast) var(--ease-out); user-select: none; border: 1px solid transparent; }
.item-row:hover { background: var(--bg-surface-hover); border-color: var(--border-subtle); transform: translateX(2px); }
.item-row.active { background: var(--accent-primary-subtle); color: var(--accent-primary); border-color: var(--accent-primary-glow); box-shadow: 0 0 12px var(--accent-primary-glow); font-weight: 600; }
.chevron { display: flex; width: 12px; transition: transform 0.2s; color: var(--text-tertiary); }
.rotate-90 { transform: rotate(90deg); }
.file-bullet { width: 12px; height: 12px; position: relative; }
.file-bullet::after { content: ''; position: absolute; left: 50%; top: 50%; width: 4px; height: 4px; background: var(--text-tertiary); border-radius: 50%; transform: translate(-50%, -50%); opacity: 0.4; }

.icon-folder { color: #eab308; opacity: 0.9; filter: drop-shadow(0 0 2px rgba(234, 179, 8, 0.3)); }
.icon-file { transition: transform 0.2s; }
.item-row:hover .icon-file { transform: scale(1.08); }

.icon-file-vue { color: #41b883; }
.icon-file-js { color: #f7df1e; }
.icon-file-json { color: #38bdf8; }
.icon-file-style { color: #c084fc; }
.icon-file-default { color: var(--text-tertiary); opacity: 0.7; }

.item-name { font-size: 0.82rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
.issue-badge { font-size: 0.65rem; font-weight: 700; background: var(--accent-danger-subtle); color: var(--accent-danger); padding: 0.15rem 0.4rem; border-radius: var(--radius-sm, 4px); min-width: 18px; text-align: center; border: 1px solid rgba(239, 68, 68, 0.15); box-shadow: 0 0 6px rgba(239, 68, 68, 0.1); }

.expand-enter-active, .expand-leave-active { transition: all 0.25s var(--ease-out); max-height: 500px; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; transform: translateY(-5px); }
</style>
