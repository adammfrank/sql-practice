# 09 — Network Reachability (One Hop)

Testers also record which hosts can reach which other hosts on the
network (discovered via port scans, ARP tables, etc.) — this is directed:
host A being able to reach host B doesn't mean B can reach A.

## Task

- Design and create a table representing "host A can reach host B" for
  assets *within the same engagement*. Think about what the primary key
  of this table should be, and why a plain auto-increment id here would
  hide a real bug (duplicate edges).
- Seed a small network for one engagement: 5-6 hosts with a mix of
  reachability, including at least one host reachable from two different
  hosts, and at least one host that can't reach anything.
- Write a query: given one specific host, list every host directly
  reachable from it (one hop).
- Write a query using a self-join on your reachability table: for a given
  starting host, list every host reachable in *exactly two* hops,
  excluding the starting host itself if a loop leads back to it.

## Think about

At what hop count does hardcoding another self-join for each additional
hop stop being reasonable? What would you reach for instead?
