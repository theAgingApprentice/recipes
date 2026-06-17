import sys
import os

# Allow imports from app/ directory when running pytest from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))
