from flask import Flask, jsonify

from config import HOST, PORT, DEBUG
from db import ensure_indexes
from routes.auth import auth_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(auth_bp)

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Ruta no encontrada"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({"error": "Método no permitido"}), 405

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": "Error interno del servidor"}), 500

    ensure_indexes()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
