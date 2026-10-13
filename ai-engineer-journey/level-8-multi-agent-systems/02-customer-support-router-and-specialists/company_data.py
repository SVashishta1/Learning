"""A pretend company backend: customers, invoices, a help-centre knowledge base and a ticket system."""
CUSTOMERS = {
    "C-1001": {"name": "Priya Shah", "email": "priya@example.com", "plan": "Pro", "status": "active"},
    "C-1002": {"name": "Tom Becker", "email": "tom@example.com", "plan": "Basic", "status": "past_due"},
    "C-1003": {"name": "Ana Lima", "email": "ana@example.com", "plan": "Team", "status": "active"},
}
INVOICES = {
    "INV-501": {"customer": "C-1001", "amount": 29.0, "status": "paid", "note": "Pro plan, October"},
    "INV-502": {"customer": "C-1001", "amount": 29.0, "status": "paid", "note": "Pro plan, October (DUPLICATE CHARGE)"},
    "INV-601": {"customer": "C-1002", "amount": 9.0, "status": "unpaid", "note": "Basic plan, October"},
    "INV-701": {"customer": "C-1003", "amount": 249.0, "status": "paid", "note": "Team plan, 10 seats, October"},
}
KB = [
    {"id": "KB-1", "title": "Reset your password", "body": "Go to Settings > Security > Reset password. A link valid for 30 minutes is emailed to you."},
    {"id": "KB-2", "title": "App crashes on startup", "body": "Update to version 4.2 or later. If it still crashes, clear the cache: Settings > Storage > Clear cache, then restart."},
    {"id": "KB-3", "title": "Sync is slow", "body": "Sync pauses on battery saver mode. Disable battery saver or connect to Wi-Fi. Large files over 2 GB sync overnight."},
    {"id": "KB-4", "title": "Export your data", "body": "Settings > Account > Export creates a ZIP of all your files and is emailed within 24 hours."},
]
TICKETS: list[dict] = []
REFUND_AUTO_LIMIT = 50.0     # company policy: refunds above this need a human manager
