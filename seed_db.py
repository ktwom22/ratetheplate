import sqlite3

dummy_plates = [
    ("Big Burger Place", "Classic Cheeseburger", "Burger", "123 Main St, Metropolis, NY, USA", "10001", "Metropolis", "NY", 5, "Juicy! Perfect cheese.", "burger.jpg", 40.7128, -74.0060),
    ("Sushi World", "Salmon Nigiri", "Sushi", "456 Ocean Ave, San Francisco, CA, USA", "94105", "San Francisco", "CA", 4, "Fresh and bright.", "sushi.jpg", 37.7749, -122.4194),
    ("Pasta Palace", "Spaghetti Carbonara", "Pasta", "789 Italian Rd, Chicago, IL, USA", "60601", "Chicago", "IL", 5, "Creamy and rich.", "carbonara.jpg", 41.8781, -87.6298),
    ("Vegan Table", "Quinoa Salad", "Salad", "321 Green St, Portland, OR, USA", "97201", "Portland", "OR", 3, "Healthy, but a bit bland.", "quinoa.jpg", 45.5051, -122.6750),
    ("Taco Spot", "Carne Asada Taco", "Taco", "654 Fiesta Blvd, Austin, TX, USA", "78701", "Austin", "TX", 5, "Spicy and flavorful.", "taco.jpg", 30.2672, -97.7431),
    ("Sweet Treats", "Chocolate Cake", "Cake", "987 Dessert Ln, Miami, FL, USA", "33101", "Miami", "FL", 4, "Very rich, moist.", "cake.jpg", 25.7617, -80.1918),
    ("Breakfast Barn", "Pancakes", "Breakfast", "246 Morning Dr, Denver, CO, USA", "80202", "Denver", "CO", 5, "Fluffy stacks!", "pancakes.jpg", 39.7392, -104.9903),
]

conn = sqlite3.connect("restaurant.db")
for plate in dummy_plates:
    conn.execute('''
        INSERT INTO plates (restaurant, plate, category, address, zipcode, city, state, rating, comment, photo, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', plate)
conn.commit()
conn.close()
print("Dummy data loaded!")