# The Architectural Half — Structurizr

**File:** [`structurizr/reservation.dsl`](../structurizr/reservation.dsl)
**Diagrams:** [`structurizr/diagrams/`](../structurizr/diagrams)

## What Structurizr is

[Structurizr](https://structurizr.com/) is an **architecture-as-code** tool.
You describe a system as a model — software systems, containers, components,
people, and the relationships between them — in a declarative DSL (or via its
Java/C# libraries). From that single model it generates a family of
C4-style diagrams:

- **System Context** — the system and the actors that use it.
- **Container** — the deployable/technical units inside the system.
- **Component** — the major components inside a container.
- **Dynamic** — the sequence of interactions between elements.

The key property: **one source of truth, many views.** The diagrams are
*derived* from the model, so they can't drift out of sync with the
architecture — and they're versionable, diffable, and CI-checkable like any
other code.

## The model

```
workspace "ReservationSystem" {
    model {
        customers = person "Customers"
        reservation = softwareSystem "Reservation Counter" {
            intake    = container "Request Intake"
            serving   = container "Serving Logic"
            inventory = container "Inventory"
            ledger    = container "Ledger"
        }
        customers -> intake    "requests a ticket"
        intake    -> serving   "enqueues a pending request"
        serving   -> inventory "reads / decrements stock"
        serving   -> ledger    "records sale or rejection"
    }
    views {
        systemContext reservation "reservation-context"
        container     reservation "reservation-container"
        dynamic       reservation "reservation-dynamic"
    }
}
```

Four containers, one actor, four relationships — the *structural* skeleton of
the same reservation counter the TLA+ spec models *behaviorally*.

## The views

| View | File | Shows |
|------|------|-------|
| System Context | [`diagrams/context.png`](../structurizr/diagrams/context.png) | Customers ↔ Reservation Counter |
| Container | [`diagrams/container.png`](../structurizr/diagrams/container.png) | Intake, Serving, Inventory, Ledger and their relationships |
| Dynamic | [`diagrams/dynamic.png`](../structurizr/diagrams/dynamic.png) | The request → serve → record flow |

There's also an **interactive static site** at
[`diagrams/index.html`](../structurizr/diagrams/index.html) — open it in a
browser to pan/zoom and inspect each view.

## Running it

```sh
# validate the model
structurizr validate -w structurizr/reservation.dsl

# export the static site (needs a JDK; the .png files were captured from the
# rendered site)
structurizr export -w structurizr/reservation.dsl -f static -o structurizr/diagrams
```

## Environment notes (this sandbox)

- The `structurizr-cli` `export -f static` site renders client-side in the
  browser (no Graphviz needed). `autoLayout` *does* require the `dot` binary,
  which isn't available here, so the model relies on Structurizr's default
  layout.
- This DSL version uses `container` (not `component`) inside a software
  system, and dynamic views include all relationships by default (no
  `include *`).
- The `.png` files are screenshots of the rendered static site; the
  authoritative artifact is the DSL model + the interactive `index.html`.
