import os 
import json 
from pathlib import Path 

import settings 

def take_snapshot(root_dir=Path(str(settings.DATA_DIR))):
    file_paths = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            file_paths.append(os.path.join(dirpath, fn))
    return file_paths

def save_snapshot(snapshot, snapshot_file=Path(str(settings.SNAPSHOT_FILE))):
    snapshot_file.write_text(json.dumps(snapshot, indent=2))

def load_snapshot(snapshot_file=Path(str(settings.SNAPSHOT_FILE))):
    if snapshot_file.exists():
        return json.loads(snapshot_file.read_text())
    return []

def find_new_files(old, new):
    old_set = set(old)
    return [p for p in new if p not in old_set]

if __name__=="__main__":
    load_snapshot()