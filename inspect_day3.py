
import inspect

from backend.app.decision import baseline_ranker, constraints
from backend.app.domain import budget, eligibility, inventory
from backend.app.services import reward_recommendation

modules = [
    eligibility,
    inventory,
    budget,
    constraints,
    baseline_ranker,
    reward_recommendation
]

for module in modules:
    print(f"\n--- {module.__name__} ---")

    for name, function in inspect.getmembers(
        module,
        inspect.isfunction
    ):
        if not name.startswith("_"):
            print(name, inspect.signature(function))
