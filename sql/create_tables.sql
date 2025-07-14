CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    customer_name TEXT,
    reason TEXT,
    channel TEXT,
    created_at TIMESTAMP
);