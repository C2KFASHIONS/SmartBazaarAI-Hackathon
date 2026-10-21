from flask import Flask, jsonify, request, render_template
from catalog import PRODUCTS, assistant_reply

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/products")
def products():
    return jsonify(PRODUCTS)

@app.post("/api/search")
def search():
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")
    if not isinstance(message, str) or len(message) > 1000:
        return jsonify({"error": "message must be text up to 1000 characters"}), 400
    return jsonify(assistant_reply(message))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
