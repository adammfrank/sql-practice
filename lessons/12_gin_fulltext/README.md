# Lesson 12 — Full-Text Search with GIN

`reviews.body` is a free-text column with 1,000,000 rows. Finding
reviews that mention a word is a classic search problem: `body ILIKE
'%dog%'` "works," but it's a full scan of every row's text, with no
index able to help a leading-wildcard pattern. Postgres's built-in
**full-text search** solves this properly: it tokenizes text into
normalized lexemes (a `tsvector`), lets you query with a `tsquery`,
and — critically for this lesson — lets you build a **GIN index** over
those tokens so a search doesn't have to re-tokenize the whole table
every time.

## 1. The problem

Return the `id`s of `reviews` whose `body`, tokenized with
`to_tsvector('english', body)`, matches the full-text query
`plainto_tsquery('english', 'dog')` — joined by the `@@` match operator.

A note on the search term: this course's seed data (`dojo/seed.py`)
fills `reviews.body` with `Faker`-generated Latin lorem-ipsum
paragraphs, not real product-review prose — so a realistic-sounding
phrase like "fast delivery" matches **zero** rows in this corpus, and
would make a useless lesson. The word `'dog'` was chosen by sampling
the actual seeded text (`ts_stat()` over a table sample, then
confirmed against the full table) specifically because it lands at a
believable "moderately common search term" frequency: **25,520 of
1,000,000 reviews (~2.55%)** contain it. Common enough that a naive
scan does real, visible work; rare enough that an index is a dramatic
win. In a real reviews table this predicate would be searching actual
review text for something a customer typed in a search box — the
mechanism taught here is identical regardless of what the underlying
text says.

You could also write the naive version of this search as `body ILIKE
'%dog%'`. It would find (almost) the same rows here, but it's worth
understanding why it's a dead end for indexing: `ILIKE` with a
leading `%` can't use a B-tree at all (nothing to sort by), and a
plain GIN trigram index for `ILIKE` is a different tool (`pg_trgm`,
not covered in this lesson). Full-text search's `tsvector`/`tsquery`
machinery is built specifically to be indexable, is language-aware
(handles stemming, stop words), and is the standard tool for this job
in Postgres.

## 2. What to do

In `indexes.sql`, build a **GIN index** over the `tsvector` expression
this query searches (`USING gin (...)`).

The index has to be built over **exactly** the same expression the
query uses — `to_tsvector('english', body)` — or the planner won't
recognize that the index applies. Then write the query above into
`solution.sql`.

## 3. What you should see in the plan

```
Bitmap Heap Scan
  -> Bitmap Index Scan on <your GIN index>
```

A GIN (Generalized Inverted iNdex) index stores, for each distinct
lexeme, the list of rows containing it — the inverse of "for each row,
what words does it contain," hence "inverted index." Looking up
`'dog'` means one lookup into that structure instead of tokenizing all
million rows. Like other index types that return a set of candidate
rows rather than a single ordered walk, GIN index scans surface in
`EXPLAIN` output as a `Bitmap Index Scan` feeding a `Bitmap Heap Scan`.

## 4. Why the speedup is so large here

Without the index, Postgres has to compute `to_tsvector('english',
body)` **from scratch for every one of 1,000,000 rows**, then check
each result against the query. That's real CPU work per row, not just
a fast column comparison — measured on the seeded template, that seq
scan takes **6.6-8.8 seconds**. With the GIN index in place, the same
query runs in **~40-48ms** — roughly **150-200x faster**. This
lesson's gate uses the brief's `ratio=10`, which is comfortably below
what's actually achievable; the real number you'll see locally is much
larger.

## 5. A correctness note (why `expected.sql` isn't the `ILIKE` version)

`expected.sql` uses the *same* `to_tsvector(...) @@ plainto_tsquery(...)`
predicate as the intended solution, not an `ILIKE '%dog%'` baseline.
That's deliberate: full-text search does stemming and tokenization
(e.g. it would also match "dogs," "Dog," or text where "dog" appears
next to punctuation), so an `ILIKE` pattern and a `tsquery` predicate
don't always return identical row sets even when both "obviously" mean
the same search. Comparing a `tsquery` result against an `ILIKE`
"ground truth" would occasionally fail correctness for a perfectly
correct full-text query. Keeping `expected.sql` and `solution.sql` on
the same predicate form means correctness checks the *rows*, and the
plan/speed gates are what actually verify you used the index.

## 6. Run it

```bash
.venv/Scripts/pytest lessons/12_gin_fulltext -v
```

## 7. The gate

Correctness, then the plan must contain a `Bitmap Index Scan` (how GIN
index usage surfaces in `EXPLAIN`), then at least a 10x speedup over
the no-index baseline.

## 8. The teaching point

GIN indexes are for **multi-valued** column data: a `tsvector` is
really a set of lexemes per row, and GIN is built exactly for "find
rows whose set contains X" queries — the same reason it's also the
right index type for array containment and JSONB containment (lesson
13). It's a fundamentally different shape than a B-tree, which assumes
one sortable scalar per row. Full-text search is the most common place
you'll reach for it in an ordinary application: whenever "search for
text containing this word/phrase" shows up as a real query pattern
against more than a trivial amount of text, `tsvector` + GIN is the
standard answer.
