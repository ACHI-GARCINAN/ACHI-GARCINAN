import time
import sys

print('Starting smoke test')

try:
    from db import load_masechet_list, get_base_dir
    print('Imported db')
except Exception as e:
    print('Failed to import db:', e)
    sys.exit(2)

try:
    from PyQt6.QtWidgets import QApplication
    from main_window import MainWindow
    print('Imported PyQt6 and MainWindow')
except Exception as e:
    print('Failed to import GUI modules:', e)
    sys.exit(3)

folder = get_base_dir()
print('Using base folder:', folder)

try:
    t0 = time.time()
    ms = load_masechet_list(folder)
    print(f'load_masechet_list: {time.time()-t0:.2f}s (found {len(ms)} masechtot)')
except Exception as e:
    print('Error loading masechtot:', e)
    sys.exit(4)

# Create QApplication but don't exec() to avoid blocking UI tests
app = QApplication([])
try:
    t0 = time.time()
    w = MainWindow(ms)
    t = time.time()-t0
    print(f'MainWindow init: {t:.2f}s')
except Exception as e:
    print('MainWindow init failed:', e)
    sys.exit(5)

print('Smoke test finished successfully')
sys.exit(0)
