"""Seed script for Smart Culinary Concierge Firestore recipes collection."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-02-82e7d8040503"

INITIAL_RECIPES = [
    {
        "recipe_id": "creamy-mushroom-risotto",
        "title": "Creamy Mushroom Risotto",
        "cuisine": "Italian",
        "cooking_time_minutes": 35,
        "dietary_tags": ["vegetarian", "gluten-free"],
        "ingredients": [
            "1.5 cups Arborio rice",
            "8 oz cremini mushrooms, sliced",
            "4 cups vegetable broth (warm)",
            "1/2 cup dry white wine",
            "1/2 cup grated Parmesan cheese",
            "2 tbsp butter",
            "1 shallot, minced",
            "2 cloves garlic, minced",
        ],
        "instructions": (
            "1. Sauté mushrooms in 1 tbsp butter until golden, set aside.\n"
            "2. In the same pan, sauté shallots and garlic. Add Arborio rice and toast 2 mins.\n"
            "3. Deglaze with white wine and stir until absorbed.\n"
            "4. Add warm broth 1 ladle at a time, stirring constantly until absorbed.\n"
            "5. Stir in cooked mushrooms, remaining butter, and Parmesan cheese. Serve warm."
        ),
    },
    {
        "recipe_id": "thai-green-curry",
        "title": "Thai Green Vegetable Curry",
        "cuisine": "Thai",
        "cooking_time_minutes": 25,
        "dietary_tags": ["vegan", "gluten-free", "dairy-free"],
        "ingredients": [
            "1 can (14 oz) coconut milk",
            "2 tbsp Thai green curry paste",
            "1 block (14 oz) extra-firm tofu, cubed",
            "1 cup bamboo shoots",
            "1 cup red bell pepper, sliced",
            "1 cup Thai basil leaves",
            "1 tbsp soy sauce or tamari",
            "1 tsp coconut sugar",
        ],
        "instructions": (
            "1. Heat 1/4 cup coconut milk in a pan until simmering. Add green curry paste and fry 2 mins.\n"
            "2. Pour in remaining coconut milk, tofu, bell pepper, and bamboo shoots.\n"
            "3. Simmer gently for 10-12 minutes until vegetables are tender-crisp.\n"
            "4. Stir in soy sauce, sugar, and Thai basil. Serve with jasmine rice."
        ),
    },
    {
        "recipe_id": "mediterranean-chickpea-salad",
        "title": "Mediterranean Chickpea Salad",
        "cuisine": "Mediterranean",
        "cooking_time_minutes": 15,
        "dietary_tags": ["vegetarian", "vegan-optional", "gluten-free"],
        "ingredients": [
            "2 cans (15 oz each) chickpeas, drained and rinsed",
            "1 English cucumber, diced",
            "1 cup cherry tomatoes, halved",
            "1/2 red onion, finely diced",
            "1/2 cup crumbled feta cheese",
            "1/4 cup extra virgin olive oil",
            "2 tbsp fresh lemon juice",
            "1 tsp dried oregano",
        ],
        "instructions": (
            "1. Combine chickpeas, cucumber, cherry tomatoes, and red onion in a large bowl.\n"
            "2. Whisk together olive oil, lemon juice, dried oregano, salt, and pepper.\n"
            "3. Toss salad with dressing and gently fold in feta cheese.\n"
            "4. Chill for 10 minutes before serving."
        ),
    },
    {
        "recipe_id": "avocado-egg-breakfast-toast",
        "title": "Avocado & Poached Egg Toast",
        "cuisine": "American",
        "cooking_time_minutes": 10,
        "dietary_tags": ["vegetarian", "high-protein"],
        "ingredients": [
            "2 slices sourdough bread, toasted",
            "1 ripe avocado",
            "2 fresh large eggs",
            "1 tbsp lemon juice",
            "1/4 tsp red pepper flakes",
            "Salt & freshly ground black pepper",
        ],
        "instructions": (
            "1. Mash avocado with lemon juice, salt, and black pepper.\n"
            "2. Poach eggs in simmering water with 1 tsp vinegar for 3 minutes.\n"
            "3. Spread mashed avocado evenly onto toasted sourdough slices.\n"
            "4. Top each toast with a poached egg and sprinkle with red pepper flakes."
        ),
    },
]


def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    recipes_ref = db.collection("recipes")

    print(f"Seeding recipes to Firestore project '{PROJECT_ID}'...")
    for recipe in INITIAL_RECIPES:
        doc_id = recipe["recipe_id"]
        recipes_ref.document(doc_id).set(recipe)
        print(f"  - Seeded: {recipe['title']} (ID: {doc_id})")

    print("Seeding complete! Successfully added initial recipes to Firestore.")


if __name__ == "__main__":
    seed_database()
