"""Quick smoke test for script_parser.py"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from script_parser import parse_source

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

result = parse_source(vue_content, "test.vue")

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
    if api.get("type") == "pattern":
        print(f"  [PATTERN] {api.get('flag')}")
        continue
    loop_marker = " [IN LOOP]" if api.get("in_loop") else ""
    print(f"  {api.get('method')} {api.get('url')} (scope={api.get('scope')}){loop_marker}")

# Verify basic API call presence
assert any(a.get("method") == "GET" and "/api/init" in a.get("url", "") for a in apis), "Should detect axios.get"
assert any(a.get("method") == "POST" and "/api/users" in a.get("url", "") for a in apis), "Should detect axios.post"
print("  OK - API calls detected")

# --- Test 2: Plain JS file ---
js_content = """
import { createRouter, createWebHistory } from 'vue-router';
import Home from './Home.vue';
import About from './About.vue';

const routes = [
  { path: '/', component: Home },
  { path: '/about', component: About }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
"""

js_result = parse_source(js_content, "router.js")
print("\n[JS Parser] Testing plain JS imports...")
js_imports = js_result["imported_components"]
assert "Home" in js_imports
assert "About" in js_imports
print("  OK - JS imports parsed")

# --- Test 3: Plain TS file ---
ts_content = """
import axios from 'axios';
import { defineStore } from 'pinia';
import type { User } from '@/types';

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null as User | null
  }),
  actions: {
    async fetchUser() {
      const { data } = await axios.get('/api/user');
      this.user = data;
    }
  }
});
"""

ts_result = parse_source(ts_content, "store.ts")
print("\n[TS Parser] Testing plain TS API calls & imports...")
ts_apis = ts_result["api_calls"]
assert any(a.get("method") == "GET" and a.get("url") == "/api/user" for a in ts_apis)
assert "defineStore" in ts_result["imported_components"]
print("  OK - TS imports and API calls parsed")

# --- Test 4: Error Handling ---
invalid_content = "import { ;syntax error"
err_result = parse_source(invalid_content, "bad.js")
print("\n[Error Handling] Testing syntax error resilience...")
# It should return an empty dict, or a partial parsed dict, but NOT crash
assert err_result is not None, "Error result should not be None (or it should be gracefully handled)"
print("  OK - Handled syntax error gracefully")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
