"""
ast_to_fingerprint.py — Converts raw AST parse data into a compact,
LLM-readable structural fingerprint for token-efficient AI triage.

Instead of sending 4,000-12,000 tokens of raw source code, this produces
a ~400-600 token structured summary that captures all architecturally
relevant signals from the AST.
"""


def build_fingerprint(bundle):
    """
    Takes a context bundle (from ai_context_fetcher) and produces a
    compact text fingerprint the LLM can reason about.
    
    Args:
        bundle: dict with keys like file_name, file_path, context,
                metrics, ast_data, dependency_impact, etc.
    
    Returns:
        str: A multi-line structured fingerprint.
    """
    lines = []
    
    file_name = bundle.get("file_name", "Unknown")
    file_path = bundle.get("file_path", "")
    context = bundle.get("context", {})
    metrics = bundle.get("metrics", {})
    ast_data = bundle.get("ast_data", {})
    dep_impact = bundle.get("dependency_impact", [])
    downstream = bundle.get("downstream_impact", [])
    
    # --- Header ---
    lines.append(f"FILE: {file_name}")
    lines.append(f"PATH: {file_path}")
    
    route = context.get("route", "unknown")
    if route and route != "unknown":
        lines.append(f"ROUTE: {route}")
    
    # --- Complexity ---
    cyc = metrics.get("cyclomatic_complexity", 1)
    cog = metrics.get("cognitive_complexity", 0)
    depth = metrics.get("nesting_depth", 0)
    loc = metrics.get("loc", 0)
    lines.append(f"COMPLEXITY: cyclomatic={cyc}, cognitive={cog}, nesting_depth={depth}, LOC={loc}")
    
    # --- Template ---
    t_lines = metrics.get("template_lines", 0)
    ui_elements = ast_data.get("ui_elements", [])
    lines.append(f"TEMPLATE: {t_lines} lines, {len(ui_elements)} UI elements")
    
    # --- Props ---
    props = ast_data.get("props_definition") or metrics.get("props_definition") or {}
    if props:
        prop_strs = []
        for name, info in props.items():
            if isinstance(info, dict):
                req = ", required" if info.get("required") else ""
                prop_strs.append(f"{name}({info.get('type', 'any')}{req})")
            else:
                prop_strs.append(str(name))
        lines.append(f"PROPS({len(props)}): {', '.join(prop_strs)}")
    
    # --- Emits ---
    emits = ast_data.get("emits_definition") or metrics.get("emits_definition") or []
    if emits:
        lines.append(f"EMITS({len(emits)}): {', '.join(str(e) for e in emits)}")
    
    # --- Methods ---
    methods = ast_data.get("methods", [])
    if methods:
        lines.append(f"METHODS({len(methods)}): {', '.join(methods[:15])}")
        if len(methods) > 15:
            lines[-1] += f" ... (+{len(methods) - 15} more)"
    
    # --- Computed ---
    computed = ast_data.get("computed", [])
    if computed:
        lines.append(f"COMPUTED({len(computed)}): {', '.join(computed[:10])}")
    
    # --- Watchers ---
    watchers = ast_data.get("watchers", [])
    if watchers:
        lines.append(f"WATCHERS({len(watchers)}): {', '.join(watchers[:10])}")
    
    # --- Imports ---
    imports = ast_data.get("imports", [])
    if imports:
        import_strs = [f"{imp.get('name', '?')}({imp.get('source', '?')})" for imp in imports[:10]]
        lines.append(f"IMPORTS({len(imports)}): {', '.join(import_strs)}")
        if len(imports) > 10:
            lines[-1] += f" ... (+{len(imports) - 10} more)"
    
    # --- Child Components ---
    registered = ast_data.get("registered_components", [])
    imported_comps = ast_data.get("imported_components", [])
    child_comps = list(set(registered + imported_comps))
    if child_comps:
        lines.append(f"CHILD_COMPONENTS({len(child_comps)}): {', '.join(child_comps[:10])}")
    
    # --- API Calls ---
    api_calls = ast_data.get("api_calls", [])
    real_apis = [a for a in api_calls if a.get("url")]
    if real_apis:
        api_strs = [f"{a.get('method', 'GET')} {a.get('url', '?')}" for a in real_apis[:5]]
        lines.append(f"API_CALLS({len(real_apis)}): {', '.join(api_strs)}")
    
    # --- AST Flags (critical for issue detection) ---
    flags = [a for a in api_calls if a.get("flag")]
    if flags:
        flag_strs = []
        for f in flags:
            flag_name = f.get("flag", "")
            extra = f.get("var") or f.get("action") or f.get("tag") or f.get("url") or ""
            if extra:
                flag_strs.append(f"{flag_name}({extra})")
            else:
                flag_strs.append(flag_name)
        lines.append(f"AST_FLAGS: {', '.join(flag_strs)}")
    
    # --- Accessibility Analysis ---
    a11y_issues = _analyze_a11y(ui_elements)
    if a11y_issues:
        lines.append(f"A11Y_ISSUES: {'; '.join(a11y_issues)}")
    
    # --- Style Metrics ---
    style_metrics = ast_data.get("style_metrics", {})
    colors = metrics.get("colors_used", []) or style_metrics.get("colors", [])
    raw_hex = [c for c in colors if isinstance(c, str) and c.startswith('#')]
    fonts = metrics.get("font_families", []) or style_metrics.get("fonts", [])
    
    style_parts = []
    if raw_hex:
        style_parts.append(f"{len(raw_hex)} hex colors ({', '.join(raw_hex[:6])})")
    if fonts:
        style_parts.append(f"fonts: {', '.join(fonts[:4])}")
    if style_parts:
        lines.append(f"STYLES: {', '.join(style_parts)}")
    
    # --- Contrast Issues ---
    contrast = metrics.get("contrast_issues", [])
    if contrast:
        lines.append(f"CONTRAST_ISSUES({len(contrast)}): {'; '.join(contrast[:3])}")
    
    # --- Architectural Context ---
    siblings = context.get("siblings", [])
    if siblings:
        lines.append(f"SIBLINGS({len(siblings)}): {', '.join(siblings[:8])}")
    
    if downstream:
        lines.append(f"DOWNSTREAM_IMPACT: {len(downstream)} files depend on this ({', '.join(str(d) for d in downstream[:5])})")
    elif dep_impact:
        lines.append(f"DEPENDENCY_IMPACT: {len(dep_impact)} connections")
    
    return "\n".join(lines)


def _analyze_a11y(ui_elements):
    """
    Analyze UI elements from AST for accessibility issues.
    Returns a list of human-readable issue strings.
    """
    issues = []
    
    buttons_no_label = 0
    imgs_no_alt = 0
    inputs_no_label = 0
    links_no_text = 0
    interactive_no_aria = 0
    
    for el in ui_elements:
        tag = (el.get("tag") or "").lower()
        attrs = el.get("attrs", {})
        label = (el.get("label") or "").strip()
        aria_label = attrs.get("aria-label", "")
        
        # Buttons without accessible name
        if tag in ("button", "v-btn"):
            if not label and not aria_label and not attrs.get("title"):
                buttons_no_label += 1
        
        # Images without alt text
        if tag == "img":
            if not attrs.get("alt") and not aria_label:
                imgs_no_alt += 1
        
        # Input fields without labels
        if tag in ("input", "textarea", "select"):
            if not aria_label and not attrs.get("id") and not attrs.get("placeholder"):
                inputs_no_label += 1
        
        # Links without text
        if tag == "a":
            if not label and not aria_label:
                links_no_text += 1
        
        # Interactive elements without ARIA roles
        if attrs.get("@click") or attrs.get("v-on:click"):
            if tag not in ("button", "a", "input", "select", "textarea", "v-btn"):
                if not attrs.get("role") and not aria_label:
                    interactive_no_aria += 1
    
    if buttons_no_label:
        issues.append(f"{buttons_no_label} buttons without accessible name")
    if imgs_no_alt:
        issues.append(f"{imgs_no_alt} images without alt text")
    if inputs_no_label:
        issues.append(f"{inputs_no_label} inputs without label/aria-label")
    if links_no_text:
        issues.append(f"{links_no_text} links without text")
    if interactive_no_aria:
        issues.append(f"{interactive_no_aria} clickable elements missing role/aria-label")
    
    return issues


def build_batch_fingerprints(bundles):
    """
    Build fingerprints for a batch of bundles.
    Returns list of dicts with file_id and fingerprint text.
    """
    results = []
    for b in bundles:
        fp = build_fingerprint(b)
        results.append({
            "file_id": str(b.get("file_id")),
            "file_name": b.get("file_name", "Unknown"),
            "fingerprint": fp
        })
    return results
