import sqlite3

dummy_plates = [
    ("Lilac City Grill", "New England Clam Chowder", "Soup", "103 N Main St, Rochester, NH, USA", "03867", "Rochester", "NH", 5, "Creamy and full of clams.", "clamchowder.jpg", 43.3045, -70.9786),
    ("Spaulding Steak & Ale", "Prime Rib", "Meat", "500 Spaulding Turnpike, Rochester, NH, USA", "03867", "Rochester", "NH", 4, "Tender, juicy prime rib.", "primerib.jpg", 43.3040, -70.9872),
    ("China Palace", "General Tso's Chicken", "Fried Food", "21 S Main St, Rochester, NH, USA", "03867", "Rochester", "NH", 4, "Crispy and tangy.", "generaltso.jpg", 43.3018, -70.9727),
    ("Revolution Taproom & Grill", "Fish Tacos", "Taco", "61 N Main St, Rochester, NH, USA", "03867", "Rochester", "NH", 5, "Fresh and zesty tacos.", "fishtacos.jpg", 43.3057, -70.9782),
    ("Dos Amigos Burritos", "Vegetarian Burrito", "Vegetarian", "55 N Main St, Rochester, NH, USA", "03867", "Rochester", "NH", 5, "Loaded with veggies!", "vegburrito.jpg", 43.3052, -70.9783),
    ("Granite Steak & Grill", "Cheesecake", "Dessert", "11 Farmington Rd, Rochester, NH, USA", "03867", "Rochester", "NH", 5, "Rich and creamy.", "cheesecake.jpg", 43.2971, -70.9765),
    ("La Corona Mexican Restaurant", "Chicken Enchiladas", "Wrap", "83 S Main St, Rochester, NH, USA", "03867", "Rochester", "NH", 4, "Spicy and satisfying.", "enchiladas.jpg", 43.2993, -70.9726),
]

conn = sqlite3.connect("restaurant.db")
for plate in dummy_plates:
    conn.execute('''
        INSERT INTO plates (restaurant, plate, category, address, zipcode, city, state, rating, comment, photo, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', plate)
conn.commit()
conn.close()
print("Rochester NH dummy data loaded!")