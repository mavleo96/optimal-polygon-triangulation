```text
Algorithm OPTIMAL-TRIANGULATION(P, w)
    n ← |P|
    split, cost ← n × n arrays initialized to None
    DP(0, n - 1)
    return BACKTRACK(0, n - 1)


Function DP(a, b)
    if split[a][b] ≠ None then
        return cost[a][b]                      // memoized value

    if (a, b) is a polygon edge then
        split[a][b] ← -1
        cost[a][b] ← None
        return None

    if (a, b) is not a valid diagonal then
        split[a][b] ← -1
        cost[a][b] ← ∞
        return ∞

    restrict polygon chain to arc [a, b]      // enables O(b - a) child checks
    best_cost ← ∞
    best_split ← -1

    for each c with a < c < b do
        cost_c ← w(d(a, b), DP(a, c), DP(c, b))
        if cost_c < best_cost then
            best_cost ← cost_c
            best_split ← c

    split[a][b] ← best_split
    cost[a][b] ← best_cost
    restore polygon chain
    return best_cost


Function BACKTRACK(a, b)
    if (a, b) is a polygon edge then
        return [], []

    c ← split[a][b]
    triangles ← [(a, c, b)]
    diagonals ← [(a, b)] if (a, b) is not a polygon edge, else []

    T_L, D_L ← BACKTRACK(a, c)
    T_R, D_R ← BACKTRACK(c, b)
    return triangles + T_L + T_R, diagonals + D_L + D_R


// d(a, b) = |v_a v_b| if (a, b) is a diagonal; otherwise None
// w_sum(b, l, r) = (b ?? 0) + (l ?? 0) + (r ?? 0)
// w_max(b, l, r) = max{b, l, r}, ignoring None
// w_min(b, l, r) = max{-b, l, r}, ignoring None (negate b to maximize the shortest edge)
```