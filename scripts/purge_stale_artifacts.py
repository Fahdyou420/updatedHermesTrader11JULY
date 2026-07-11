import shutil, os, subprocess, sys
from pathlib import Path

root = Path('C:/Users/user/Desktop/hermes_claude')
patterns = {
    '.venv': root/'.venv',
    'venv': root/'venv',
    'dist': root/'dist',
    'build': root/'build',
    'node_modules': root/'node_modules',
    'HermesLogs': root/'HermesLogs',
}
for name, path in patterns.items():
    if path.exists():
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            print('removed', name)
        else:
            path.unlink(missing_ok=True)
            print('removed file', name)
# loose caches
for p in root.rglob('__pycache__'):
    shutil.rmtree(p, ignore_errors=True)
print('purge complete')
