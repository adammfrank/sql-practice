# Lesson 08 — Join Algorithms: Hash Join vs. Nested Loop

Postgres has three ways to join two row sets: **Nested Loop**, **Hash
Join**, and **Merge Join**. The planner picks whichever it estimates
will be cheapest for the specific query at hand — the same join
written the same way can execute completely differently depending on
how selective the surrounding filters are. This lesson walks through
both ends of that decision using one join: `orders` ⋈ `order_items`.

## 1. Part A — an unselective join gets a Hash Join

Suppose you want total item value per order status, across the whole
table: join `orders` to `order_items` on `order_items.order_id =
orders.id`, and for each `orders.status` sum `quantity * price` across
its line items.

There's no selective filter here — every row of both tables
participates. Run that query yourself under `EXPLAIN ANALYZE` (no
indexes needed) and look at the plan.

You should see a **Hash Join**: Postgres builds an in-memory hash
table from the smaller side (`orders`, keyed on `id`) and then
streams the other side (`order_items`) through it, probing the hash
table once per row. This is the right call when you're going to touch
most or all of both tables anyway — a Hash Join's cost is roughly
"read both tables once, plus build one hash table," which beats
probing an index a million times over.

`work_mem` controls how big that in-memory hash table is allowed to
get before Postgres spills batches of it to disk. With the default
`work_mem` (4MB) and this table size, the hash table for `orders`
fits comfortably in memory, so the Hash Join stays single-pass. If
`work_mem` were too small for the hash table, you'd see the same
Hash Join node but with multiple batches — still correct, just slower.

## 2. Part B — a selective join gets a Nested Loop

Now narrow the query to one customer's orders and their line items —
the kind of query a customer-facing "order history" page runs
constantly: the same `orders`/`order_items` join, but filtered to
`orders.customer_id = 4242` and grouped by `orders.id`, summing
`quantity * price` per order.

Customer 4242 has about a dozen orders out of 500,000. This is a
completely different shape of problem: instead of "touch everything,"
it's "find a handful of rows, then look up their matches." Building a
whole hash table over a million `order_items` rows to serve a dozen
lookups is wasteful.

## 3. What to do

In `indexes.sql`, add the indexes that let this selective join run off
index lookups instead of full scans. Two lookups need to get cheap:

- finding customer 4242's orders without scanning all of `orders`, and
- finding each of those orders' line items without scanning all of
  `order_items`.

Then write the Part B query above into `solution.sql` and run the test.

With both indexes in place and a selective outer predicate, the
planner switches to a **Nested Loop**: for each of customer 4242's
~11 orders (found via the index on `orders`), it does one indexed
lookup into `order_items` by `order_id`. Total work is proportional to
"a dozen orders, plus a dozen indexed lookups" — nothing close to a
full scan of either table.

## 4. Why the planner switches

The planner estimates the cost of every join strategy it considers and
picks the cheapest. A Nested Loop's cost is roughly `(rows on the
outer side) x (cost to look up matches for one outer row on the inner
side)`. When the outer side is tiny (a dozen orders) and the inner
lookup is cheap (an index seek, not a scan), that product is small —
smaller than building an entire hash table over a million-row table
just to serve a dozen probes. Flip the outer side back to "all
orders," as in Part A, and the same math favors Hash Join: the
per-row lookup cost stays the same, but now you're paying it hundreds
of thousands of times, and building one hash table up front is
cheaper than that many index probes.

The general pattern: **Nested Loop wins when one side is small and the
other side has a cheap, indexed way to find matches. Hash Join wins
when you're going to touch a large fraction of both sides regardless.**
A **Merge Join** (not forced by either query here) is the planner's
third option, useful when both inputs are already sorted on the join
key (or cheap to sort) — it walks both sorted streams in lockstep.

## 5. Run it

```bash
.venv/Scripts/pytest lessons/08_join_algorithms -v
```

## 6. The gate

The graded query is the **Part B** selective variant. The gate
checks:

- Correctness (unordered row match against `expected.sql`).
- The plan contains a `Nested Loop` and an `Index Scan`, and contains
  no `Seq Scan` — confirming the planner is driving the join off the
  indexes rather than scanning either table in full.
- At least an 8x speedup over the no-index baseline.

Part A's Hash Join is this README's teaching example — worth running
yourself to see the contrast — but the lesson's one gated
`solution.sql` is Part B.

## 7. The teaching point

The "right" join algorithm isn't a property of the query text, it's a
property of the query text *combined with* how selective the
surrounding filters are and what indexes exist. The same join clause
can and should execute completely differently depending on whether
you're touching 12 rows or 12 million. When you see a Hash Join where
you expected an index-driven Nested Loop (or vice versa), the first
question isn't "is Postgres broken" — it's "does the planner's row
estimate for the outer side match reality, and does a useful index
exist for the inner side's lookup."
