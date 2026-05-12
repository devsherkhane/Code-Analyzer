import re
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
def extract_fonts(content):
    fonts = set()
    try:
        # Find font-family styles in CSS or inline styles
        matches = re.finditer(r'font-family:\s*["\']?([^";,]+)', content, re.IGNORECASE)
        for match in matches:
            font = match.group(1).strip().lower()
            if font and len(font) > 1:
                fonts.add(font)
        
        # Find common fonts mentioned in class names (e.g., class="font-roboto")
        class_matches = re.finditer(r'class="[^"]*\b(roboto|arial|sans-serif|mono)[^"]*"', content, re.IGNORECASE)
        for match in class_matches:
            fonts.add(match.group(1).lower())
    except:
        pass
    return fonts

def extract_font_sizes(content):
    sizes = set()
    try:
        matches = re.finditer(r'font-size:\s*(\d+)(?:px|em|rem)', content, re.IGNORECASE)
        for match in matches:
            sizes.add(f"{match.group(1)}px")
    except:
        pass
    return sizes

def extract_colors(content):
    colors = set()
    try:
        # HEX colors (e.g., #ffffff, #000)
        hex_matches = re.finditer(r'#[0-9a-fA-F]{3,6}', content)
        for match in hex_matches:
            colors.add(match.group(0).lower())
        
        # RGB colors (e.g., rgb(255, 255, 255))
        rgb_matches = re.finditer(r'rgb\([^)]+\)', content, re.IGNORECASE)
        for match in rgb_matches:
            colors.add(match.group(0).lower())
        
        # Standard named colors used in CSS 'color' or 'background' properties
        color_names = ['red', 'blue', 'green', 'gray', 'grey', 'white', 'black', 'yellow', 'orange']
        for color in color_names:
            if re.search(rf'color:\s*{color}', content, re.IGNORECASE):
                colors.add(color)
    except:
        pass
    return colors

def extract_padding(content):
    paddings = set()
    try:
        matches = re.finditer(r'padding:\s*(\d+)(?:px|em|rem)', content, re.IGNORECASE)
        for match in matches:
            paddings.add(f"{match.group(1)}px")
    except:
        pass
    return paddings

def extract_margins(content):
    margins = set()
    try:
        matches = re.finditer(r'margin:\s*(\d+)(?:px|em|rem)', content, re.IGNORECASE)
        for match in matches:
            margins.add(f"{match.group(1)}px")
    except:
        pass
    return margins
def extract_header_styles(content):
    """Extract header font sizes and styles"""
    styles = {"h1_sizes": set(), "h2_sizes": set(), "h3_sizes": set()}
    try:
        # Find all h1, h2, h3 tags with styles
        for tag_name in ['h1', 'h2', 'h3']:
            pattern = rf'<{tag_name}[^>]*style="([^"]*)"'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                style_str = match.group(1)
                # Specifically capture the numeric pixel value
                size_match = re.search(r'font-size:\s*(\d+)px', style_str)
                if size_match:
                    styles[f'{tag_name}_sizes'].add(f"{size_match.group(1)}px")
    except:
        pass
    return styles
def extract_alignment_info(content, elements):
    """Extract text alignment information"""
    alignments = set()
    try:
        for elem in elements:
            # Look for the style attribute in the specified tags (e.g., h1, h2, h3)
            pattern = rf'<{elem}[^>]*style="([^"]*)"'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                style_str = match.group(1)
                # Capture 'text-align' or just 'align' values
                align_match = re.search(r'(?:text-)?align:\s*(\w+)', style_str)
                if align_match:
                    alignments.add(align_match.group(1))
    except:
        pass
    return alignments


def get_metrics(file_path, tags):
    """Extract metrics from a Vue file with isolated template and style scanning"""
    try:
        with open(file_path, 'r', encoding="utf8") as f:
            content = f.read()
            lines = content.splitlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return get_empty_metrics()

    # --- 1. Surgical Block Extraction ---
    # Extract Template specifically for UI Spelling
    # Extract Template specifically for UI Spelling
    template_match = re.search(r'<template>(.*?)</template>', content, re.DOTALL)
    template_content = template_match.group(1) if template_match else ""
    
    # 1. Strip Vue mustache bindings (e.g., {{ user.firstName }})
    text_without_vars = re.sub(r'\{\{.*?\}\}', ' ', template_content, flags=re.DOTALL)
    
    # 2. Safely extract only human-readable text using BeautifulSoup
    soup_text = BeautifulSoup(text_without_vars, "html.parser").get_text(separator=' ')
    
    # 3. Clean up extra whitespace and stray braces
    visible_ui_text = ' '.join(soup_text.split())

    # Extract Style specifically for Button/UI Color validation
    style_match = re.search(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)
    css_content = style_match.group(1) if style_match else ""

    # --- 2. Component Metrics (Script Logic) ---
    methods = re.findall(r'methods:\s*{', content)
    computed = re.findall(r'computed:\s*{', content)
    watchers = re.findall(r'watch:\s*{', content)
    
    def count_props(block_name):
        try:
            match = re.search(rf'{block_name}:\s*\{{(.*?)\n\s*\}}', content, re.DOTALL)
            if not match: return 0
            return len(re.findall(r'\w+\s*\(', match.group(1)))
        except Exception:
            return 0

    # Script-based Component Detection
    try:
        imported_components = re.findall(r'import\s+(\w+)\s+from', content)
        comp_block_match = re.search(r'components\s*:\s*\{([^}]*)\}', content, re.DOTALL)
        registered_locally = []
        if comp_block_match:
            registered_locally = re.findall(r'(\w+)\s*[:|,]', comp_block_match.group(1))
        script_components = list(set(imported_components + registered_locally))
    except Exception:
        script_components = []

    # --- 3. UI/Header Metrics ---
    try:
        headers = {
            "h1": len(re.findall(r'<h1', template_content, re.IGNORECASE)),
            "h2": len(re.findall(r'<h2', template_content, re.IGNORECASE)),
            "h3": len(re.findall(r'<h3', template_content, re.IGNORECASE))
        }
    except Exception:
        headers = {"h1": 0, "h2": 0, "h3": 0}

    # Use isolated CSS content for style metrics to ensure accuracy
    header_styles = extract_header_styles(content) # Keeps full content check for inline styles
    header_alignment = extract_alignment_info(template_content, ['h1', 'h2', 'h3'])
    
    # Global Style Extraction (Now uses full content but targets CSS patterns)
    font_families = extract_fonts(content)
    font_sizes = extract_font_sizes(content)
    colors_used = extract_colors(css_content) # Target ONLY the CSS block for color inventory
    padding_values = extract_padding(content)
    margin_values = extract_margins(content)

    # Calculate nesting depth within template
    max_depth = 0
    try:
        if tags:
            for tag in tags:
                depth = len(list(tag.parents))
                if ("v-if" in tag.attrs or "v-for" in tag.attrs) and depth > max_depth:
                    max_depth = depth
    except Exception:
        max_depth = 0

    return {
        "loc": len(lines),
        "methods": count_props("methods") or len(methods),
        "computed": count_props("computed") or len(computed),
        "watchers": count_props("watch") or len(watchers),
        "template_lines": len(template_content.splitlines()),
        "nesting_depth": max_depth,
        "content": content,
        "css_content": css_content,       # New: Isolated CSS for Button Color rules
        "script_components": script_components,
        "visible_text": visible_ui_text,  # Updated: Only UI text for Spelling
        "headers": headers,
        "header_styles": {k: list(v) for k, v in header_styles.items()},
        "header_alignment": list(header_alignment),
        "padding_values": list(padding_values),
        "margin_values": list(margin_values),
        "font_families": list(font_families),
        "font_sizes": list(font_sizes),
        "colors_used": list(colors_used),
        "contrast_issues": [],
    }

# ... (Keep existing extract_header_styles, extract_alignment_info, etc. functions) ...

def get_empty_metrics():
    """Return empty metrics dict structure with new fields"""
    return {
        "loc": 0,
        "methods": 0,
        "computed": 0,
        "watchers": 0,
        "template_lines": 0,
        "nesting_depth": 0,
        "content": "",
        "css_content": "",
        "script_components": [],
        "visible_text": "",
        "headers": {"h1": 0, "h2": 0, "h3": 0},
        "header_styles": {"h1_sizes": [], "h2_sizes": [], "h3_sizes": []},
        "header_alignment": [],
        "padding_values": [],
        "margin_values": [],
        "font_families": [],
        "font_sizes": [],
        "colors_used": [],
        "contrast_issues": [],
    }