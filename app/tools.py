import json
import os
import re
import urllib.parse
import urllib.request
from google.cloud import firestore, storage
from google.adk.tools import ToolContext

PROJECT_ID = "qwiklabs-gcp-02-82e7d8040503"


def search_recipes(query: str = "", cuisine: str = "", dietary_tag: str = "", max_cooking_time: int = 0) -> str:
    """Searches the Firestore database for recipes matching criteria.

    Args:
        query: Optional text query to search recipe titles or ingredients.
        cuisine: Optional cuisine filter (e.g. 'Italian', 'Thai', 'Mediterranean').
        dietary_tag: Optional dietary tag filter (e.g. 'vegetarian', 'vegan', 'gluten-free').
        max_cooking_time: Optional maximum cooking time in minutes (0 means no limit).

    Returns:
        A list of matching recipe summaries.
    """
    db = firestore.Client(project=PROJECT_ID)
    docs = db.collection("recipes").stream()
    matches = []

    for doc in docs:
        data = doc.to_dict()
        title = data.get("title", "")
        c_cuisine = data.get("cuisine", "")
        tags = [t.lower() for t in data.get("dietary_tags", [])]
        time_mins = data.get("cooking_time_minutes", 0)
        ingredients = " ".join(data.get("ingredients", [])).lower()

        if query and (query.lower() not in title.lower() and query.lower() not in ingredients):
            continue
        if cuisine and cuisine.lower() not in c_cuisine.lower():
            continue
        if dietary_tag and dietary_tag.lower() not in tags:
            continue
        if max_cooking_time > 0 and time_mins > max_cooking_time:
            continue

        matches.append({
            "recipe_id": doc.id,
            "title": title,
            "cuisine": c_cuisine,
            "cooking_time_minutes": time_mins,
            "dietary_tags": data.get("dietary_tags", []),
        })

    if not matches:
        return "No recipes found matching your search criteria."
    return str(matches)


def get_recipe_details(recipe_id: str) -> str:
    """Fetches full recipe details (ingredients, instructions) by recipe ID from Firestore.

    Args:
        recipe_id: The document ID of the recipe (e.g., 'creamy-mushroom-risotto').

    Returns:
        Full recipe document containing title, ingredients, and instructions.
    """
    db = firestore.Client(project=PROJECT_ID)
    doc_ref = db.collection("recipes").document(recipe_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"Recipe with ID '{recipe_id}' not found."
    return str(doc.to_dict())


def save_recipe(
    title: str,
    cuisine: str,
    cooking_time_minutes: int,
    dietary_tags: list[str],
    ingredients: list[str],
    instructions: str,
) -> str:
    """Saves a new recipe into the Firestore database.

    Args:
        title: The title of the recipe.
        cuisine: The cuisine type (e.g. 'Italian', 'Mexican', 'Asian').
        cooking_time_minutes: Total preparation and cooking time in minutes.
        dietary_tags: List of dietary tags (e.g. ['vegetarian', 'gluten-free']).
        ingredients: List of ingredient strings.
        instructions: Step-by-step cooking instructions string.

    Returns:
        Confirmation message with the created recipe ID.
    """
    db = firestore.Client(project=PROJECT_ID)
    recipe_id = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    doc_data = {
        "recipe_id": recipe_id,
        "title": title,
        "cuisine": cuisine,
        "cooking_time_minutes": int(cooking_time_minutes),
        "dietary_tags": dietary_tags,
        "ingredients": ingredients,
        "instructions": instructions,
    }
    db.collection("recipes").document(recipe_id).set(doc_data)
    return f"Successfully saved recipe '{title}' to Firestore with ID: {recipe_id}"


def scale_recipe_ingredients(recipe_id: str, target_servings: int, base_servings: int = 2) -> str:
    """Scales ingredient quantities in a recipe for the requested target number of servings.

    Args:
        recipe_id: The document ID of the recipe (e.g., 'creamy-mushroom-risotto').
        target_servings: The target number of servings desired (e.g., 4, 6).
        base_servings: Original recipe servings count (default 2).

    Returns:
        A dictionary containing the scaled ingredient amounts for target_servings.
    """
    db = firestore.Client(project=PROJECT_ID)
    doc_ref = db.collection("recipes").document(recipe_id)
    doc = doc_ref.get()

    if not doc.exists:
        return f"Recipe '{recipe_id}' not found."

    data = doc.to_dict()
    title = data.get("title", recipe_id)
    ingredients = data.get("ingredients", [])
    factor = target_servings / max(1, base_servings)

    scaled_ingredients = []
    for item in ingredients:
        match = re.match(r"^(\d+(?:\.\d+)?|\d+/\d+)\s*(.*)$", item.strip())
        if match:
            raw_qty, rest = match.groups()
            if "/" in raw_qty:
                num, denom = raw_qty.split("/")
                qty = float(num) / float(denom)
            else:
                qty = float(raw_qty)
            scaled_qty = round(qty * factor, 2)
            if scaled_qty.is_integer():
                scaled_qty = int(scaled_qty)
            scaled_ingredients.append(f"{scaled_qty} {rest}")
        else:
            scaled_ingredients.append(f"{item} (scaled x{round(factor, 2)})")

    return str({
        "title": title,
        "base_servings": base_servings,
        "target_servings": target_servings,
        "scaled_ingredients": scaled_ingredients,
    })


def search_global_recipes(query: str) -> str:
    """Searches the open TheMealDB global recipe database for real external recipes, ingredients, and instructions.

    Args:
        query: The meal or ingredient name to search for (e.g. 'pasta', 'chicken', 'tacos', 'curry').

    Returns:
        A list of matching recipe results with title, category, cuisine/area, ingredients, and instructions.
    """
    api_key = os.getenv("THEMEALDB_API_KEY", "1")
    url = f"https://www.themealdb.com/api/json/v1/{api_key}/search.php?s={urllib.parse.quote(query)}"

    req = urllib.request.Request(url, headers={"User-Agent": "SmartCulinaryConcierge/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            meals = data.get("meals")
            if not meals:
                return f"No global recipes found for '{query}'."

            results = []
            for meal in meals[:3]:
                ingredients = []
                for i in range(1, 21):
                    ing = meal.get(f"strIngredient{i}")
                    meas = meal.get(f"strMeasure{i}")
                    if ing and ing.strip():
                        ingredients.append(f"{meas.strip() if meas else ''} {ing.strip()}".strip())

                results.append({
                    "title": meal.get("strMeal"),
                    "category": meal.get("strCategory"),
                    "cuisine": meal.get("strArea"),
                    "ingredients": ingredients,
                    "instructions": meal.get("strInstructions"),
                })
            return str(results)
    except Exception as e:
        return f"Error fetching global recipes from external API: {e}"


def geocode_address(address: str) -> str:
    """Converts a street address or city name into geographical coordinates (latitude, longitude).

    Args:
        address: The address or city name to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'San Francisco').

    Returns:
        A dictionary containing latitude, longitude, and formatted address.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not set in environment."

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={api_key}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            results = data.get("results", [])
            if not results:
                return f"No location found for address: '{address}'."

            first = results[0]
            loc = first["geometry"]["location"]
            return str({
                "address": first.get("formatted_address"),
                "latitude": loc["lat"],
                "longitude": loc["lng"],
            })
    except Exception as e:
        return f"Geocoding API error: {e}"


def find_nearby_places(place_type: str, latitude: float, longitude: float, radius_meters: float = 3000.0) -> str:
    """Finds nearby places of a given type (e.g. 'supermarket', 'grocery_store', 'restaurant', 'bakery') near coordinates.

    Args:
        place_type: The Google Places category/type (e.g. 'grocery_store', 'supermarket', 'restaurant', 'bakery').
        latitude: Latitude coordinate.
        longitude: Longitude coordinate.
        radius_meters: Search radius in meters (default 3000m / 3km).

    Returns:
        A list of nearby places with name, address, and location coordinates.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not set in environment."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    payload = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": float(latitude), "longitude": float(longitude)},
                "radius": float(radius_meters),
            }
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            places_list = data.get("places", [])
            if not places_list:
                return f"No nearby '{place_type}' places found near ({latitude}, {longitude})."

            results = []
            for p in places_list:
                results.append({
                    "name": p.get("displayName", {}).get("text", "Unknown"),
                    "address": p.get("formattedAddress", "N/A"),
                    "location": p.get("location", {}),
                })
            return str(results)
    except Exception as e:
        return f"Places API error: {e}"


BUCKET_NAME = "smart-culinary-concierge-media-82e7d8040503"


def generate_culinary_video(prompt: str, item_name: str, tool_context: ToolContext = None) -> str:
    """Generates a short video showcasing a culinary item, dish, or technique using Google's Omni model (gemini-omni-flash-preview).

    Args:
        prompt: Detailed description of the video scene (e.g., 'A 3-second close-up video of sizzling garlic and shrimp in olive oil').
        item_name: The name or title of the item/dish (e.g., 'garlic-butter-shrimp' or 'pasta-carbonara').
        tool_context: ADK ToolContext injected by the framework to save artifacts.

    Returns:
        The public HTTPS URL of the video uploaded to Cloud Storage.
    """
    import base64
    import google.auth
    from google.auth.transport.requests import Request
    from google.genai import types

    credentials, _ = google.auth.default()
    credentials.refresh(Request())
    token = credentials.token

    url = f"https://aiplatform.googleapis.com/v1beta1/projects/{PROJECT_ID}/locations/global/interactions"
    body = {
        "model": "gemini-omni-flash-preview",
        "input": [
            {"type": "text", "text": prompt}
        ]
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            res_data = json.loads(resp.read().decode())

        video_bytes = None
        for step in res_data.get("steps", []):
            if step.get("type") == "model_output":
                for content in step.get("content", []):
                    if content.get("type") == "video":
                        b64 = content.get("data")
                        if b64:
                            video_bytes = base64.b64decode(b64)
                            break

        if not video_bytes:
            return f"Error: No video bytes returned from gemini-omni-flash-preview for '{item_name}'."

        slug = re.sub(r"[^a-z0-9]+", "_", item_name.lower()).strip("_") or "culinary_item"
        filename = f"{slug}_video.mp4"

        # (1) Save video with tool_context.save_artifact for the Playground Artifacts panel
        if tool_context is not None and hasattr(tool_context, "save_artifact"):
            try:
                artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
                tool_context.save_artifact(filename=filename, artifact=artifact_part)
            except Exception as e:
                print(f"Warning: tool_context.save_artifact failed: {e}")

        # (2) Upload video bytes directly to public Cloud Storage bucket (no local file)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return public_url

    except Exception as e:
        return f"Error generating video with gemini-omni-flash-preview: {e}"




