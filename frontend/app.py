"""NutriFit AI — Flask frontend.

Serves Jinja2 pages and proxies image/audio media from the FastAPI backend.
Communication with the backend is done from the browser via JS fetch() calls
(see static/js/main.js).
"""
from __future__ import annotations

import os

from flask import Flask, redirect, render_template, url_for


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["BACKEND_URL"] = BACKEND_URL

    @app.context_processor
    def inject_globals() -> dict:
        return {"BACKEND_URL": BACKEND_URL, "APP_NAME": "NutriFit AI"}

    # ------------------- public pages -------------------
    @app.route("/")
    def landing():
        return render_template("landing.html")

    @app.route("/login")
    def login():
        return render_template("login.html")

    @app.route("/register")
    def register():
        return render_template("register.html")

    @app.route("/logout")
    def logout():
        return redirect(url_for("landing"))

    # ------------------- authenticated pages -------------------
    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/meal-scan")
    def meal_scan():
        return render_template("meal_scan.html")

    @app.route("/rag-chat")
    def rag_chat():
        return render_template("rag_chat.html")

    @app.route("/dieticians")
    def dieticians():
        return render_template("dieticians.html")

    @app.route("/consultations")
    def consultations():
        return render_template("consultation.html")

    @app.route("/activity")
    def activity():
        return render_template("activity_log.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
