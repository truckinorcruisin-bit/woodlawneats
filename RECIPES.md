# Adding recipes

One JSON file per recipe in `data/recipes/`. Filename should match the `id`.
Push to `main` and the **Build recipe index** workflow rebuilds `data/index.json`,
which is the only file the front end actually fetches.

## Before you paste in a cookbook recipe

This repo is public. Ingredient lists are largely facts and fine to record, but the
written method is the copyrightable part — rewrite each step in your own words rather
than copying. That's required by the design anyway, because steps have to be templated
for the swap engine to work. Put the book in `source` for attribution.

## Recipe schema

```json
{
  "id": "fish-tacos",
  "title": "{Protein} tacos",
  "source": "Book Name, p. 142 (adapted)",

  "role": "weeknight",        // "sunday" = the big cook | "weeknight" = assembly
  "effort": "assemble",       // "cook" | "assemble"
  "activeMin": 15,
  "serves": 4,

  "cuisines": ["texmex", "mexican"],
  "seasons": ["spring", "summer"],

  "slots": {
    "protein": { "default": "whitefish", "accepts": ["whitefish","chicken","shrimp","tofu"] },
    "starch":  { "default": "tortilla",  "accepts": ["tortilla","rice"] }
  },

  "needs": ["salsa-verde", "slaw"],

  "ingredients": [
    { "slot": "protein", "mult": 1.2 },
    { "slot": "starch", "qty": 12, "unit": "ea" },
    { "item": "avocados", "qty": 2, "unit": "ea", "cat": "Produce" }
  ],

  "lanes": [ { "lane": "grill", "label": "{Protein}", "s": 75, "d": 25 } ],

  "steps": ["{STARCH_REHEAT}", "{PROTEIN_REHEAT}", "Build: ..."],
  "kid": "Deconstruct it.",
  "note": "Pure assembly."
}
```

### The two fields that make the engine work

**`slots`** is what lets the site turn your fish tacos into chicken tacos. Every value
in `accepts` must exist in `data/swaps.json`. When a recipe joins a week, the engine
picks whichever accepted option is already being bought for another meal — that's the
grocery-efficiency behaviour.

**`steps`** must use tokens instead of naming the protein, or swapping produces
nonsense instructions. Available tokens:

| Token | Expands to |
|---|---|
| `{Protein}` / `{protein}` | the name, capitalised or not |
| `{PROTEIN_PREP}` | prep note for that protein |
| `{PROTEIN_COOK}` | full cooking method and temps |
| `{PROTEIN_REHEAT}` | how to bring it back on a weeknight |
| `{Starch}` / `{starch}` | the name |
| `{STARCH_COOK}` | Sunday cooking method |
| `{STARCH_REHEAT}` | weeknight reheat method |

Write the rest of the step around the token. Anything protein-specific that isn't in a
token will read wrong after a swap.

### Fields

| Field | Notes |
|---|---|
| `role` | `sunday` recipes are anchors — one per week. `weeknight` ones fill the rest. |
| `effort` | Aim for `cook` on Sunday only. Weeknights should be `assemble`. |
| `needs` | Component ids from `data/components/`. These get made Sunday and shared across meals. |
| `ingredients[].slot` | Omit `item`; the engine substitutes. `mult` scales protein weight (1.0 = one meal's worth for 4). |
| `ingredients[].cat` | `Produce`, `Protein`, `Fridge`, `Pantry`, `Spice`. Drives grocery grouping. |
| `lanes` | Sunday anchors only. Drives the cook-flow chart. `s` and `d` are minutes from session start. |

## Component schema

Sauces, broths, slaws, roasted trays — anything made Sunday and used across multiple
nights. `data/components/<id>.json`:

```json
{
  "id": "salsa-verde",
  "name": "Roasted salsa verde",
  "type": "component",
  "keeps": "7 days fridge",
  "lane": "oven",
  "min": 30,
  "why": "Jarred salsa verde is always onion-based.",
  "ingredients": [ { "item": "tomatillos", "qty": 2, "unit": "lb", "cat": "Produce" } ],
  "steps": ["Halve the tomatillos...", "Roast at 450°F..."]
}
```

## Validation

`scripts/build_index.py` fails the build if any ingredient contains an allium, red meat,
or gluten term, if a recipe references a component that doesn't exist, or if a slot
accepts a value missing from `swaps.json`. Step text gets a warning rather than an error,
since explanatory mentions ("in place of onion") are legitimate.

Run it locally with `python scripts/build_index.py` if you have a checkout.

## Adding a new protein or starch

Edit `data/swaps.json`. Each protein needs `label`, `buy`, `cat`, `lbPerServing`,
`cook`, `reheat`, and `prep`. Once it's there, add its key to the `accepts` list of
every recipe it works in.
