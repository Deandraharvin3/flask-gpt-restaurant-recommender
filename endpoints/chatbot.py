from openai import OpenAI
import requests

client = OpenAI(
        api_key="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"
    )
# 1. Define the Tool Menu for GPT
custom_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_driving_distance",
            "description": "Calculates the driving distance and estimated travel time between two locations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "The user's starting city or location."
                    },
                    "destination": {
                        "type": "string",
                        "description": "The exact name and city of the restaurant."
                    }
                },
                "required": ["origin", "destination"]
            }
        }
    }
]

def chat_with_gpt(messages):
    response = client.responses.create(
        model="gpt-4o",
        tools=[{
            "type": "web_search",
        }],
        input=messages,
    )
    return response.output_text

def voice_chat_with_gpt(audio_value):
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file = audio_value
    )
    return response

def get_google_place_photo(restaurant_query, city="Baltimore"):

    api_key = "AIzaSyC-RDrpaoAevYI0Ra1CPaRmsSMfoqBJ1Fo"
    print("API KEY FOUND:", api_key is not None)

    if not api_key:
        print("❌ No GOOGLE_MAPS_API_KEY found in secrets")
        return None

    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.photos"
    }

    payload = {
        "textQuery": restaurant_query + " restaurant " + city
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)

        print("STATUS CODE:", response.status_code)
        print("RESPONSE TEXT:", response.text)

        response.raise_for_status()

        data = response.json()
        print("PARSED DATA:", data)

        places = data.get("places", [])
        if not places:
            print("❌ No places found")
            return None

        first_place = places[0]
        photos = first_place.get("photos", [])

        place_name = first_place.get("displayName", {}).get("text", restaurant_query)
        address = first_place.get("formattedAddress", "")

        if not photos:
            print("⚠️ Place found but no photos")
            return {
                "name": place_name,
                "address": address,
                "photo_url": None
            }

        photo_name = photos[0]["name"]

        photo_url = (
            "https://places.googleapis.com/v1/"
            + photo_name
            + "/media?maxWidthPx=800&key="
            + api_key
        )

        print("✅ PHOTO URL:", photo_url)

        return {
            "name": place_name,
            "address": address,
            "photo_url": photo_url
        }

    except requests.RequestException as e:
        print("❌ Request failed:", e)
        if hasattr(e, "response") and e.response is not None:
            print("❌ Error response body:", e.response.text)
        return None
