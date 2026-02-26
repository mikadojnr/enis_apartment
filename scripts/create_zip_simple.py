#!/usr/bin/env python3
"""
Create a complete zip file of the project for distribution - simplified version
"""

import zipfile
import shutil
from pathlib import Path
from datetime import datetime

def create_project_zip():
    """Create a zip file of the entire project"""
    
    project_root = Path('/vercel/share/v0-project')
    output_dir = project_root / 'dist'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create zip filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f'eni-apartments-complete-{timestamp}.zip'
    zip_path = output_dir / zip_filename
    
    # Directories to exclude
    exclude_dirs = {'.git', '__pycache__', '.venv', 'venv', 'dist', '.pytest_cache', '.vscode', '.idea', 'node_modules'}
    exclude_files = {'.gitignore', '.env.local', '.DS_Store'}
    
    def should_exclude(path):
        """Check if path should be excluded"""
        # Check if any parent directory is excluded
        if any(part in exclude_dirs for part in path.parts):
            return True
        
        # Check if file is excluded
        if path.name in exclude_files or path.suffix == '.pyc':
            return True
        
        return False
    
    print(f"[v0] Creating zip file: {zip_path}")
    print(f"[v0] Project root: {project_root}")
    
    file_count = 0
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Use glob to find all files recursively
        for filepath in project_root.rglob('*'):
            if filepath.is_file() and not should_exclude(filepath):
                # Calculate archive name (relative path from project root)
                arcname = filepath.relative_to(project_root)
                
                try:
                    zipf.write(filepath, arcname)
                    file_count += 1
                    if file_count % 50 == 0:
                        print(f"[v0] Added {file_count} files...")
                except Exception as e:
                    print(f"[v0] Warning: Could not add {filepath}: {e}")
    
    # Get file size
    zip_size = zip_path.stat().st_size
    zip_size_mb = zip_size / (1024 * 1024)
    
    print(f"\n[v0] ✓ Zip file created successfully!")
    print(f"[v0] Location: {zip_path}")
    print(f"[v0] Size: {zip_size_mb:.2f} MB")
    print(f"[v0] Files included: {file_count}")
    print(f"\n[v0] Download from: dist/{zip_filename}")
    
    # Also create a latest symlink for convenience
    latest_link = output_dir / 'eni-apartments-latest.zip'
    if latest_link.exists():
        latest_link.unlink()
    shutil.copy(zip_path, latest_link)
    print(f"[v0] Latest link created: dist/eni-apartments-latest.zip")
    
    return zip_path

if __name__ == '__main__':
    try:
        create_project_zip()
    except Exception as e:
        print(f"[v0] Error creating zip file: {e}")
        import traceback
        traceback.print_exc()
