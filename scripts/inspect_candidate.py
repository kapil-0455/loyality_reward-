
import inspect
from backend.app.decision import models

print("Classes in decision/models.py:\n")

for name, cls in inspect.getmembers(models, inspect.isclass):
    if cls.__module__ == models.__name__:
        print("\nClass:", name)
        print("Constructor:", inspect.signature(cls))
        print("Annotations:", getattr(cls, "__annotations__", {}))
