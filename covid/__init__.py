
"""Initialise Flask app."""

from pathlib import Path
from datetime import date, time
import sqlite3

from flask import Flask, render_template, request

import covid.adapters.repository as repo
from covid.adapters.memory_repository import MemoryRepository, populate


def create_app(test_config=None):
    """Construct the core application."""

    # Create Flask application
    app = Flask(__name__)

    # Load configuration
    app.config.from_object("config.Config")

    data_path = Path("covid") / "adapters" / "data"

    if test_config is not None:
        app.config.from_mapping(test_config)
        data_path = app.config["TEST_DATA_PATH"]

    # Initialise repository
    repo.repo_instance = MemoryRepository()

    populate(data_path, repo.repo_instance)

    with app.app_context():

        # Register home blueprint
        from .home import home
        app.register_blueprint(home.home_blueprint)

        # Register news blueprint
        from .news import news
        app.register_blueprint(news.news_blueprint)

        # Register authentication blueprint
        from .authentication import authentication
        app.register_blueprint(
            authentication.authentication_blueprint
        )

        # Register utilities blueprint
        from .utilities import utilities
        app.register_blueprint(
            utilities.utilities_blueprint
        )

        # --------------------------------
        # Appointment database
        # --------------------------------

        db_path = Path(app.instance_path) / "appointments.db"

        db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Create appointments table
        with sqlite3.connect(db_path) as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_name TEXT NOT NULL,
                    appointment_type TEXT NOT NULL,
                    appointment_date TEXT NOT NULL,
                    appointment_time TEXT NOT NULL,
                    reason TEXT,
                    status TEXT NOT NULL DEFAULT 'Pending'
                )
            """)
        # Create health timeline table
        with sqlite3.connect(db_path) as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_date TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT,
                    notes TEXT
                )
            """)
        # --------------------------------
        # Book appointment
        # --------------------------------

        @app.route(
            "/appointment/book",
            methods=["GET", "POST"]
        )
        def book_appointment():

            # Display booking page
            if request.method == "GET":

                return render_template(
                    "appointment/book.html"
                )

            # Get submitted form data
            patient_name = request.form.get(
                "patient_name", ""
            ).strip()

            appointment_type = request.form.get(
                "appointment_type", ""
            ).strip()

            appointment_date = request.form.get(
                "appointment_date", ""
            ).strip()

            appointment_time = request.form.get(
                "appointment_time", ""
            ).strip()

            reason = request.form.get(
                "reason", ""
            ).strip()

            # Check required fields
            if not all([
                patient_name,
                appointment_type,
                appointment_date,
                appointment_time
            ]):

                return (
                    "Please complete all required fields.",
                    400
                )

            # Validate appointment type
            allowed_types = {
                "General consultation",
                "Follow-up visit",
                "Health check-up",
                "Other"
            }

            if appointment_type not in allowed_types:

                return (
                    "Invalid appointment type.",
                    400
                )

            # Validate date and time
            try:

                selected_date = date.fromisoformat(
                    appointment_date
                )

                selected_time = time.fromisoformat(
                    appointment_time
                )

                if selected_date < date.today():

                    return (
                        "Please select today or a future date.",
                        400
                    )

            except ValueError:

                return (
                    "Invalid date or time.",
                    400
                )

            # Save appointment to SQLite
            with sqlite3.connect(db_path) as conn:

                conn.execute(
                    """
                    INSERT INTO appointments (
                        patient_name,
                        appointment_type,
                        appointment_date,
                        appointment_time,
                        reason
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        patient_name,
                        appointment_type,
                        selected_date.isoformat(),
                        selected_time.isoformat(
                            timespec="minutes"
                        ),
                        reason
                    )
                )

            # Show success message
            return render_template(
                "appointment/book.html",
                success=True
            )

        # My Appointments page
        @app.route("/appointment/my")
        def my_appointments():

            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row

                appointments = conn.execute("""
                    SELECT *
                    FROM appointments
                    ORDER BY appointment_date DESC
                """).fetchall()

            return render_template(
                "appointment/my_appointments.html",
                appointments=appointments
            )
    # --------------------------------
    # Health Timeline
    # --------------------------------

    @app.route(
        "/health-timeline",
        methods=["GET", "POST"]
    )
    def health_timeline():

        if request.method == "POST":

            event_date = request.form.get(
                "event_date", ""
            ).strip()

            event_type = request.form.get(
                "event_type", ""
            ).strip()

            description = request.form.get(
                "description", ""
            ).strip()

            severity = request.form.get(
                "severity", ""
            ).strip()

            notes = request.form.get(
                "notes", ""
            ).strip()

            if event_date and event_type and description:

                with sqlite3.connect(db_path) as conn:
                    conn.execute(
                        """
                        INSERT INTO health_events (
                            event_date,
                            event_type,
                            description,
                            severity,
                            notes
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            event_date,
                            event_type,
                            description,
                            severity,
                            notes
                        )
                    )

        with sqlite3.connect(db_path) as conn:

            conn.row_factory = sqlite3.Row

            events = conn.execute(
                """
                SELECT *
                FROM health_events
                ORDER BY event_date DESC, id DESC
                """
            ).fetchall()

        return render_template(
            "timeline/health_timeline.html",
            events=events
        )
    return app
