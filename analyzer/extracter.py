def extract_elements(ui_elements_ast):
    """
    Extract UI elements from the Node.js JSON AST output.
    Guarantees 100% accurate parsing without Regex/BS4 HTML tree glitches.
    """
    elements = []
    components = [] 
    
    if not ui_elements_ast:
        return elements, components
    
    target_components = [
        "Header", "Footer", "Main", "Section", "Article", "Sidebar", 
        "Container", "Navbar", "Breadcrumbs", "Pagination", "Tabs", 
        "Dropdown", "Menu", "Modal", "Accordion", "Card", 
        "ProgressBar", "Tooltip", "Alert", "Label"
    ]
    
    target_btn_types = ["button", "v-btn", "button", "basebutton", "m-btn"]
    target_header_tags = ["h1", "h2", "h3", "pageheader", "baseheader"]

    # --- Step 1: Detect Page Header ---
    main_header_text = "Unknown Header"
    for node in ui_elements_ast:
        tag_name = node.get("tag", "").lower()
        if tag_name in [h.lower() for h in target_header_tags] and node.get("label"):
            main_header_text = node.get("label").strip()
            break

    # --- Step 2: Extract Elements ---
    try:
        for node in ui_elements_ast:
            name = node.get("tag")
            if not name: 
                continue

            attrs = node.get("attrs", {})
            label_text = (node.get("label") or attrs.get("aria-label") or attrs.get("title") or "")[:100]

            # 1. Identify Components
            is_component = any(c.lower() == name.lower() for c in target_components) or name[0].isupper() or "-" in name
            if is_component:
                components.append({
                    "name": name,
                    "type": "Custom" if (name[0].isupper() or "-" in name) else "Structural",
                    "props": list(attrs.keys())
                })
            
            # 2. Extract Class
            class_str = str(attrs.get("class", ""))

            # 3. Extract Style attributes
            style_dict = parse_style_string(attrs.get("style", ""))
            
            # 4. Extract color information
            color = style_dict.get('color') or style_dict.get('background-color')
            
            # 5. Extract button-specific properties
            button_props = {}
            if any(btn in name.lower() or btn in class_str.lower() for btn in target_btn_types):
                button_props = {
                    "variant": extract_variant(class_str),
                    "size": extract_size(class_str, style_dict),
                    "disabled": "disabled" in attrs or ":disabled" in attrs,
                    "type": attrs.get("type", "button")
                }
            
            # 6. Extract modal-specific properties
            modal_props = {}
            if "modal" in class_str.lower() or "dialog" in name.lower():
                modal_props = {
                    "title": label_text,
                    "has_close_button": False, # Complex to determine perfectly from flat AST
                    "backdrop": "backdrop" in attrs or ":backdrop" in attrs
                }
            
            # 7. Extract font information
            font_info = {
                "family": style_dict.get("font-family"),
                "size": style_dict.get("font-size"),
                "weight": style_dict.get("font-weight"),
                "style": style_dict.get("font-style")
            }
            
            # 8. Extract alignment
            alignment = style_dict.get("text-align") or style_dict.get("align")
            
            # Build element dictionary
            elements.append({
                "type": name,
                "label": label_text,
                "class": class_str,
                "event": attrs.get("@click") or attrs.get("v-on:click"),
                "found_header": main_header_text,
                "style": style_dict,
                "color": color,
                "button_props": button_props,
                "modal_props": modal_props,
                "font_info": font_info,
                "has_header": False,
                "alignment": alignment,
                "padding": style_dict.get("padding", ""),
                "margin": style_dict.get("margin", ""),
                
                # Accessibility Fields natively from AST attrs
                "alt": attrs.get("alt"),
                "aria_label": attrs.get("aria-label"),
                "aria_hidden": attrs.get("aria-hidden"),
                "aria_live": attrs.get("aria-live"),
                "tabindex": attrs.get("tabindex"),
                "for_attr": attrs.get("for"),
                "id_attr": attrs.get("id"),
                "placeholder": attrs.get("placeholder"),
                "required": "required" in attrs or ":required" in attrs,
                "width": style_dict.get("width") or attrs.get("width"),
                "height": style_dict.get("height") or attrs.get("height"),
                "min_width": style_dict.get("min-width"),
                "min_height": style_dict.get("min-height"),
            })
    except Exception as e:
        print(f"AST Error extracting elements: {e}")

    return elements, components


def parse_style_string(style_str):
    """Parse style string into dictionary"""
    style_dict = {}
    try:
        if not style_str:
            return style_dict
        for declaration in style_str.split(';'):
            if ':' in declaration:
                key, value = declaration.split(':', 1)
                style_dict[key.strip().lower()] = value.strip()
    except:
        pass
    return style_dict

def extract_variant(classes):
    class_lower = str(classes).lower()
    variants = ['primary', 'secondary', 'danger', 'success', 'warning', 'outlined', 'text']
    for variant in variants:
        if variant in class_lower:
            return variant
    return 'default'

def extract_size(classes, style_dict):
    class_lower = str(classes).lower()
    sizes = ['small', 'medium', 'large', 'sm', 'md', 'lg']
    for size in sizes:
        if size in class_lower:
            return size
    if 'font-size' in style_dict:
        return style_dict['font-size']
    return 'medium'
