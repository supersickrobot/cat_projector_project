"""WhatsApp bot for controlling the cat projector toy remotely.
Uses Twilio's WhatsApp API to receive messages and control video playback.
Runs on the Raspberry Pi as a Flask web server that receives webhook callbacks from Twilio.

To expose this to the internet (required for Twilio webhooks), use ngrok:
    ngrok http 5000
Then set the ngrok URL as your Twilio WhatsApp webhook.
"""
import logging
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import playback_controller
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
)
log = logging.getLogger("whatsapp_bot")

app = Flask(__name__)

# Allowed phone numbers (WhatsApp format: "whatsapp:+1234567890")
# Leave empty to allow any number, or add specific numbers for security
ALLOWED_NUMBERS = []

HELP_TEXT = """🐱 Cat Projector Commands:
• *on* - Start the current scene
• *off* - Stop playback
• *fish* - Play the fish scene
• *status* - Check what's playing
• *scenes* - List available scenes
• *play <name>* - Play a specific scene
• *help* - Show this message"""


def handle_command(message_body, sender_number):
    """Parse an incoming message and execute the appropriate command.
    Returns a response string to send back via WhatsApp.
    """
    command = message_body.strip().lower()

    if command in ("on", "start", "play"):
        # Start the default or last scene
        success, response = playback_controller.start_playback("fish")
        return f"🐟 {response}"

    elif command in ("off", "stop"):
        success, response = playback_controller.stop_playback()
        return f"⏹️ {response}"

    elif command == "fish":
        success, response = playback_controller.start_playback("fish")
        return f"🐟 {response}"

    elif command == "status":
        status = playback_controller.get_status()
        return f"📊 {status}"

    elif command in ("scenes", "list"):
        scenes = playback_controller.list_available_scenes()
        if scenes:
            scene_list = "\n".join([f"  • {scene}" for scene in scenes])
            return f"🎬 Available scenes:\n{scene_list}"
        return "🎬 No scenes available. Upload some videos first."

    elif command.startswith("play "):
        scene_name = command[5:].strip()
        if scene_name:
            success, response = playback_controller.switch_scene(scene_name)
            return f"🎬 {response}"
        return "Usage: play <scene_name>"

    elif command in ("help", "?", "commands"):
        return HELP_TEXT

    else:
        # For unrecognized commands, be friendly and suggest help
        return f"🐱 I don't know '{command}'. Send *help* to see available commands."


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Twilio webhook endpoint for incoming WhatsApp messages."""
    sender_number = request.form.get("From", "")
    message_body = request.form.get("Body", "")

    log.info(f"Message from {sender_number}: {message_body}")

    # Optional: restrict to allowed numbers
    if ALLOWED_NUMBERS and sender_number not in ALLOWED_NUMBERS:
        log.info(f"Rejected message from unauthorized number: {sender_number}")
        response = MessagingResponse()
        response.message("🚫 Unauthorized. This cat projector doesn't know you.")
        return str(response)

    # Process the command
    reply_text = handle_command(message_body, sender_number)
    log.info(f"Reply to {sender_number}: {reply_text}")

    # Build Twilio response
    response = MessagingResponse()
    response.message(reply_text)
    return str(response)


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    status = playback_controller.get_status()
    return {"status": "ok", "playback": status}


@app.route("/", methods=["GET"])
def index():
    """Landing page with basic info."""
    return """
    <h1>🐱 Cat Projector</h1>
    <p>WhatsApp bot is running. Send a message to control the projector.</p>
    <p>Status: {}</p>
    <p>Endpoints:</p>
    <ul>
        <li><code>POST /whatsapp</code> - Twilio webhook</li>
        <li><code>GET /health</code> - Health check</li>
    </ul>
    """.format(playback_controller.get_status())


def main():
    """Start the WhatsApp bot server."""
    print("=" * 50)
    print("🐱 Cat Projector - WhatsApp Bot")
    print("=" * 50)
    print(f"Listening on {config.FLASK_HOST}:{config.FLASK_PORT}")
    print(f"WhatsApp webhook: http://localhost:{config.FLASK_PORT}/whatsapp")
    print()
    print("To expose to internet, run in another terminal:")
    print(f"  ngrok http {config.FLASK_PORT}")
    print()
    print("Then set the ngrok HTTPS URL + /whatsapp as your")
    print("Twilio WhatsApp sandbox webhook URL.")
    print()

    available_scenes = playback_controller.list_available_scenes()
    print(f"Available scenes: {', '.join(available_scenes) or 'none'}")
    print("=" * 50)

    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False)


if __name__ == "__main__":
    main()
