# P3 implementation note

While adding the packet prerequisite, `scripts/promotion_gate.py` also removes an unreachable duplicate copy of the old regime-evaluation block that appeared after an unconditional `return` in `verdict_for`. This is an auditability cleanup only: the live regime-crossover computation remains in `_verdict_for_net_metric`, and P3 pins every historical verdict to its pre-change value.
