# C001 specification addendum

This addendum resolves the local parameter-domain issue raised in `R1-M1` of the same-context review.

The registered domain for C001 is

`n >= 2` and `2 <= k <= n`.

The circuit size convention is the one already frozen in C001. Internal AND/OR gates are counted; input literals are leaves; constants are allowed in the restricted monotone comparison model.

Any quantitative monotone CLIQUE lower bound imported later must either use this convention or carry an explicit conversion argument. Until that source/convention binding is complete, C001 remains `PROOF_DRAFT` and no quantitative literature corollary is promoted.
