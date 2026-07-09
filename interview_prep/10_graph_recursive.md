# 10 — Recursive CTE: Full Attack Path

Using the reachability table from problem 9: given a host a tester has
compromised, the interesting question isn't "2 hops away," it's "every
host reachable at all, through any chain of hops" — a lateral-movement
footprint.

## Task

- Write a recursive CTE that, given one starting host, returns every host
  reachable from it through any number of hops (the transitive closure),
  each with the hop count at which it was first reached.
- Make sure a cycle in the reachability graph (A → B → A) can't put your
  query into an infinite loop. Test this: add a cycle to your seed data
  and confirm the query still terminates and doesn't return the same host
  twice.
- Extend it: also return the *path* taken to reach each host (e.g. as an
  array of hostnames), not just the destination.
- One-line answer: what part of the recursive CTE is responsible for the
  query eventually stopping?
