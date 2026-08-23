#!/usr/bin/env python3
"""
Merges data/recipes/*.json + data/components/*.json + data/swaps.json
into a single data/index.json for the front end to fetch.

Also validates every ingredient against the household diet rules and
fails the build if anything violates them.
"""
import json, os, sys, glob, re, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")

# --- diet rules -------------------------------------------------------------
ALLIUM = ["onion", "garlic", "shallot", "leek", "scallion", "chive", "ramp",
          "asafoetida", "sofrito"]
RED_MEAT = ["beef", "pork", "lamb", "veal", "bacon", "prosciutto", "chorizo",
            "pancetta", "steak", "brisket", "sausage", "ham "]
GLUTEN = ["soy sauce", "panko", "barley", "rye", "semolina", "farro", "couscous",
          "seitan", "wheat", "breadcrumb", "flour tortilla"]
# phrases that make an otherwise-flagged term acceptable
ALLOW = ["gf ", "gluten-free", "gluten free", "certified gf", "tamari"]
# explanatory mentions ("in place of onion") are not violations
NEGATED = ["place of", "instead of", "without", "no onion", "-free", " free",
           "normally", "rather than", "not ", "skip", "unlike", "would"]


def _hit(word, t):
    return re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", t) is not None


def violations(text):
    t = text.lower()
    if any(a in t for a in ALLOW):
        return []
    out = []
    for kind, words in (("allium", ALLIUM), ("red meat", RED_MEAT), ("gluten", GLUTEN)):
        for w in words:
            if not _hit(w.strip(), t):
                continue
            # look at the clause around the hit for a negating phrase
            i = t.find(w.strip())
            window = t[max(0, i - 60):i + 60]
            if any(n in window for n in NEGATED):
                continue
            out.append((kind, w.strip()))
    return out


def load(pattern):
    items = []
    for p in sorted(glob.glob(pattern)):
        try:
            with open(p) as f:
                items.append(json.load(f))
        except json.JSONDecodeError as e:
            print("PARSE ERROR in %s: %s" % (p, e))
            sys.exit(1)
    return items


def main():
    recipes = load(os.path.join(D, "recipes", "*.json"))
    components = load(os.path.join(D, "components", "*.json"))
    with open(os.path.join(D, "swaps.json")) as f:
        swaps = json.load(f)

    errors, warnings = [], []
    comp_ids = {c["id"] for c in components}
    seen = set()

    for r in recipes + components:
        rid = r.get("id")
        if not rid:
            errors.append("A file is missing an 'id' field")
            continue
        if rid in seen:
            errors.append("Duplicate id: %s" % rid)
        seen.add(rid)

        for ing in r.get("ingredients", []):
            name = ing.get("item", "")
            if not name:
                continue  # slot-driven ingredient, resolved at runtime
            for kind, word in violations(name):
                errors.append("%s: ingredient '%s' contains %s (%s)"
                              % (rid, name, kind, word))

        for step in r.get("steps", []):
            for kind, word in violations(step):
                warnings.append("%s: step text mentions %s (%s)" % (rid, kind, word))

        for need in r.get("needs", []):
            if need not in comp_ids:
                errors.append("%s: needs unknown component '%s'" % (rid, need))

        for slot, cfg in r.get("slots", {}).items():
            pool = swaps.get("proteins" if slot == "protein" else "starches", {})
            for opt in cfg.get("accepts", []):
                if opt not in pool:
                    errors.append("%s: slot %s accepts unknown '%s'" % (rid, slot, opt))
            if cfg.get("default") not in cfg.get("accepts", []):
                errors.append("%s: slot %s default not in accepts" % (rid, slot))

    for w in warnings:
        print("WARN  " + w)
    if errors:
        print("\nBUILD FAILED — %d error(s):" % len(errors))
        for e in errors:
            print("  " + e)
        sys.exit(1)

    index = {
        "builtAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "counts": {"recipes": len(recipes), "components": len(components)},
        "swaps": swaps,
        "components": components,
        "recipes": recipes,
    }
    out = os.path.join(D, "index.json")
    with open(out, "w") as f:
        json.dump(index, f, separators=(",", ":"), ensure_ascii=False)

    print("OK  %d recipes, %d components, %d warnings -> data/index.json (%.1f KB)"
          % (len(recipes), len(components), len(warnings),
             os.path.getsize(out) / 1024.0))


if __name__ == "__main__":
    main()
