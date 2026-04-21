import os

def get_luminance(hex_color):
    """Calculate relative luminance from hex color"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = "".join([c*2 for c in hex_color])
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        # Using the standard relative luminance formula
        vals = []
        for v in [r, g, b]:
            v /= 255.0
            if v <= 0.03928:
                vals.append(v / 12.92)
            else:
                vals.append(((v + 0.055) / 1.055) ** 2.4)
        return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]
    except:
        return 0

def check_contrast_issues(colors):
    """Simple check for potential contrast issues between detected colors"""
    issues = []
    # Simplified: check each color against black and white as a heuristic
    for color in colors:
        if color.startswith('#'):
            lum = get_luminance(color)
            # Contrast against white (1.0)
            ratio_white = (1.0 + 0.05) / (lum + 0.05)
            # Contrast against black (0.0)
            ratio_black = (lum + 0.05) / (0.0 + 0.05)
            
            if ratio_white < 3.0 and ratio_black < 3.0:
                issues.append(f"Color {color} has poor contrast against both black and white (< 3:1).")
    return issues

def get_metrics(file_path, parsed_script):
    """
    Extract metrics strictly using standard string manipulation and 
    the provided Structural AST data. No regex allowed.
    """
    try:
        with open(file_path, 'r', encoding="utf8") as f:
            content = f.read()
            lines = content.splitlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return get_empty_metrics()

    # --- 1. Basic Template Metrics ---
    visible_ui_text = ""
    max_depth = 0
    t_lines = 0
    missing_alt_count = 0
    unlabeled_inputs = 0
    interactive_without_role = 0
    headers_count = {f"h{i}": 0 for i in range(1, 7)}
    
    if parsed_script and parsed_script.get('template_metrics'):
        t_metrics = parsed_script['template_metrics']
        visible_ui_text = t_metrics.get('visible_text', '')
        max_depth = t_metrics.get('max_depth', 0)
        t_lines = t_metrics.get('lines', 0)
        missing_alt_count = t_metrics.get('missing_alt_count', 0)
        unlabeled_inputs = t_metrics.get('unlabeled_inputs', 0)
        interactive_without_role = t_metrics.get('interactive_without_role', 0)
        
        for el in parsed_script.get("ui_elements", []):
            tag_name = el.get("tag", "").lower()
            if tag_name in headers_count:
                headers_count[tag_name] += 1
    
    # --- 2. Structural Component Metrics ---
    if parsed_script:
        num_methods = len(parsed_script.get("methods", []))
        num_computed = len(parsed_script.get("computed", []))
        num_watchers = len(parsed_script.get("watchers", []))
        
        imports = parsed_script.get("imported_components", [])
        regs = parsed_script.get("registered_components", [])
        script_components = list(set(imports + regs))
        
        script_metrics = parsed_script.get('script_metrics', {})
        cyc_val = script_metrics.get('cyclomatic_complexity', 1)
        cog_val = script_metrics.get('cognitive_complexity', 0)
    else:
        num_methods = num_computed = num_watchers = 0
        script_components = []
        cyc_val = 1
        cog_val = 0

    # --- 3. Style Metrics (Pure AST/Structural) ---
    font_families = []
    font_sizes = []
    colors_used = []
    padding_values = []
    margin_values = []
    
    if parsed_script and parsed_script.get('style_metrics'):
        s_metrics = parsed_script['style_metrics']
        font_families = sorted(list(set(s_metrics.get('fonts', []))))
        font_sizes = sorted(list(set(s_metrics.get('font_sizes', []))))
        colors_used = sorted(list(set(s_metrics.get('colors', []))))
        
        for item in s_metrics.get('spacing', []):
            prop = item.get('prop', '')
            val = item.get('val', '')
            if 'padding' in prop or val.startswith('p-'):
                padding_values.append(val)
            elif 'margin' in prop or val.startswith('m-'):
                margin_values.append(val)

    # --- 4. Element-Specific Analysis (Regex-free) ---
    button_metrics = []
    if parsed_script and parsed_script.get("ui_elements"):
        for el in parsed_script.get("ui_elements", []):
            if el.get("tag") == "button":
                label = el.get("label", "").strip().lower()
                action = "generic"
                # String-based semantic checks
                if "save" in label or "submit" in label or "confirm" in label: action = "confirm"
                elif "delete" in label or "remove" in label or "cancel" in label: action = "danger"
                
                button_metrics.append({
                    "label": label,
                    "class": el.get("attrs", {}).get("class", ""),
                    "action": action
                })

    # --- 5. Token & Ghost Detection ---
    raw_hex_codes = [c for c in colors_used if c.startswith('#')]
    token_usage = [c for c in colors_used if 'var(--' in c]

    return {
        "loc": len(lines),
        "methods": num_methods,
        "computed": num_computed,
        "watchers": num_watchers,
        "template_lines": t_lines,
        "nesting_depth": max_depth,
        "cyclomatic_complexity": cyc_val,
        "cognitive_complexity": cog_val,
        "content": content,
        "css_content": "", # CSS logic is now handled in Node AST
        "script_components": script_components,
        "visible_text": visible_ui_text,
        "headers": headers_count,
        "header_styles": {"h1_sizes": [], "h2_sizes": [], "h3_sizes": []}, # Simplified
        "header_alignment": [],
        "padding_values": sorted(list(set(padding_values))),
        "margin_values": sorted(list(set(margin_values))),
        "font_families": font_families,
        "font_sizes": font_sizes,
        "colors_used": colors_used,
        "raw_hex_codes": raw_hex_codes,
        "token_usage": token_usage,
        "button_metrics": button_metrics,
        "missing_alt_count": missing_alt_count,
        "unlabeled_inputs": unlabeled_inputs,
        "interactive_without_role": interactive_without_role,
        "hardcoded_colors": len(raw_hex_codes),
        "focus_styles": [],
        "hover_styles": [],
        "outline_rules": [],
        "contrast_issues": check_contrast_issues(colors_used),
        "props_definition": parsed_script.get("props_definition") if parsed_script else {},
        "emits_definition": parsed_script.get("emits_definition") if parsed_script else [],
    }

def get_empty_metrics():
    return {
        "loc": 0, "methods": 0, "computed": 0, "watchers": 0,
        "template_lines": 0, "nesting_depth": 0,
        "content": "", "css_content": "",
        "script_components": [], "visible_text": "",
        "headers": {f"h{i}": 0 for i in range(1, 7)},
        "header_styles": {"h1_sizes": [], "h2_sizes": [], "h3_sizes": []},
        "header_alignment": [],
        "padding_values": [], "margin_values": [],
        "font_families": [], "font_sizes": [], "colors_used": [],
        "raw_hex_codes": [], "token_usage": [],
        "button_metrics": [],
        "missing_alt_count": 0, "unlabeled_inputs": 0,
        "interactive_without_role": 0, "hardcoded_colors": 0,
        "focus_styles": [], "hover_styles": [], "outline_rules": [],
        "contrast_issues": [],
        "props_definition": {}, "emits_definition": [],
    }