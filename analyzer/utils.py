import os
import shutil
import zipfile

def unzip(zip_path):
    # Always extract to backend/temp/ relative to the analyzer directory
    # so the Go backend's /file-content endpoint can serve files
    this_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(this_dir, "..", "backend", "temp"))
    
    if not os.path.exists(zip_path):
        print(f"  -> [ERROR] Input path not found: {zip_path}")
        # Create an empty temp so the script can still run/fail gracefully
        if not os.path.exists(folder): os.makedirs(folder, exist_ok=True)
        return folder

    if os.path.exists(folder):
        try:
            shutil.rmtree(folder)
        except Exception as e:
            print(f"  -> [WARNING] Failed to clean temp folder: {e}")
    
    if zipfile.is_zipfile(zip_path):
        os.makedirs(folder, exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Security: Check for path traversal attacks
                for member in zip_ref.namelist():
                    abspath_target = os.path.abspath(os.path.join(folder, member))
                    abspath_folder = os.path.abspath(folder)
                    if not abspath_target.startswith(abspath_folder):
                        print(f"  -> [SECURITY WARNING] Skipping suspicious file in ZIP: {member}")
                        continue
                zip_ref.extractall(folder)
        except Exception as e:
            print(f"  -> [ERROR] Failed to extract ZIP: {e}")
    elif os.path.isdir(zip_path):
        # Allow running on a direct folder path instead of only zips
        shutil.copytree(zip_path, folder)
    else:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        shutil.copy(zip_path, os.path.join(folder, os.path.basename(zip_path)))
    return folder

def insert_project(project_name, storage):
    return storage.insert_project(project_name)

def insert_folder(pid, f_path, root_folder, storage):
    folder_name = os.path.basename(f_path) if f_path != root_folder else "root"
    return storage.insert_folder(pid, folder_name, f_path)

def insert_file(folder_id, file_path, storage, imports=None, exports=None, metrics=None, ast_data=None):
    file_name = os.path.basename(file_path)
    return storage.insert_file(folder_id, file_name, file_path, imports, exports, metrics, ast_data=ast_data)

def insert_component_data_v2(file_id, components, elements, apis, storage):
    
    # 1. Insert PageBody
    default_comp_id = storage.insert_component(file_id, "PageBody", "Container")

    # 2. Insert Custom Components
    for comp in components:
        storage.insert_component(file_id, comp['name'], comp.get('type', 'Custom'))

    # 3. Process elements
    target_btn_types = ["button", "v-btn", "m-btn", "btn", "basebutton", "appbutton"]

    for el in elements:
        current_element_id = storage.insert_ui_element(default_comp_id, el['type'], el['event'])

        is_button = any(t.lower() == el['type'].lower() for t in target_btn_types)
        
        if is_button:
            page_header = el.get('found_header', '')
            btn_text = el['label'] if el['label'] else "[No Text]"
            storage.insert_ui_button(file_id, current_element_id, btn_text, el['class'], page_header)

    # 4. Insert API calls
    for api in apis:
        storage.insert_api_call(file_id, api.get('method', 'GET'), api.get('url', 'N/A'), api.get('payload', ''))
    
    return default_comp_id