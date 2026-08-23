# Adding recipes

One JSON file per recipe in `data/recipes/`. Filename should match the `id`.
Push to `main` and the **Build recipe index** workflow rebuilds `data/index.json`,
which is the only file the front end actually fetches.

## Diet model: household default + spouse accommodation

The family eats normally — red meat, gluten, and alliums are all fine by default.
Sean's spouse needs an accommodation for all three. Rather than banning those
ingredients from the whole site, every recipe or component that uses one carries
a documented one-line workaround for her plate specifically.

**Two places this lives:**

1. **`accommodateNote` on a protein or starch in `swaps.json`.** Anything tagged
   `"red meat"` or with `"containsGluten": true` needs this. It's written once per
   ingredient and applies everywhere that ingredient is used — e.g. every recipe
   that resolves to `beef` automatically shows the same note about searing chicken
   alongside.
2. **`accommodate` on the recipe or component itself.** For alliums (not a slot,
   so not swappable) or any other literal ingredient that needs a per-dish
   workaround — e.g. "reserve 2 cups of sauce before the garlic goes in."

The build fails if a flagged ingredient shows up without one of these two. It
does **not** fail if a recipe simply contains onion, garlic, steak, or regular
pasta — that's the normal case now.

```json
{
  "id": "marinara",
  "ingredients": [
    { "item": "yellow onion, diced", "qty": 1, "unit": "ea", "cat": "Produce" },
    { "item": "garlic cloves, minced", "qty": 3, "unit": "ea", "cat": "Produce" }
  ],
  "accommodate": "Set aside 2 cups of crushed tomatoes before the onion and garlic go in. Simmer that portion separately with a splash of vinegar for the accommodated plate."
}
```

The front end surfaces these automatically as a "Spouse plate" note on every menu
card and Sunday prep task — no need to duplicate the text anywhere else.

---


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

`scripts/build_index.py` requires an `accommodateNote` on any `swaps.json` entry
tagged `red meat` or `containsGluten`, and an `accommodate` field on any
recipe/component containing a literal allium, gluten, or red-meat ingredient.
It does not block the ingredients themselves. Step text gets a warning rather
than an error if it mentions one of these terms — that's just a nudge to check
the accommodate note actually covers what the step describes.

Run it locally with `python scripts/build_index.py` if you have a checkout.

## Adding a new protein or starch

Edit `data/swaps.json`. Each protein needs `label`, `buy`, `cat`, `lbPerServing`,
`cook`, `reheat`, and `prep`. Once it's there, add its key to the `accepts` list of
every recipe it works in.
