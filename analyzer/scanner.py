import os

def scan_folder(root):
    files = []
    folders = []
    
    # List of folders to ignore (industry-standard exclusions)
    exclude = set([
        'node_modules', 'dist', '.git', '__pycache__', 'build', 'coverage',
        '.nuxt', '.next', '.vite', 'vendor', '.output', '.cache', '.parcel-cache',
        '.turbo', 'storybook-static', '.svelte-kit', 'out', '.vercel', '.netlify'
    ])

    # Include all web frontend file types
    include_extensions = ('.vue', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss')

    for path, dirs, filenames in os.walk(root):
        # Modify dirs in-place to skip excluded folders
        dirs[:] = [d for d in dirs if d not in exclude]
        
        for d in dirs:
            folders.append(os.path.join(path, d))
            
        for f in filenames:
            if f.lower().endswith(include_extensions):
                files.append(os.path.join(path, f))
                
    return files, folders