# Woodlawn Eats

Static meal-prep site. Rolls a weekly menu — one Sunday cook plus two weeknight
assemblies — and generates a merged grocery list.

## Repo layout

```
index.html            the site (also carries a fallback snapshot of the data)
woodlawn-data.json    every recipe, component, swap, and category. Edit this.
README.md
```

That's it. No folders, no build step, no workflow. GitHub Pages serves it as-is.

`index.html` loads `woodlawn-data.json` at runtime, so **adding a recipe means
editing one file and committing**. The site picks it up on the next page load.

`index.html` also has a snapshot of the data baked into it as a fallback, so if
`woodlawn-data.json` is ever missing the site still works rather than going
blank. The live file always wins when present.

---

## Adding a recipe

Append an object to the `recipes` array in `woodlawn-data.json`.

```json
{
  "id": "fish-tacos",
  "title": "{Protein} tacos",
  "source": "Book Name, p. 142 (adapted)",
  "role": "weeknight",
  "effort": "assemble",
  "activeMin": 15,
  "cuisines": ["texmex"],
  "seasons": ["spring", "summer"],
  "slots": {
    "protein": { "default": "whitefish", "accepts": ["whitefish","chicken","shrimp","tofu"] },
    "starch":  { "default": "tortilla",  "accepts": ["tortilla","rice"] }
  },
  "needs": ["salsa-verde", "slaw"],
  "ingredients": [
    "@protein 1.2",
    "@starch 12",
    "2 avocados",
    "1 bunch cilantro",
    "6 oz cotija"
  ],
  "steps": ["{STARCH_REHEAT}", "{PROTEIN_REHEAT}", "Build: ..."],
  "kid": "Deconstruct it.",
  "accommodate": "Reserve a portion before the garlic goes in."
}
```

### Compact ingredient syntax

Ingredients are plain strings. Category is inferred from the `categories`
lookup at the top of the data file.

| Write | Means |
|---|---|
| `"2 avocados"` | 2 avocados, unit-less count |
| `"1 bunch cilantro"` | qty 1, unit `bunch` |
| `"1.5 lb carrots"` | qty 1.5, unit `lb` |
| `"olive oil"` | no quantity, just add it to the list |
| `"@protein 1.2"` | fills the protein slot, 1.2× a normal portion |
| `"@starch 3 cup"` | fills the starch slot, 3 cups |
| `"2 lb carrots \| Fridge"` | force the category with a pipe |

Recognised units: `lb oz cup cups tsp Tbsp can cans bunch head pint qt inch bag
stick sticks slice clove`. Anything else is treated as part of the item name.

Unknown ingredients default to **Pantry**. To make one stick, either add a pipe
override or add the word to the `categories` map — `"radicchio": "Produce"` —
and every future recipe using it inherits that.

The old verbose object form (`{"item":"avocados","qty":2,"unit":"ea","cat":"Produce"}`)
still parses, so you can mix the two if a line ever needs it.

### Templated steps

Steps must use tokens rather than naming the protein, or swapping produces
nonsense. `{Protein}` / `{protein}`, `{PROTEIN_PREP}`, `{PROTEIN_COOK}`,
`{PROTEIN_REHEAT}`, `{Starch}` / `{starch}`, `{STARCH_COOK}`, `{STARCH_REHEAT}`.

Write the rest of the sentence around the token. "Flake the fish gently" reads
wrong once the slot resolves to chicken; `{PROTEIN_REHEAT}` doesn't.

### Components

Sauces, broths, roasted trays — anything made Sunday and shared across nights.
Add to the `components` array; reference by `id` in a recipe's `needs`. Shared
components are deduped in the grocery list automatically.

---

## Diet model

The family eats normally. One household member needs no red meat, no gluten,
and no alliums, so anything using those carries a documented workaround:

- **`accommodateNote`** on a protein or starch in `swaps` — written once, applies
  everywhere that ingredient is used.
- **`accommodate`** on a recipe or component — for alliums and other per-dish
  swaps ("reserve 2 cups before the garlic goes in").

Both surface automatically as a **Spouse plate** note on menu cards and prep tasks.

---

## Regenerating the fallback snapshot

Only needed if you want `index.html`'s built-in copy refreshed. The site works
without doing this — the live JSON takes priority.

```
python scripts/build_snapshot.py
```

Copyright note: ingredient lists are fine to record, but rewrite cookbook
methods in your own words and keep the book in `source`. The templated-step
requirement means you'd be rewriting them anyway.
