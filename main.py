from flask import Flask, render_template, redirect, url_for
import os
from endpoints.routes import api_bp, PERSONAS # Import PERSONAS from routes

app = Flask(__name__)
app.register_blueprint(api_bp)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-developer-key")

@app.route('/')
def home():
    # Redirect the base URL to the Chef Dee dashboard automatically
    return redirect(url_for('chat_page', persona_id='chef'))

@app.route('/chat/<persona_id>')
def chat_page(persona_id):
    # If they type a weird URL, send them back to Chef Dee
    if persona_id not in PERSONAS:
        return redirect(url_for('chat_page', persona_id='chef'))
    
    # Get the specific bot's info
    current_bot = PERSONAS[persona_id]
    
    # Render the ONE template, but pass the dynamic data to it
    return render_template(
        "chat.html", 
        personas=PERSONAS, 
        current_id=persona_id,
        bot=current_bot
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)