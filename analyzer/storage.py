import threading
import json
import os
from datetime import datetime

class JSONStorage:
    """
    A thread-safe in-memory storage manager that replaces the MySQL database.
    It holds objects in memory until export_all() writes them to JSON files.
    """
    def __init__(self):
        self._lock = threading.Lock()
        
        # In-memory "tables"
        self.tables = {
            "projects": [],
            "folders": [],
            "files": [],
            "components": [],
            "ui_elements": [],
            "ui_buttons": [],
            "api_calls": [],
            "analysis_flags": [],
            "component_complexity": [],
            "ui_consistency_reports": [],
            "accessibility_reports": [],
            "dependency_graph": {
                "connections": [],
                "file_map": {},
                "impact_map": {}
            }
        }
        
        # Simulating AUTO_INCREMENT keys
        self.auto_inc = {table: 1 for table in self.tables.keys()}

    def _insert(self, table_name, data):
        """Thread-safe insert that assigns an ID and returns it."""
        with self._lock:
            # Generate ID based on table
            if table_name in ["projects", "folders", "ui_consistency_reports", "accessibility_reports"]:
                id_col = "id"
            elif table_name == "files":
                id_col = "file_id"
            elif table_name == "components":
                id_col = "component_id"
            elif table_name == "ui_elements":
                id_col = "element_id"
            elif table_name == "ui_buttons":
                id_col = "button_id"
            elif table_name == "api_calls":
                id_col = "api_id"
            elif table_name == "analysis_flags":
                id_col = "flag_id"
            elif table_name == "component_complexity":
                id_col = "complexity_id"
            else:
                id_col = "id"

            data[id_col] = self.auto_inc[table_name]
            self.auto_inc[table_name] += 1
            
            # Auto-timestamp for reports
            if table_name in ["ui_consistency_reports", "accessibility_reports"]:
                data["created_at"] = datetime.now().isoformat()
            
            self.tables[table_name].append(data)
            return data[id_col]

    def insert_project(self, project_name):
        return self._insert("projects", {"project_name": project_name})

    def insert_folder(self, project_id, folder_name, path):
        return self._insert("folders", {
            "project_id": project_id,
            "folder_name": folder_name,
            "path": path
        })

    def insert_file(self, folder_id, file_name, path, imports=None, exports=None, metrics=None, context=None, ast_data=None):
        return self._insert("files", {
            "folder_id": folder_id,
            "file_name": file_name,
            "path": path,
            "imports": imports or [],
            "exports": exports or [],
            "metrics": metrics or {},
            "context": context or {},
            "ast_data": ast_data or {}
        })

    def run_consistency_check(self):
        """Performs project-wide Layer 2 consistency analysis."""
        from collections import Counter, defaultdict
        
        button_map = defaultdict(list) # action -> list of classes
        all_font_sizes = Counter()
        all_paddings = Counter()
        ghost_tokens = [] # list of (file, hex)
        
        for file in self.tables["files"]:
            m = file.get("metrics", {})
            f_name = file["file_name"]
            
            # Button consistency
            for b in m.get("button_metrics", []):
                button_map[b["action"]].append(b["class"])
                
            # Typography scale
            for fs in m.get("font_sizes", []):
                all_font_sizes[fs] += 1
                
            # Spacing
            for p in m.get("padding_values", []):
                all_paddings[p] += 1
                
            # Ghost tokens (Hardcoded hex vs CSS vars)
            raw_hex = m.get("raw_hex_codes", [])
            tokens = m.get("token_usage", [])
            if raw_hex and tokens:
                for h in raw_hex:
                    ghost_tokens.append((file["file_id"], h))

        # --- Generate Reports ---
        
        # 1. Inconsistent Buttons
        for action, classes in button_map.items():
            unique_classes = set(classes)
            if len(unique_classes) > 1:
                self.insert_ui_consistency_report(
                    0, "Button Consistency", "INCONSISTENT_BUTTON_STYLE",
                    f"Action '{action}' uses {len(unique_classes)} different styles: {', '.join(unique_classes)}", 
                    "medium"
                )

        # 2. Typography Chaos
        if len(all_font_sizes) >= 6:
             self.insert_ui_consistency_report(
                0, "Typography", "TYPOGRAPHY_SCALE_CHAOS",
                f"Project uses {len(all_font_sizes)} distinct font sizes. Recommended: < 6.",
                "low"
            )

        # 3. Spacing Chaos
        if len(all_paddings) > 4:
            self.insert_ui_consistency_report(
                0, "Spacing", "SPACING_CHAOS",
                f"Project uses {len(all_paddings)} distinct padding values. Sign of missing design system.",
                "low"
            )

        # 4. Ghost Tokens
        for f_id, hex_val in ghost_tokens[:10]: # Limit report size
            self.insert_ui_consistency_report(
                f_id, "Design Tokens", "HARDCODED_VS_TOKEN_MISMATCH",
                f"Hardcoded color {hex_val} found in file that otherwise uses CSS variables.",
                "medium"
            )

    def insert_component(self, file_id, component_name, comp_type):
        return self._insert("components", {
            "file_id": file_id,
            "component_name": component_name,
            "type": comp_type
        })

    def insert_ui_element(self, component_id, element_type, event):
        return self._insert("ui_elements", {
            "component_id": component_id,
            "element_type": element_type,
            "event": event
        })

    def insert_ui_button(self, file_id, element_id, button_text, css_class, headers):
        return self._insert("ui_buttons", {
            "file_id": file_id,
            "element_id": element_id,
            "button_text": button_text,
            "css_class": css_class,
            "headers": headers
        })

    def insert_api_call(self, file_id, method, url, payload_data):
        return self._insert("api_calls", {
            "file_id": file_id,
            "method": method,
            "url": url,
            "payload_data": payload_data
        })

    def insert_analysis_flag(self, file_id, api_count, api_flags, payload_flags, component_flags, combined_condn_flags, specific_pattern_flags, ui_flags):
        return self._insert("analysis_flags", {
            "file_id": file_id,
            "api_count": api_count,
            "api_flags": api_flags,
            "payload_flags": payload_flags,
            "component_flags": component_flags,
            "combined_condn_flags": combined_condn_flags,
            "specific_pattern_flags": specific_pattern_flags,
            "ui_flags": ui_flags
        })

    def insert_component_complexity(self, file_id, component_id, lines_count, methods_count, computed_count, watchers_count, template_lines_count, child_component_count, flags, cyclomatic_complexity=1, cognitive_complexity=0):
        return self._insert("component_complexity", {
            "file_id": file_id,
            "component_id": component_id,
            "lines_count": lines_count,
            "methods_count": methods_count,
            "computed_count": computed_count,
            "watchers_count": watchers_count,
            "template_lines_count": template_lines_count,
            "child_component_count": child_component_count,
            "flags": flags,
            "cyclomatic_complexity": cyclomatic_complexity,
            "cognitive_complexity": cognitive_complexity
        })

    def insert_ui_consistency_report(self, file_id, rule_category, defect_type, finding_details, severity):
        return self._insert("ui_consistency_reports", {
            "file_id": file_id,
            "rule_category": rule_category,
            "defect_type": defect_type,
            "finding_details": finding_details,
            "severity": severity
        })

    def insert_accessibility_report(self, file_id, rule_category, defect_type, finding_details, severity):
        return self._insert("accessibility_reports", {
            "file_id": file_id,
            "rule_category": rule_category,
            "defect_type": defect_type,
            "finding_details": finding_details,
            "severity": severity
        })

    def export_all(self):
        """Dumps all tables into backend/json_reports/"""
        # Determine the paths correctly
        # This script is in analyzer/storage.py, so .. is root
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        export_dir = os.path.normpath(os.path.join(curr_dir, "..", "backend", "json_reports"))
            
        os.makedirs(export_dir, exist_ok=True)
        print(f"[STORAGE] Exporting in-memory data to JSON in {export_dir}")
        for table_name, rows in self.tables.items():
            output_file = os.path.join(export_dir, f"{table_name}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(rows, f, indent=4)
            print(f"  -> Exported {len(rows)} rows to {table_name}.json")
