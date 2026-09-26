"""Initialise Flask app."""

from pathlib import Path
from datetime import date, time
import sqlite3

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort
)

import covid.adapters.repository as repo
from covid.adapters.memory_repository import (
    MemoryRepository,
    populate
)


def create_app(test_config=None):
    """Construct the core application."""

    # -------------------------------------------------
    # Create Flask application
    # -------------------------------------------------

    app = Flask(__name__)

    # Load configuration
    app.config.from_object("config.Config")

    data_path = Path("covid") / "adapters" / "data"

    if test_config is not None:
        app.config.from_mapping(test_config)
        data_path = app.config["TEST_DATA_PATH"]

    # -------------------------------------------------
    # Initialise repository
    # -------------------------------------------------

    repo.repo_instance = MemoryRepository()

    populate(
        data_path,
        repo.repo_instance
    )

    with app.app_context():

        # =================================================
        # BLUEPRINTS
        # =================================================

        # Home
        from .home import home

        app.register_blueprint(
            home.home_blueprint
        )

        # News
        from .news import news

        app.register_blueprint(
            news.news_blueprint
        )

        # Authentication
        from .authentication import authentication

        app.register_blueprint(
            authentication.authentication_blueprint
        )

        # Utilities
        from .utilities import utilities

        app.register_blueprint(
            utilities.utilities_blueprint
        )

        # Doctor Visit Prep
        from .doctor_visit_prep import doctor_visit_prep

        app.register_blueprint(
            doctor_visit_prep.doctor_visit_prep_blueprint
        )

        # =================================================
        # DATABASE
        # =================================================

        db_path = (
            Path(app.instance_path)
            / "appointments.db"
        )

        db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with sqlite3.connect(db_path) as conn:

            # ---------------------------------------------
            # Appointments
            # ---------------------------------------------

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_name TEXT NOT NULL,
                    appointment_type TEXT NOT NULL,
                    appointment_date TEXT NOT NULL,
                    appointment_time TEXT NOT NULL,
                    reason TEXT,
                    status TEXT NOT NULL DEFAULT 'Pending'
                )
                """
            )

            columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(appointments)"
                )
            }

            if (
                "patient_name" in columns
                and "doctor_name" not in columns
            ):
                conn.execute(
                    """
                    ALTER TABLE appointments
                    RENAME COLUMN patient_name
                    TO doctor_name
                    """
                )

            # ---------------------------------------------
            # Doctor Visit Preparation
            # ---------------------------------------------

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS appointment_preparation (
                    appointment_id INTEGER PRIMARY KEY,

                    main_concern TEXT NOT NULL,

                    start_date TEXT NOT NULL,

                    duration_frequency TEXT
                        NOT NULL DEFAULT '',

                    current_medications TEXT
                        NOT NULL DEFAULT '',

                    allergies TEXT
                        NOT NULL DEFAULT '',

                    questions TEXT
                        NOT NULL DEFAULT '',

                    FOREIGN KEY (appointment_id)
                        REFERENCES appointments(id)
                )
                """
            )

        # =================================================
        # LOG APPOINTMENT
        # =================================================

        @app.route(
            "/appointment/log",
            methods=["GET", "POST"]
        )
        def log_appointment():

            if request.method == "GET":

                return render_template(
                    "appointment/log.html"
                )

            doctor_name = request.form.get(
                "doctor_name",
                ""
            ).strip()

            appointment_type = request.form.get(
                "appointment_type",
                ""
            ).strip()

            appointment_date = request.form.get(
                "appointment_date",
                ""
            ).strip()

            appointment_time = request.form.get(
                "appointment_time",
                ""
            ).strip()

            reason = request.form.get(
                "reason",
                ""
            ).strip()

            # Required fields
            if not all([
                doctor_name,
                appointment_type,
                appointment_date,
                appointment_time
            ]):

                return (
                    "Please complete all required fields.",
                    400
                )

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

            try:

                selected_date = date.fromisoformat(
                    appointment_date
                )

                selected_time = time.fromisoformat(
                    appointment_time
                )

            except ValueError:

                return (
                    "Invalid date or time.",
                    400
                )

            with sqlite3.connect(db_path) as conn:

                conn.execute(
                    """
                    INSERT INTO appointments (
                        doctor_name,
                        appointment_type,
                        appointment_date,
                        appointment_time,
                        reason
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        doctor_name,
                        appointment_type,
                        selected_date.isoformat(),
                        selected_time.isoformat(
                            timespec="minutes"
                        ),
                        reason
                    )
                )

            return render_template(
                "appointment/log.html",
                success=True
            )

        # =================================================
        # MY APPOINTMENTS
        # =================================================

        @app.route(
            "/appointment/my"
        )
        def my_appointments():

            sort_by = request.args.get(
                "sort",
                "date"
            )

            sort_orders = {

                "date":
                    "appointment_date DESC, "
                    "appointment_time DESC",

                "date_oldest":
                    "appointment_date ASC, "
                    "appointment_time ASC",

                "doctor":
                    "doctor_name COLLATE NOCASE ASC, "
                    "appointment_date DESC, "
                    "appointment_time DESC"
            }

            if sort_by not in sort_orders:
                sort_by = "date"

            with sqlite3.connect(db_path) as conn:

                conn.row_factory = sqlite3.Row

                appointments = conn.execute(
                    f"""
                    SELECT
                        appointments.*,

                        EXISTS (
                            SELECT 1
                            FROM appointment_preparation
                            WHERE
                                appointment_preparation.appointment_id
                                = appointments.id
                        ) AS has_prep

                    FROM appointments

                    ORDER BY
                        {sort_orders[sort_by]}
                    """
                ).fetchall()

            return render_template(
                "appointment/my_appointments.html",
                appointments=appointments,
                sort_by=sort_by
            )

        # =================================================
        # DOCTOR VISIT PREP
        # =================================================

        @app.route(
            "/appointment/<int:appointment_id>/prep",
            methods=["GET", "POST"]
        )
        def appointment_visit_prep(
            appointment_id
        ):

            field_names = (
                "main_concern",
                "start_date",
                "duration_frequency",
                "current_medications",
                "allergies",
                "questions"
            )

            success = False

            with sqlite3.connect(db_path) as conn:

                conn.row_factory = sqlite3.Row

                appointment = conn.execute(
                    """
                    SELECT *
                    FROM appointments
                    WHERE id = ?
                    """,
                    (
                        appointment_id,
                    )
                ).fetchone()

                if appointment is None:
                    abort(404)

                existing_notes = conn.execute(
                    """
                    SELECT *
                    FROM appointment_preparation
                    WHERE appointment_id = ?
                    """,
                    (
                        appointment_id,
                    )
                ).fetchone()

                prep_notes = {
                    field:
                        existing_notes[field]
                        if existing_notes
                        else ""

                    for field in field_names
                }

                if request.method == "POST":

                    prep_notes = {
                        field:
                            request.form.get(
                                field,
                                ""
                            ).strip()

                        for field in field_names
                    }

                    if (
                        not prep_notes["main_concern"]
                        or
                        not prep_notes["start_date"]
                    ):

                        return render_template(
                            "doctor_visit_prep/"
                            "doctor_visit_prep.html",

                            appointment=appointment,

                            prep_notes=prep_notes,

                            error=(
                                "Please complete the "
                                "main concern and start date."
                            )
                        ), 400

                    conn.execute(
                        """
                        INSERT INTO appointment_preparation (
                            appointment_id,
                            main_concern,
                            start_date,
                            duration_frequency,
                            current_medications,
                            allergies,
                            questions
                        )

                        VALUES (?, ?, ?, ?, ?, ?, ?)

                        ON CONFLICT(appointment_id)

                        DO UPDATE SET
                            main_concern =
                                excluded.main_concern,

                            start_date =
                                excluded.start_date,

                            duration_frequency =
                                excluded.duration_frequency,

                            current_medications =
                                excluded.current_medications,

                            allergies =
                                excluded.allergies,

                            questions =
                                excluded.questions
                        """,
                        (
                            appointment_id,

                            prep_notes[
                                "main_concern"
                            ],

                            prep_notes[
                                "start_date"
                            ],

                            prep_notes[
                                "duration_frequency"
                            ],

                            prep_notes[
                                "current_medications"
                            ],

                            prep_notes[
                                "allergies"
                            ],

                            prep_notes[
                                "questions"
                            ]
                        )
                    )

                    success = True

            return render_template(
                "doctor_visit_prep/"
                "doctor_visit_prep.html",

                appointment=appointment,

                prep_notes=prep_notes,

                success=success
            )

        # =================================================
        # DELETE APPOINTMENT
        # =================================================

        @app.route(
            "/appointment/<int:appointment_id>/delete",
            methods=["POST"]
        )
        def delete_appointment(
            appointment_id
        ):

            with sqlite3.connect(db_path) as conn:

                conn.execute(
                    """
                    DELETE FROM appointment_preparation
                    WHERE appointment_id = ?
                    """,
                    (
                        appointment_id,
                    )
                )

                conn.execute(
                    """
                    DELETE FROM appointments
                    WHERE id = ?
                    """,
                    (
                        appointment_id,
                    )
                )

            return redirect(
                url_for(
                    "my_appointments"
                )
            )

        # =================================================
        # HEALTH TIMELINE
        # =================================================

        @app.route(
            "/health-timeline",
            methods=["GET", "POST"]
        )
        def health_timeline():

            success = False

            timeline_data = {
                "event_date": "",
                "event_type": "",
                "description": "",
                "severity": "",
                "notes": ""
            }

            if request.method == "POST":

                timeline_data = {

                    "event_date":
                        request.form.get(
                            "event_date",
                            ""
                        ).strip(),

                    "event_type":
                        request.form.get(
                            "event_type",
                            ""
                        ).strip(),

                    "description":
                        request.form.get(
                            "description",
                            ""
                        ).strip(),

                    "severity":
                        request.form.get(
                            "severity",
                            ""
                        ).strip(),

                    "notes":
                        request.form.get(
                            "notes",
                            ""
                        ).strip()
                }

                success = True

            return render_template(
                "timeline/health_timeline.html",
                success=success,
                timeline_data=timeline_data,
                events=[]
            )

        # =================================================
        # MEDICATION TRACKER
        # =================================================

        @app.route(
            "/medication/tracker",
            methods=["GET", "POST"]
        )
        def medication_tracker():

            success = False

            # Empty values when page is first opened
            medication_data = {

                "medicine_name": "",

                "dose": "",

                "frequency": "",

                "medication_time": "",

                "start_date": "",

                "notes": ""
            }

            # ---------------------------------------------
            # POST
            # ---------------------------------------------

            if request.method == "POST":

                medication_data = {

                    "medicine_name":
                        request.form.get(
                            "medicine_name",
                            ""
                        ).strip(),

                    "dose":
                        request.form.get(
                            "dose",
                            ""
                        ).strip(),

                    "frequency":
                        request.form.get(
                            "frequency",
                            ""
                        ).strip(),

                    "medication_time":
                        request.form.get(
                            "medication_time",
                            ""
                        ).strip(),

                    "start_date":
                        request.form.get(
                            "start_date",
                            ""
                        ).strip(),

                    "notes":
                        request.form.get(
                            "notes",
                            ""
                        ).strip()
                }

                success = True

            return render_template(
                "medication/tracker.html",

                success=success,

                medication_data=medication_data
            )

    return app