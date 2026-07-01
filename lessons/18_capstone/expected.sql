-- CORRECTNESS ANSWER KEY + TIMING BASELINE for the capstone.
--
-- Report: the top 10 products by revenue from PAID orders placed in the
-- last 7 days of the dataset (a fixed recent window -- the seed data is a
-- fixed snapshot whose most recent order is 2023-11-14, so we anchor the
-- window to a fixed date rather than now()), together with each of those
-- products' total review count.
--
-- This is written the naive, obvious way: aggregate revenue per product,
-- separately aggregate review counts for EVERY product, then join. It is
-- correct but slow with no indexes -- the harness measures its runtime as
-- the baseline the learner's solution must beat.
--
-- Note the two aggregations are kept SEPARATE (two CTEs). Joining
-- order_items and reviews to products in one flat query would multiply the
-- two one-to-many relationships and inflate revenue by the review count
-- (a fan-out bug). Keep them apart.
WITH rev AS (
    SELECT oi.product_id,
           SUM(oi.quantity * oi.price) AS revenue
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id
    WHERE o.status = 'paid'
      AND o.created_at >= '2023-11-07'::timestamptz
    GROUP BY oi.product_id
),
rc AS (
    SELECT product_id, count(*) AS review_count
    FROM reviews
    GROUP BY product_id
)
SELECT p.id,
       p.name,
       rev.revenue,
       COALESCE(rc.review_count, 0) AS review_count
FROM rev
JOIN products p ON p.id = rev.product_id
LEFT JOIN rc ON rc.product_id = rev.product_id
ORDER BY rev.revenue DESC, p.id
LIMIT 10;
