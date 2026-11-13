workspace "ReservationSystem (generated from code)" "Derived from code/reservation" {
    model {
        customers = person "Customers"
        reservation = softwareSystem "Reservation System" {
            intake = container "Request Intake" "Python module intake.py (RequestIntake)"
            inventory = container "Inventory" "Python module inventory.py (Inventory)"
            ledger = container "Ledger" "Python module ledger.py (Ledger)"
            serving = container "Serving Logic" "Python module serving.py (ServingLogic)"
        }
        customers -> reservation "requests a ticket"
        intake -> serving "imports"
        serving -> inventory "imports"
        serving -> ledger "imports"
    }
    views {
        systemContext reservation "generated-context" {
            include *
        }
        container reservation "generated-container" {
            include *
        }
    }
}
