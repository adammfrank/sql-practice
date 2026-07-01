# Lesson 13 — GIN Indexes on JSONB Containment

`products.attributes` is a `jsonb` column — an unstructured bag of
attributes per product (`color`, `size`, `tags`, and whatever else a
future product might add). Querying it with the containment operator
`@>` ("does this jsonb value contain this other jsonb value") is a
natural way to filter: "find products where attributes contains
`color: red`." A plain B-tree index can't help with `@>` at all — it
has no idea how to sort or search "does this document contain this
sub-document." **GIN** is the index type built for exactly this.

## 1. The problem

```sql
SELECT id
FROM products
WHERE attributes @> '{"color":"red","size":"m"}';
```

A note on the predicate: the brief for this lesson suggested a
single-key containment, `attributes @> '{"color":"red"}'`. `color` is
one of 5 values in the seed data (`dojo/seed.py`), so that predicate
matches roughly 1 in 5 products — measured, 1,920 of 10,000. On top of
that, `products` itself is a small table (~2.5MB), so a full scan of
it is already cheap regardless of the `WHERE` clause. Combining both
factors, the single-key version doesn't beat a seq scan by a
convincing margin. This lesson uses a **two-key** containment instead
— `{"color":"red","size":"m"}`, requiring both attributes to match —
which is meaningfully more selective (measured: 462 of 10,000 rows,
~4.6%) while still being a genuine GIN containment query, not a
different kind of predicate.

## 2. What to do

In `indexes.sql`, build a GIN index over the whole `jsonb` column:

```sql
CREATE INDEX idx_products_attrs ON products USING gin (attributes);
```

Then write the query above into `solution.sql`.

## 3. What you should see in the plan

```
Bitmap Heap Scan
  -> Bitmap Index Scan on idx_products_attrs
```

By default, a GIN index on `jsonb` indexes every key and every value
in the document, which is what makes `@>` containment queries — for
any key, not just ones you anticipated — usable by the index. (There's
a second GIN operator class, `jsonb_path_ops`, that trades that
generality for a smaller, faster index specifically tuned for `@>`
queries — see step 5.)

## 4. A note on the speedup you'll actually see

Don't expect a dramatic multiple here. `products` has only 10,000
rows and occupies roughly 2.5MB (~318 pages) — small enough that
reading the whole table sequentially is already fast, the same
small-table effect that limited lesson 09's speedup. Measured
repeatedly on the seeded template, the baseline (seq scan) for the
two-key query runs **1.5-1.9ms**, and the GIN-indexed version runs
**~0.4-0.6ms** — a real but modest **2.9x-4.1x** speedup (minimum
observed 2.87x across 5 trials). This lesson's gate uses `ratio=2`,
set below that floor.

There's a subtlety worth knowing about here: this test harness treats
any baseline measurement under 2ms (`floor_ms=2.0`) as "too fast and
too noisy to gate on" and skips the ratio check entirely rather than
asserting on it (see `dojo/grader.py`) — and on `products`, the
baseline sits right around that line, sometimes above it and
sometimes below depending on system load. That's why this lesson's
**primary** gate is the plan check — `uses_index="idx_products_attrs"`
and `must_have=["Bitmap Index Scan"]` — which unlike the timing
check always applies and is what actually proves you built and used
the GIN index. The speed ratio is a secondary, best-effort check on
top of that.

## 5. Run it

```bash
.venv/Scripts/pytest lessons/13_gin_jsonb -v
```

## 6. The gate

Correctness, then the plan must use `idx_products_attrs` and contain a
`Bitmap Index Scan`, then at least a 2x speedup over the no-index
baseline when that check applies (see step 4).

## 7. The teaching point

GIN over `jsonb` is the standard way to make containment queries
against semi-structured data indexable, without having to know your
full schema of attributes in advance or normalize every possible
attribute into its own column. If your application's real workload
leans hard on one or two specific keys (e.g. always filtering by
`color`), a **GIN index with the `jsonb_path_ops` operator class** —
`CREATE INDEX ... USING gin (attributes jsonb_path_ops)` — builds a
smaller, faster index tuned specifically for `@>` queries, at the cost
of not supporting the `?`/`?&`/`?|` "does this key exist" operators
that the default operator class supports. And if you find yourself
querying the *same* one or two keys constantly, an **expression
index** on just that key (lesson 11's technique, e.g. `CREATE INDEX ON
products ((attributes->>'color'))`) is often a better fit than GIN —
smaller, and a plain B-tree lookup instead of an inverted index scan.
GIN on the whole document is the right default when you don't know in
advance which keys you'll be querying by.
