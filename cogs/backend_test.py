from flask import Flask, request

app = Flask(__name__)


@app.route("/api/files", methods=["POST"])
def receive_files():
    data = request.get_json()
    print("Received payload:", data)
    return {"status": "ok"}, 201


if __name__ == "__main__":
    app.run(port=5000, debug=True)
