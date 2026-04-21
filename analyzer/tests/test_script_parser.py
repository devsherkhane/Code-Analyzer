"""Quick smoke test for script_parser.py"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from script_parser import parse_vue_script

# --- Test 1: Full Vue component ---
vue_content = """
<template>
  <div>
    <h1>{{ title }}</h1>
    <button @click="save">Save</button>
  </div>
</template>

<script>
import axios from 'axios';
import Header from './Header.vue';
import Sidebar from './Sidebar.vue';

export default {
    name: 'TestComponent',
    components: {
        Header,
        Sidebar
    },
    data() {
        return { items: [], title: 'Test' };
    },
    methods: {
        save() {
            axios.post('/api/users', { name: 'test' });
        },
        remove() {
            for (let i = 0; i < this.items.length; i++) {
                axios.delete('/api/items/' + i);
            }
        },
        loadList() {
            this.items.forEach(item => {
                fetch('/api/check/' + item.id);
            });
        },
        loadAll() {
            fetch('/api/list').then(res => res.json());
        }
    },
    computed: {
        total() { return this.items.length; },
        filtered() { return this.items.filter(x => x.active); }
    },
    watch: {
        searchTerm(newVal) { console.log(newVal); }
    },
    mounted() {
        axios.get('/api/init');
        new MQL().setActivity('GetDashboard').setData({ userId: 123 }).fetch();
    }
}
</script>
"""

result = parse_vue_script(vue_content)

print("=" * 50)
print("SCRIPT PARSER TEST RESULTS")
print("=" * 50)

# Test methods
methods = result["methods"]
print(f"\n[Methods] Found {len(methods)}: {methods}")
assert len(methods) == 4, f"Expected 4 methods, got {len(methods)}"
assert "save" in methods
assert "remove" in methods
assert "loadList" in methods
assert "loadAll" in methods
print("  OK")

# Test computed
computed = result["computed"]
print(f"\n[Computed] Found {len(computed)}: {computed}")
assert len(computed) == 2, f"Expected 2 computed, got {len(computed)}"
print("  OK")

# Test watchers
watchers = result["watchers"]
print(f"\n[Watchers] Found {len(watchers)}: {watchers}")
assert len(watchers) == 1, f"Expected 1 watcher, got {len(watchers)}"
print("  OK")

# Test imports
imports = result["imported_components"]
print(f"\n[Imports] Found {len(imports)}: {imports}")
assert "Header" in imports
assert "Sidebar" in imports
print("  OK")

# Test registered components
regs = result["registered_components"]
print(f"\n[Registered] Found {len(regs)}: {regs}")
assert "Header" in regs
assert "Sidebar" in regs
print("  OK")

# Test API calls
apis = result["api_calls"]
print(f"\n[API Calls] Found {len(apis)}:")
for api in apis:
    loop_marker = " [IN LOOP]" if api["in_loop"] else ""
    print(f"  {api['method']} {api['url']} (scope={api['scope']}){loop_marker}")

# Verify scope-awareness
assert any(a["scope"] == "mounted" and a["method"] == "GET" for a in apis), "Should detect axios.get in mounted"
assert any(a["scope"] == "mounted" and a["method"] == "MQL" for a in apis), "Should detect MQL in mounted"
assert any(a["in_loop"] and a["scope"] == "methods.remove" for a in apis), "Should detect API in for-loop"
assert any(a["in_loop"] and a["scope"] == "methods.loadList" for a in apis), "Should detect API in forEach"
assert any(a["scope"] == "methods.save" and not a["in_loop"] for a in apis), "save() API should NOT be in loop"
print("  OK - All scope/loop checks passed!")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
