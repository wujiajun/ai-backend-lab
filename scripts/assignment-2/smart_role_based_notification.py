
print("Smart Role-Based Notification Script executed successfully!")


users = [
    {"id": 1, "name": "Alice", "role": "admin", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "role": "user", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "role": "editor", "email": "charlie@example.com"},
    {"id": 4, "name": "David", "role": "user", "email": "david@example.com"},
]

logged_in_users = [
    user["id"] for user in users if user["id"] in [1, 2]
]  # Example: Alice and Bob are logged in
