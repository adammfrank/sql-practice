# Lesson 13 — GIN Indexes on JSONB Containment

`products.attributes` is a `jsonb` column — an unstructured bag of
attributes per product. The containment operator `@>` ("does this jsonb
contain that jsonb") is the natural way to filter it, but a B-tree can't
help `@>` at all. **GIN** is built for exactly this.

## 1. The problem

Return the `id`s of `products` whose `attributes` contains both
`"color": "red"` and `"size": "m"` — i.e.
`attributes @> '{"color":"red","size":"m"}'`.

Two keys, not one: `color` alone (5 values) matches ~1 in 5 rows, too
weak to beat a seq scan convincingly on this small table. The two-key
containment is ~4.6% selective (462 of 10,000) while still being a
genuine GIN containment query.

## 2. What to do

- In `indexes.sql`, build a **GIN index** (`USING gin (...)`) over the
  whole `attributes` column — GIN is what makes `@>` indexable.
- Write the query above into `solution.sql`, returning `id`.

## 3. What you should see

```
Bitmap Heap Scan
  -> Bitmap Index Scan on <your GIN index>
```

A default GIN index on `jsonb` indexes every key and value, so `@>`
containment works for any key. (A second operator class,
`jsonb_path_ops`, is smaller and faster for `@>` specifically — see the
teaching point.)

## 4. A note on the speedup

`products` is tiny (~10,000 rows, ~2.5MB), so a full scan is already
fast: baseline ~1.5–1.9ms, indexed ~0.4–0.6ms — a real but modest
**2.9–4.1x**. The gate uses `ratio=2`, and because the baseline can dip
under the harness's `floor_ms=2.0` (where the ratio check is skipped),
the **plan check** (`Bitmap Index Scan`) is the primary gate — it's what
proves you built and used the GIN index.

## 5. Run it

```bash
make test lessons/13_gin_jsonb
```

## 6. The gate

Correctness, then the plan must contain a `Bitmap Index Scan`, then at
least a 2x speedup over the no-index baseline when that check applies
(see step 4).

## 7. The teaching point

GIN over `jsonb` makes containment queries against semi-structured data
indexable without knowing the schema in advance. If your workload leans
on one or two specific keys, two smaller alternatives beat a whole-doc
GIN: a `jsonb_path_ops` GIN index (smaller and faster for `@>`, but no
key-existence `?`/`?&`/`?|` operators), or an **expression index** on
just that key (lesson 11's technique — indexing `attributes->>'color'`).
Whole-document GIN is the right default when you don't know in advance
which keys you'll query.
