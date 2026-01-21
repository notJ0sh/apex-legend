# RUN THIS SCRIPT TO AUTO REMOVE __pycache_ DIRECTORIES AND SPECIFIC FILES

import os
import shutil


def cleanup():
    # Remove __pycache__ directories
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            shutil.rmtree(pycache_path)
            print(f"Removed: {pycache_path}")

    # Remove specific files (like the db's and other stuff add the name here)
    files_to_remove = ['user_data.db', 'files_data.db']
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed: {file}")

    print("Cleanup complete!")


if __name__ == "__main__":
    cleanup()
