"""Reconcile Blueprint RUA marks with the question-mark denominations."""

from copy import deepcopy
from functools import lru_cache
from heapq import heappop, heappush
from math import gcd


COMPONENTS = ("R", "U", "A")


def _pattern_inventory(blueprint):
    inventory = {}
    pattern = blueprint.get("question_pattern", {})
    if not isinstance(pattern, dict) or not pattern:
        raise ValueError("Blueprint question_pattern must be a non-empty object")
    for section, details in pattern.items():
        if not isinstance(details, dict):
            raise ValueError(f"Question pattern section {section!r} must be an object")
        count = details.get("questions_to_generate", details.get("number_of_questions", 0))
        marks = details.get("marks_per_question", 0)
        if not isinstance(count, int) or count < 0 or not isinstance(marks, int) or marks <= 0:
            raise ValueError(f"Invalid question count or marks in section {section!r}")
        inventory[marks] = inventory.get(marks, 0) + count
    return tuple(sorted(inventory.items()))


def _can_compose_cells(cells, inventory):
    """Can each RUA cell be made from the exact global denomination inventory?"""
    denominations = tuple(mark for mark, _ in inventory)
    capacities = tuple(count for _, count in inventory)
    @lru_cache(None)
    def ways(amount, index, remaining):
        if index == len(denominations):
            return ((),) if amount == 0 else ()
        mark = denominations[index]
        result = []
        for n in range(min(remaining[index], amount // mark) + 1):
            for tail in ways(amount - n * mark, index + 1, remaining):
                result.append((n,) + tail)
        return tuple(result)

    states = {capacities}
    for amount in cells:
        next_states = set()
        for remaining in states:
            for used in ways(amount, 0, remaining):
                left = tuple(a - b for a, b in zip(remaining, used))
                next_states.add(left)
        if not next_states:
            return False
        states = next_states
    return tuple(0 for _ in capacities) in states


def _compatible(blueprint, rua):
    inventory = _pattern_inventory(blueprint)
    cells = sorted(
        (rua[unit][part] for unit in rua for part in COMPONENTS),
        reverse=True,
    )
    return _can_compose_cells(cells, inventory)


def _unit_candidate_score(vals, original, total):
    """Score unit-local deviation and balance, with deterministic tie breaks.

    Absolute deviation is the primary objective. Squared distance from an
    equal R/U/A split is secondary; it discourages concentrated targets only
    when candidates require comparable redistribution. The final tuple keeps
    ties stable without depending on mapping or hash iteration order.
    """
    deviation = sum(abs(new - old) for new, old in zip(vals, original))
    balance = sum((3 * value - total) ** 2 for value in vals)
    spread = max(vals) - min(vals)
    return deviation, balance, spread, tuple(vals)


def _unit_candidates(details, step):
    total = details.get("Total", sum(details.get(c, 0) for c in COMPONENTS))
    if not isinstance(total, int) or total < 0:
        raise ValueError("Each RUA unit Total must be a non-negative integer")
    original = tuple(details.get(c, 0) for c in COMPONENTS)
    for value in original + (total,):
        if not isinstance(value, int) or value < 0:
            raise ValueError("RUA components and totals must be non-negative integers")
    candidates = []
    for r in range(0, total + 1, step):
        for u in range(0, total - r + 1, step):
            a = total - r - u
            if a % step:
                continue
            vals = (r, u, a)
            candidates.append((_unit_candidate_score(vals, original, total), vals))
    return sorted(candidates, key=lambda item: item[0])


def make_rua_pattern_compatible(blueprint):
    """Return a copied Blueprint whose complete RUA table fits its question pattern.

    Unit totals and every field outside requirements.rua_allocation are preserved.
    The optimizer ranks complete compatible allocations globally. It minimizes
    total deviation first, then favors more even unit-level R/U/A distributions.
    """
    result = deepcopy(blueprint)
    requirements = result.get("requirements")
    if not isinstance(requirements, dict) or not isinstance(requirements.get("rua_allocation"), dict):
        raise ValueError("Blueprint requirements.rua_allocation must be an object")
    rua = requirements["rua_allocation"]
    _pattern_inventory(result)
    if _compatible(result, rua):
        return result

    inventory = _pattern_inventory(result)
    granularity = 0
    for denomination, _ in inventory:
        granularity = gcd(granularity, denomination)
    granularity = max(1, granularity)
    units = sorted(rua)
    options = [_unit_candidates(rua[unit], granularity) for unit in units]
    # Best-first search over the Cartesian product without materializing it.
    # Additive lexicographic scores make the first compatible result globally
    # optimal under deviation, balance, spread, and deterministic tie breaks.
    start = tuple(0 for _ in units)
    def combination_cost(indices):
        scores = [options[i][index][0] for i, index in enumerate(indices)]
        return tuple(sum(score[component] for score in scores) for component in range(3))
    frontier = [(combination_cost(start), start)]
    seen = {start}
    best = None
    while frontier:
        score, indices = heappop(frontier)
        candidate = deepcopy(rua)
        for i, unit in enumerate(units):
            vals = options[i][indices[i]][1]
            for key, value in zip(COMPONENTS, vals):
                candidate[unit][key] = value
            if "Total" in candidate[unit]:
                candidate[unit]["Total"] = sum(vals)
        if _compatible(result, candidate):
            best = candidate
            break
        for i in range(len(units)):
            if indices[i] + 1 >= len(options[i]):
                continue
            neighbor = indices[:i] + (indices[i] + 1,) + indices[i + 1:]
            if neighbor not in seen:
                seen.add(neighbor)
                heappush(frontier, (combination_cost(neighbor), neighbor))
    if best is None:
        raise ValueError("No RUA redistribution can satisfy the Blueprint question pattern")
    requirements["rua_allocation"] = best
    return result
