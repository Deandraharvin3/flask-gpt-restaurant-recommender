from openai import OpenAI
import requests
import json
import os

client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY")
    )
# 1. Define the Tool Menu for GPT
import json

custom_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_driving_distance",
            "description": "Calculates the driving distance and estimated travel time between two locations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "The user's starting city or location."},
                    "destination": {"type": "string", "description": "The exact name and city of the restaurant."}
                },
                "required": ["origin", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_google_place_photo",
            "description": "Fetches a real photo URL and address for a specific restaurant using Google Places.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_query": {"type": "string", "description": "The name of the restaurant."},
                    "city": {"type": "string", "description": "The city the restaurant is in (default is Baltimore)."}
                },
                "required": ["restaurant_query"]
            }
        }
    }
]

def chat_with_gpt(messages, message=None, image=None):
    if image:
        print("Got image:", image)
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": message},
                    {
                        "type": "input_image",
                        "image_url": image,
                    },
                ],
            }],
        )
        
        return response.output_text

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=custom_tools,
        tool_choice="auto"
    )
    
    response_message = response.choices[0].message

    # 2. Did GPT decide to use a tool?
    if response_message.tool_calls:
        
        # THE FIX: Convert the complex OpenAI object into a standard Python dictionary
        assistant_msg = {
            "role": "assistant",
            "content": response_message.content,
            "tool_calls": [
                {
                    "id": tool.id,
                    "type": tool.type,
                    "function": {
                        "name": tool.function.name,
                        "arguments": tool.function.arguments
                    }
                } for tool in response_message.tool_calls
            ]
        }
        
        # Append the safe dictionary to the history
        messages.append(assistant_msg)
        
        # Loop through the tools it wants to use
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "get_google_place_photo":
                args = json.loads(tool_call.function.arguments)
                
                # Run your Google Python function
                result = get_google_place_photo(
                    restaurant_query=args.get("restaurant_query"), 
                    city=args.get("city", "Baltimore")
                )
                
                # Feed the JSON result back into the chat history
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": "get_google_place_photo",
                    "content": json.dumps(result)
                })
        
        # 3. Send the updated history back to GPT so it can format the final HTML response
        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return final_response.choices[0].message.content

    # If it didn't use a tool, just return the standard text response
    return response_message.content

def voice_chat_with_gpt(audio_value):
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file = audio_value
    )
    return response

def get_google_place_photo(restaurant_query, city="Baltimore"):

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
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
