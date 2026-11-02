import sys
import os

# Root directory ko Python path mein add karo
root = os.path.dirname(os.path.abspath(__file__))
if root not in sys.path:
    sys.path.insert(0, root)

