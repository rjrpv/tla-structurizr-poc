"""Mirror package for the canonical TLA+ examples (RJR-275).

Each module here is the Python mirror of one ``examples/*.tla`` model:

    traffic_light, counter, fifo_queue, leader_election, token_ring,
    inventory, key_value_store, consensus

The modules are intentionally independent (each is a standalone one-property
model), so the dependency graph is eight isolated modules. ``code/observe.py``
watches this package (``--target examples``) and diffs its graph against
``examples/baseline.json``.
"""
