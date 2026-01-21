"""Script to move email-related files to email_system folder"""
import shutil
from pathlib import Path

# Get the workspace root
workspace_root = Path(__file__).parent
email_system_dir = workspace_root / "email_system"

# Create email_system directory if it doesn't exist
email_system_dir.mkdir(exist_ok=True)

# Files to move
files_to_move = [
    "email_service.py",
    "email_manager.py",
    "email_patterns.json",
    "email_signatures.json"
]

# Folders to move
folders_to_move = [
    "email_logos"
]

print("Moving email-related files to email_system/ folder...")

# Move files
for file_name in files_to_move:
    source = workspace_root / file_name
    if source.exists():
        destination = email_system_dir / file_name
        shutil.move(str(source), str(destination))
        print(f"✓ Moved {file_name}")
    else:
        print(f"✗ {file_name} not found (skipping)")

# Move folders
for folder_name in folders_to_move:
    source = workspace_root / folder_name
    if source.exists() and source.is_dir():
        destination = email_system_dir / folder_name
        if destination.exists():
            # Merge contents if destination exists
            for item in source.iterdir():
                shutil.move(str(item), str(destination / item.name))
            source.rmdir()
        else:
            shutil.move(str(source), str(destination))
        print(f"✓ Moved {folder_name}/")
    else:
        print(f"✗ {folder_name}/ not found (skipping)")

print("\n✓ Done! Files moved to email_system/ folder")

