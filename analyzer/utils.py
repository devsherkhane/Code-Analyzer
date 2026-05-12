import os
import shutil
import zipfile
from db import cursor, db

def unzip(zip_path):
    folder = "temp"
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.mkdir(folder)
    if zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(folder)
    else:
        shutil.copy(zip_path, os.path.join(folder, os.path.basename(zip_path)))
    return folder

def insert_project(project_name):
    cursor.execute("INSERT INTO projects(project_name) VALUES(%s)", (project_name,))
    db.commit()
    return cursor.lastrowid

def insert_folder(pid, f_path, root_folder):
    folder_name = os.path.basename(f_path) if f_path != root_folder else "root"
    cursor.execute(
        "INSERT INTO folders (project_id, folder_name, path) VALUES (%s, %s, %s)",
        (pid, folder_name, f_path)
    )
    db.commit()
    return cursor.lastrowid

def insert_file(folder_id, file_path):
    file_name = os.path.basename(file_path)
    cursor.execute(
        "INSERT INTO files(folder_id, file_name, path) VALUES(%s, %s, %s)",
        (folder_id, file_name, file_path)
    )
    db.commit()
    return cursor.lastrowid
def insert_component_data_v2(file_id, components, elements, apis):
    # 1. Insert PageBody
    cursor.execute(
        "INSERT INTO components (file_id, component_name, type) VALUES (%s, %s, %s)",
        (file_id, "PageBody", "Container")
    )
    db.commit()
    default_comp_id = cursor.lastrowid

    # 2. Insert Custom Components
    for comp in components:
        cursor.execute(
            "INSERT INTO components (file_id, component_name, type) VALUES (%s, %s, %s)",
            (file_id, comp['name'], comp.get('type', 'Custom'))
        )

    # 3. Process elements (Buttons and Headers logic)
    target_btn_types = ["button", "v-btn", "m-btn", "btn", "basebutton", "appbutton"]

    for el in elements:
        # Standard insert into ui_elements
        cursor.execute(
            "INSERT INTO ui_elements (component_id, element_type, event) VALUES (%s, %s, %s)",
            (default_comp_id, el['type'], el['event'])
        )
        current_element_id = cursor.lastrowid 

        # Task-4: Linking Logic for ui_buttons
        is_button = any(t.lower() == el['type'].lower() for t in target_btn_types)
        
        if is_button:
            # Get the page header text attached during extraction from extractor.py
            page_header = el.get('found_header', '')
            btn_text = el['label'] if el['label'] else "[No Text]"
            
            cursor.execute(
                """INSERT INTO ui_buttons (file_id, element_id, button_text, css_class, headers) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (file_id, current_element_id, btn_text, el['class'], page_header)
            )

    # --- RESTORED API INSERTION LOGIC ---
    # 4. Insert API calls
    for api in apis:
        cursor.execute(
            "INSERT INTO api_calls (file_id, method, url, payload_data) VALUES (%s, %s, %s, %s)",
            (file_id, api.get('method', 'GET'), api.get('url', 'N/A'), api.get('payload', ''))
        )
    
    db.commit()
    return default_comp_id