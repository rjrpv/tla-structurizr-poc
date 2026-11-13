workspace "ReservationSystem" "Architecture half of the RJR-267 proof of concept" {

    model {

        customers = person "Customers" "People who request tickets"

        reservation = softwareSystem "Reservation Counter" "Keeps a stock of tickets and answers requests: sell if stock remains, else reject" {

            intake = container "Request Intake" "Accepts a ticket request from a customer who has not yet been answered" "Java"
            serving = container "Serving Logic" "Serves one pending request; sells a ticket if stock remains, otherwise rejects" "Java"
            inventory = container "Inventory" "Tracks the number of tickets in stock (MaxInventory)" "In-memory"
            ledger = container "Ledger" "Records who was sold a ticket and who was rejected" "In-memory"
        }

        customers -> intake "requests a ticket" "HTTP"
        intake -> serving "enqueues a pending request"
        serving -> inventory "reads / decrements stock"
        serving -> ledger "records sale or rejection"
    }

    views {

        systemContext reservation "reservation-context" "System context: who uses the reservation counter" {
            include *
        }

        container reservation "reservation-container" "Container view of the reservation counter" {
            include *
        }

        dynamic reservation "reservation-dynamic" "Dynamic view: the request-then-serve flow" {
        }

        theme default
    }
}
