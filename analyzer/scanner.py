import os

def scan_folder(root):
    files = []
    folders = []
    
    # List of folders to ignore
    exclude = set(['node_modules', 'dist', '.git', '__pycache__'])

    # Only include code files for dependency analysis
    include_extensions = ('.vue', '.js', '.ts', '.jsx', '.tsx')

    for path, dirs, filenames in os.walk(root):
        # Modify dirs in-place to skip excluded folders
        dirs[:] = [d for d in dirs if d not in exclude]
        
        for d in dirs:
            folders.append(os.path.join(path, d))
            
        for f in filenames:
            if f.lower().endswith(include_extensions):
                files.append(os.path.join(path, f))
                
    return files, folders