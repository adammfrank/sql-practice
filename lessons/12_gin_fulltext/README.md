# Lesson 12 — Full-Text Search with GIN

`reviews.body` is a 1,000,000-row free-text column. `body ILIKE '%dog%'`
works but scans and re-tokenizes every row, and a leading-wildcard
pattern can't use a B-tree. Postgres's **full-text search** tokenizes
text into normalized lexemes (a `tsvector`), queried with a `tsquery`
via the `@@` operator — and a **GIN index** over those lexemes means a
search never re-tokenizes the whole table.

## 1. The problem

Return the `id`s of `reviews` where
`to_tsvector('english', body) @@ plainto_tsquery('english', 'dog')`.

The search term is `'dog'` because the seed data fills `body` with Faker
lorem-ipsum, not real prose — realistic phrases match zero rows. `'dog'`
was picked by sampling the corpus to land at a believable "moderately
common" frequency: 25,520 of 1,000,000 rows (~2.55%).

## 2. What to do

- In `indexes.sql`, build a **GIN index** (`USING gin (...)`) over the
  `tsvector` expression. It must be **exactly**
  `to_tsvector('english', body)`, or the planner won't match it to the
  query.
- Write the query above into `solution.sql`, returning `id`.

## 3. What you should see

```
Bitmap Heap Scan
  -> Bitmap Index Scan on <your GIN index>
```

A GIN (Generalized Inverted iNdex) stores, per lexeme, the list of rows
containing it — the inverse of "per row, which words." Looking up `'dog'`
is one lookup instead of tokenizing a million rows. GIN scans surface as
a `Bitmap Index Scan` feeding a `Bitmap Heap Scan`.

## 4. Why the speedup is huge

Without the index, Postgres computes `to_tsvector(...)` from scratch for
all 1,000,000 rows — real CPU per row, measured at **6.6–8.8s**. With the
GIN index, ~**40–48ms** (150–200x faster). The gate uses `ratio=10`,
well below what's achievable.

(`expected.sql` uses the same `tsvector`/`tsquery` predicate, not an
`ILIKE` baseline: full-text stemming means the two don't always return
identical rows, so matching predicates keeps the correctness check
honest.)

## 5. Run it

```bash
make test lessons/12_gin_fulltext
```

## 6. The gate

Correctness, then the plan must contain a `Bitmap Index Scan` (how GIN
usage surfaces in `EXPLAIN`), then at least a 10x speedup over the
no-index baseline.

## 7. The teaching point

GIN is for **multi-valued** column data: a `tsvector` is a set of lexemes
per row, and GIN answers "find rows whose set contains X" — the same
reason it fits array and JSONB containment (lesson 13). Whenever "search
text for this word" is a real query pattern over more than a trivial
amount of text, `tsvector` + GIN is the standard answer.
