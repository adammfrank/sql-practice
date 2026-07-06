# Lesson 08 — Join Algorithms: Hash Join vs. Nested Loop

Postgres can join two row sets with a **Nested Loop**, a **Hash
Join**, or a **Merge Join**. The planner picks whichever it estimates
is cheapest — so the *same* join can execute completely differently
depending on how selective the surrounding filters are. This lesson
shows both ends of that decision using one join: `orders` ⋈
`order_items`.

## 1. Part A — an unselective join gets a Hash Join

Join `orders` to `order_items` on `order_items.order_id = orders.id`
and, for each `orders.status`, sum `quantity * price` across its line
items. There's no selective filter — every row of both tables
participates.

Run this yourself under `EXPLAIN ANALYZE` (no indexes needed). You
should see a **Hash Join**: Postgres builds a hash table from the
smaller side (`orders`) and streams the other side through it. That's
the right call when you're touching most of both tables anyway —
reading both once and building one hash table beats probing an index
a million times.

## 2. Part B — a selective join gets a Nested Loop

This is the graded query. Take the same `orders`/`order_items` join,
but filter to `orders.customer_id = 4242` and report, **for each of
that customer's orders, the order's id alongside the sum of
`quantity * price` across its line items** — one row per order, each
row carrying its `orders.id` and that order's total.

Customer 4242 has about a dozen orders out of 500,000. Instead of
"touch everything," this is "find a handful of rows, then look up
their matches" — building a hash table over a million `order_items`
rows to serve a dozen lookups would be wasteful.

## 3. What to do

1. In `indexes.sql`, add the indexes that let the two selective
   lookups run off the index instead of a full scan: finding customer
   4242's orders, and finding each of those orders' line items.
2. Write the Part B query into `solution.sql` — remember it returns
   two columns per order: the order id and that order's total.
3. Run the test.

With the indexes in place and a tiny outer side, the planner switches
to a **Nested Loop**: for each of customer 4242's ~11 orders (found
via the index), it does one indexed lookup into `order_items`. Total
work is proportional to a dozen orders plus a dozen lookups — nothing
like a full scan of either table.

## 4. Why the planner switches

A Nested Loop's cost is roughly `(rows on the outer side) x (cost to
look up one outer row's matches)`. When the outer side is tiny and the
inner lookup is a cheap index seek, that product is small — smaller
than building a hash table over a million-row table for a dozen
probes. Flip the outer side back to "all orders" (Part A) and the same
math favors Hash Join: the per-row lookup cost is unchanged, but now
you pay it hundreds of thousands of times.

**Nested Loop wins when one side is small and the other has a cheap,
indexed way to find matches. Hash Join wins when you'll touch a large
fraction of both sides regardless.** (A **Merge Join** is the third
option, useful when both inputs are already sorted on the join key.)

## 5. Run it

```bash
make test lessons/08_join_algorithms
```

## 6. The gate

- Correctness: unordered row match against `expected.sql`.
- The plan contains a `Nested Loop` and an `Index Scan`, and no
  `Seq Scan` — the planner is driving the join off the indexes, not
  scanning either table in full.
- At least an 8x speedup over the no-index baseline.

## 7. The teaching point

The "right" join algorithm isn't a property of the query text — it's
the query text *combined with* how selective the filters are and what
indexes exist. When you see a Hash Join where you expected an
index-driven Nested Loop (or vice versa), the first question isn't "is
Postgres broken" — it's "does the planner's row estimate for the outer
side match reality, and does a useful index exist for the inner
lookup."
