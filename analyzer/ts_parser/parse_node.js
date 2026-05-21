const fs = require('fs');
const compilerSfc = require('@vue/compiler-sfc');
const { parse } = require('@typescript-eslint/typescript-estree');
const postcss = require('postcss');

const isWorker = process.argv.includes('--worker');
const filePathArg = process.argv.slice(2).find(arg => arg !== '--worker');

if (!isWorker && !filePathArg) {
    console.error("Usage: node parse_node.js <file> [--worker]");
    process.exit(1);
}

const TAILWIND_COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'pink', 'gray', 'slate', 'zinc', 'neutral', 'stone', 'orange', 'amber', 'lime', 'emerald', 'teal', 'cyan', 'sky', 'indigo', 'violet', 'fuchsia', 'rose'];

function parseFile(filePath) {
try {
    const content = fs.readFileSync(filePath, 'utf-8');
    let scriptContent = content;
    let isVue = filePath.toLowerCase().endsWith('.vue');
    let descriptor = null;

    if (isVue) {
        try {
            const parsed = compilerSfc.parse(content);
            descriptor = parsed.descriptor;
            if (descriptor.scriptSetup) {
                scriptContent = descriptor.scriptSetup.content;
            } else if (descriptor.script) {
                scriptContent = descriptor.script.content;
            } else {
                scriptContent = "";
            }
        } catch (e) {
            scriptContent = ""; 
        }
    }

    // Prepare unified results
    const result = {
        methods: [],
        computed: [],
        watchers: [],
        api_calls: [],
        imported_components: [],
        registered_components: [],
        imports: [],
        exports: [],
        ui_elements: [], 
        props_definition: null,
        emits_definition: null,
        routes: {},
        style_metrics: {
            colors: [],
            fonts: [],
            font_sizes: [],
            spacing: []
        },
        template_metrics: {
            visible_text: "",
            lines: 0,
            max_depth: 0,
            missing_alt_count: 0,
            unlabeled_inputs: 0,
            interactive_without_role: 0
        },
        script_metrics: {
            cyclomatic_complexity: 1, 
            cognitive_complexity: 0
        }
    };

    const reactiveVars = new Set();

    // --- STYLE AST PARSING ---
    if (isVue && descriptor && descriptor.styles) {
        descriptor.styles.forEach(style => {
            try {
                const root = postcss.parse(style.content);
                root.walkDecls(decl => {
                    const prop = decl.prop.toLowerCase();
                    const val = decl.value.trim();
                    
                    if (prop.includes('color')) {
                        result.style_metrics.colors.push(val);
                    } else if (prop === 'font-family') {
                        result.style_metrics.fonts.push(val.replace(/['"]/g, ''));
                    } else if (prop === 'font-size') {
                        result.style_metrics.font_sizes.push(val);
                    } else if (prop.startsWith('padding') || prop.startsWith('margin')) {
                        result.style_metrics.spacing.push({ prop, val });
                    }
                });
            } catch (e) {
                // Ignore CSS parse errors for individual blocks
            }
        });
    } else if (filePath.toLowerCase().endsWith('.css')) {
        try {
            const root = postcss.parse(content);
            root.walkDecls(decl => {
                const prop = decl.prop.toLowerCase();
                const val = decl.value.trim();
                if (prop.includes('color')) result.style_metrics.colors.push(val);
                else if (prop === 'font-family') result.style_metrics.fonts.push(val.replace(/['"]/g, ''));
                else if (prop === 'font-size') result.style_metrics.font_sizes.push(val);
                else if (prop.startsWith('padding') || prop.startsWith('margin')) result.style_metrics.spacing.push({ prop, val });
            });
        } catch (e) {}
    }

    // --- TEMPLATE AST PARSING ---
    if (isVue && descriptor && descriptor.template && descriptor.template.ast) {
        const { loc, ast } = descriptor.template;
        result.template_metrics.lines = loc.end.line - loc.start.line;
        
        let visibleTextParts = [];

        function walkTemplateAst(node, depth) {
            if (!node) return;
            
            if (depth > result.template_metrics.max_depth) {
                result.template_metrics.max_depth = depth;
            }

            if (node.type === 2) { // 2 = Text
                if (node.content && node.content.trim()) {
                    visibleTextParts.push(node.content.trim());
                }
            }

            if (node.type === 1) { // 1 = Element
                let attrs = {};
                let hasVForKey = false;
                let isVFor = false;

                if (node.props) {
                    node.props.forEach(prop => {
                        if (prop.type === 6) { // 6 = Attribute
                            const val = prop.value ? prop.value.content : "";
                            attrs[prop.name] = val;
                            
                            // Tailwind/Style Detection (Regex-free)
                            if (prop.name === 'class') {
                                const classes = val.split(' ');
                                classes.forEach(cls => {
                                    if (cls.startsWith('text-') || cls.startsWith('bg-')) {
                                        const colorPart = cls.split('-')[1];
                                        if (TAILWIND_COLORS.includes(colorPart)) {
                                            result.style_metrics.colors.push(cls);
                                        }
                                    }
                                    if (cls.startsWith('p-') || cls.startsWith('m-') || cls.includes(':p-') || cls.includes(':m-')) {
                                        result.style_metrics.spacing.push({ prop: 'tailwind', val: cls });
                                    }
                                });
                            }
                        } else if (prop.type === 7) { // 7 = Directive
                            let attrName = prop.name;
                            if (prop.arg && prop.arg.content) {
                                if (prop.name === 'bind') {
                                    attrName = ':' + prop.arg.content;
                                    if (prop.arg.content === 'key') hasVForKey = true;
                                }
                                else if (prop.name === 'on') attrName = '@' + prop.arg.content;
                                else attrName = 'v-' + prop.name + ':' + prop.arg.content;
                            } else {
                                attrName = 'v-' + prop.name;
                                if (prop.name === 'for') isVFor = true;
                            }
                            
                            let expVal = "";
                            if (prop.exp && prop.exp.content) {
                                expVal = prop.exp.content;
                            }
                            attrs[attrName] = expVal;
                        }
                    });
                }
                
                if (isVFor && !hasVForKey) {
                    result.api_calls.push({ type: 'pattern', flag: 'MISSING_VFOR_KEY', tag: node.tag });
                }

                let label = "";
                if (node.children) {
                    let childText = node.children.filter(c => c.type === 2).map(c => c.content).join(' ');
                    if (childText.trim()) label = childText.trim();
                }

                if (node.tag === 'img' && (!attrs.alt || attrs.alt.trim() === '')) {
                    result.template_metrics.missing_alt_count++;
                }
                if (node.tag === 'input' && !attrs.id) {
                    result.template_metrics.unlabeled_inputs++;
                }
                if (attrs['@click'] || attrs['v-on:click']) {
                    if (node.tag !== 'button' && node.tag !== 'a' && attrs.role !== 'button') {
                        result.template_metrics.interactive_without_role++;
                    }
                }

                result.ui_elements.push({
                    tag: node.tag,
                    attrs: attrs,
                    label: label,
                    line_start: node.loc ? node.loc.start.line : null,
                    line_end: node.loc ? node.loc.end.line : null
                });
            }

            if (node.children) {
                node.children.forEach(child => walkTemplateAst(child, depth + 1));
            }
        }
        
        walkTemplateAst(ast, 0);
        result.template_metrics.visible_text = visibleTextParts.join(' ');
    }

    if (!scriptContent.trim()) {
        return result;
    }

    let tsAst;
    try {
        tsAst = parse(scriptContent, {
            loc: true,
            range: true,
            jsx: true,
            sourceType: 'module'
        });
    } catch (e) {
        result.syntax_error = e.message;
        return result;
    }
    
    // Calculate Complexity
    function calculateComplexity(node, depth) {
        if (!node || typeof node !== 'object') return;
        const branchTypes = ['IfStatement', 'ForStatement', 'ForInStatement', 'ForOfStatement', 'WhileStatement', 'DoWhileStatement', 'CatchClause', 'ConditionalExpression'];
        let newDepth = depth;
        if (branchTypes.includes(node.type)) {
            result.script_metrics.cyclomatic_complexity += 1;
            result.script_metrics.cognitive_complexity += (depth + 1);
            newDepth++;
        } else if (node.type === 'LogicalExpression' && (node.operator === '&&' || node.operator === '||')) {
            result.script_metrics.cyclomatic_complexity += 1;
            result.script_metrics.cognitive_complexity += 1;
        } else if (node.type === 'SwitchCase' && node.test !== null) {
            result.script_metrics.cyclomatic_complexity += 1;
            result.script_metrics.cognitive_complexity += 1;
        }
        for (const key of Object.keys(node)) {
            if (key === 'loc' || key === 'range' || key === 'type') continue;
            const child = node[key];
            if (Array.isArray(child)) child.forEach(c => calculateComplexity(c, newDepth));
            else if (child && typeof child === 'object') calculateComplexity(child, newDepth);
        }
    }
    calculateComplexity(tsAst, 0);

    // Pre-walk for Reactive Vars
    function preWalk(node) {
        if (!node || typeof node !== 'object') return;
        if (node.type === 'VariableDeclarator' && node.id && node.id.type === 'Identifier') {
             if (node.init && node.init.type === 'CallExpression' && node.init.callee.type === 'Identifier') {
                const calleeName = node.init.callee.name;
                if (['ref', 'reactive', 'computed', 'shallowRef'].includes(calleeName)) {
                    reactiveVars.add(node.id.name);
                }
            }
        }
        for (const key of Object.keys(node)) {
            if (key === 'loc' || key === 'range' || key === 'type') continue;
            const child = node[key];
            if (Array.isArray(child)) child.forEach(c => preWalk(c));
            else if (child && typeof child === 'object') preWalk(child);
        }
    }
    preWalk(tsAst);

    function walkScript(node, parent, visitor) {
        if (!node || typeof node !== 'object') return;
        visitor(node, parent);
        for (const key of Object.keys(node)) {
            if (key === 'loc' || key === 'range' || key === 'type') continue;
            const child = node[key];
            if (Array.isArray(child)) child.forEach(c => walkScript(c, node, visitor));
            else if (child && typeof child === 'object') walkScript(child, node, visitor);
        }
    }

    walkScript(tsAst, null, (node, parent) => {
        // --- ROUTE DETECTION ---
        if (node.type === 'ObjectExpression') {
            const props = {};
            node.properties.forEach(p => {
                const key = p.key ? (p.key.name || p.key.value) : null;
                if (key && p.value && p.value.type === 'Literal') {
                    props[key] = p.value.value;
                }
            });
            if (props.path && props.component) {
                const compName = String(props.component).split('/').pop().split('.')[0];
                result.routes[compName] = props.path;
            }
        }

        // Watcher Cascade
        if (node.type === 'CallExpression' && node.callee && (node.callee.name === 'watch' || node.callee.name === 'watchEffect')) {
            const lastArg = node.arguments[node.arguments.length - 1];
            if (lastArg && lastArg.range) {
                const bodyStr = scriptContent.slice(lastArg.range[0], lastArg.range[1]);
                for (let v of reactiveVars) {
                    if (bodyStr.includes(v + '.value =') || bodyStr.includes(v + ' =')) {
                        result.api_calls.push({ type: 'pattern', flag: 'WATCHER_CASCADE', var: v });
                    }
                }
            }
        }

        // Computed Side Effect
        if (node.type === 'CallExpression' && node.callee && node.callee.name === 'computed') {
            const arg = node.arguments[0];
            if (arg && arg.range) {
                const bodyStr = scriptContent.slice(arg.range[0], arg.range[1]);
                if (bodyStr.includes('=') && !bodyStr.includes('==') && !bodyStr.includes('=>')) {
                    result.api_calls.push({ type: 'pattern', flag: 'COMPUTED_SIDE_EFFECT' });
                }
            }
        }

        // Memory Leak
        if (node.type === 'CallExpression' && node.callee && (node.callee.name === 'setInterval' || node.callee.name === 'addEventListener')) {
            const hasCleanup = scriptContent.includes('clearInterval') || scriptContent.includes('removeEventListener') || scriptContent.includes('onUnmounted') || scriptContent.includes('beforeUnmount');
            if (!hasCleanup) {
                result.api_calls.push({ type: 'pattern', flag: 'MISSING_CLEANUP', action: node.callee.name });
            }
        }

        // API Calls & Async Lifecycle
        if (node.type === 'CallExpression' || node.type === 'NewExpression') {
            let calleeName = '';
            if (node.callee.type === 'Identifier') calleeName = node.callee.name;
            else if (node.callee.type === 'MemberExpression') {
                let objName = '';
                if (node.callee.object.type === 'Identifier') objName = node.callee.object.name;
                else if (node.callee.object.type === 'ThisExpression') objName = 'this';
                calleeName = objName + '.' + (node.callee.property ? (node.callee.property.name || node.callee.property.value) : '');
            }

            if (calleeName.startsWith('axios.') || calleeName.startsWith('api.') || calleeName === 'fetch' || calleeName.startsWith('$http.')) {
                let url = '[dynamic]';
                if (node.arguments && node.arguments.length > 0) {
                    if (node.arguments[0].type === 'Literal') url = node.arguments[0].value;
                    else if (node.arguments[0].type === 'TemplateLiteral') url = node.arguments[0].quasis.map(q => q.value.raw).join('{var}');
                }

                let hasLoading = false;
                let hasCatch = false;
                
                const nearby = scriptContent.slice(Math.max(0, node.range[0] - 500), Math.min(scriptContent.length, node.range[1] + 500));
                if (nearby.includes('loading')) hasLoading = true;
                if (nearby.includes('catch')) hasCatch = true;

                if (!hasLoading || !hasCatch) {
                    result.api_calls.push({ type: 'pattern', flag: 'INCOMPLETE_ASYNC_LIFECYCLE', url: url });
                }

                result.api_calls.push({
                    method: calleeName.includes('.') ? calleeName.split('.').pop().toUpperCase() : 'GET',
                    url: url,
                    payload: '...',
                    scope: 'unknown',
                    in_loop: false
                });
            }
        }

        // Imports
        if (node.type === 'ImportDeclaration') {
            const source = node.source.value;
            node.specifiers.forEach(spec => {
                let name = spec.local.name;
                result.imported_components.push(name);
                result.imports.push({ name, source, type: spec.type === 'ImportSpecifier' ? 'named' : 'default' });
            });
        }
        
        // --- PROPS & EMITS (SETUP) ---
        if (node.type === 'CallExpression' && node.callee && node.callee.name === 'defineProps') {
            const propsData = {};
            const arg = node.arguments[0];
            if (arg && arg.type === 'ObjectExpression') {
                arg.properties.forEach(p => {
                    const key = p.key ? (p.key.name || p.key.value) : null;
                    if (key) {
                        const propName = key;
                        let type = 'any';
                        let required = false;
                        if (p.value.type === 'Identifier') {
                            type = p.value.name;
                        } else if (p.value.type === 'ObjectExpression') {
                            p.value.properties.forEach(ip => {
                                const ikey = ip.key ? (ip.key.name || ip.key.value) : null;
                                if (ikey === 'type') type = ip.value.name || 'any';
                                if (ikey === 'required') required = ip.value.value === true;
                            });
                        }
                        propsData[propName] = { type, required };
                    }
                });
            } else if (arg && arg.type === 'ArrayExpression') {
                arg.elements.forEach(el => {
                    if (el.type === 'Literal') propsData[el.value] = { type: 'any', required: false };
                });
            }
            result.props_definition = propsData;
        }

        if (node.type === 'CallExpression' && node.callee && node.callee.name === 'defineEmits') {
            const emitsData = [];
            const arg = node.arguments[0];
            if (arg && arg.type === 'ArrayExpression') {
                arg.elements.forEach(el => {
                    if (el.type === 'Literal') emitsData.push(el.value);
                });
            } else if (arg && arg.type === 'ObjectExpression') {
                arg.properties.forEach(p => {
                    const key = p.key ? (p.key.name || p.key.value) : null;
                    if (key) emitsData.push(key);
                });
            }
            result.emits_definition = emitsData;
        }
        
        // --- OPTIONS API ---
        if (node.type === 'Property' && node.key) {
            const keyName = node.key.name || node.key.value;
            if (keyName === 'methods' && node.value && node.value.type === 'ObjectExpression') {
                node.value.properties.forEach(p => { 
                    const k = p.key ? (p.key.name || p.key.value) : null;
                    if (k) result.methods.push(k); 
                });
            } else if (keyName === 'props' && node.value && node.value.type === 'ObjectExpression') {
                const propsData = {};
                node.value.properties.forEach(p => {
                    const k = p.key ? (p.key.name || p.key.value) : null;
                    if (k) {
                        const propName = k;
                        let type = 'any';
                        let required = false;
                        if (p.value.type === 'Identifier') {
                            type = p.value.name;
                        } else if (p.value.type === 'ObjectExpression') {
                            p.value.properties.forEach(ip => {
                                const ik = ip.key ? (ip.key.name || ip.key.value) : null;
                                if (ik === 'type') type = ip.value.name || 'any';
                                if (ik === 'required') required = ip.value.value === true;
                            });
                        }
                        propsData[propName] = { type, required };
                    }
                });
                result.props_definition = { ...result.props_definition, ...propsData };
            } else if (keyName === 'emits' && node.value && (node.value.type === 'ArrayExpression' || node.value.type === 'ObjectExpression')) {
                const emitsData = [];
                if (node.value.type === 'ArrayExpression') {
                    node.value.elements.forEach(el => { if (el.type === 'Literal') emitsData.push(el.value); });
                } else {
                    node.value.properties.forEach(p => { 
                        const k = p.key ? (p.key.name || p.key.value) : null;
                        if (k) emitsData.push(k); 
                    });
                }
                result.emits_definition = emitsData;
            } else if (keyName === 'computed' && node.value && node.value.type === 'ObjectExpression') {
                node.value.properties.forEach(p => { 
                    const k = p.key ? (p.key.name || p.key.value) : null;
                    if (k) result.computed.push(k); 
                });
            } else if (keyName === 'watch' && node.value && node.value.type === 'ObjectExpression') {
                node.value.properties.forEach(p => { 
                    const k = p.key ? (p.key.name || p.key.value) : null;
                    if (k) result.watchers.push(k); 
                });
            } else if (keyName === 'components' && node.value && node.value.type === 'ObjectExpression') {
                node.value.properties.forEach(p => { 
                    const k = p.key ? (p.key.name || p.key.value) : null;
                    if (k) result.registered_components.push(k); 
                });
            }
        }
    });

    return result;

} catch (e) {
    return { error: e.message, stack: e.stack };
}
}

if (isWorker) {
    const readline = require('readline');
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        terminal: false
    });

    rl.on('line', (line) => {
        const filePath = line.trim();
        if (filePath) {
            const result = parseFile(filePath);
            console.log(JSON.stringify(result));
        }
    });
} else {
    const result = parseFile(filePathArg);
    console.log(JSON.stringify(result));
    process.exit(0);
}
