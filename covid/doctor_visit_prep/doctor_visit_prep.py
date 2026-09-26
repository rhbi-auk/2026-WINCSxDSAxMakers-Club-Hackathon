from pathlib import Path
import sqlite3

from flask import Blueprint, abort, current_app, redirect, render_template, request, session, url_for

from covid.authentication.authentication import login_required

doctor_visit_prep_blueprint = Blueprint(
    "doctor_visit_prep_bp",
    __name__
)

@doctor_visit_prep_blueprint.route(
    "/doctor-visit-prep",
    methods=["GET", "POST"]
)
@login_required
def doctor_visit_prep():
    db_path = Path(current_app.instance_path) / "appointments.db"
    field_names = (
        "main_concern",
        "start_date",
        "duration_frequency",
        "current_medications",
        "allergies",
        "questions"
    )
    error = None
    success = False
    appointment_id = request.args.get("appointment_id", type=int)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        appointments = conn.execute(
            "SELECT * FROM appointments WHERE owner_user_name = ? ORDER BY appointment_date DESC, appointment_time DESC",
            (session["user_name"],)
        ).fetchall()

        if request.method == "POST":
            try:
                appointment_id = int(request.form.get("appointment_id", ""))
            except ValueError:
                appointment_id = None

        appointment = next(
            (item for item in appointments if item["id"] == appointment_id),
            None
        )
        if appointment_id is not None and appointment is None:
            abort(404)

        existing_notes = None
        if appointment is not None:
            existing_notes = conn.execute(
                "SELECT * FROM appointment_preparation WHERE appointment_id = ?",
                (appointment_id,)
            ).fetchone()

        prep_notes = {
            field: existing_notes[field] if existing_notes else ""
            for field in field_names
        }

        if request.method == "POST":
            if appointment is None:
                error = "Select an appointment to link these notes to."
            else:
                prep_notes = {
                    field: request.form.get(field, "").strip()
                    for field in field_names
                }
                if not prep_notes["main_concern"] or not prep_notes["start_date"]:
                    error = "Please complete the main concern and start date."
                else:
                    conn.execute("""
                        INSERT INTO appointment_preparation (
                            appointment_id,
                            main_concern,
                            start_date,
                            duration_frequency,
                            current_medications,
                            allergies,
                            questions
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(appointment_id) DO UPDATE SET
                            main_concern = excluded.main_concern,
                            start_date = excluded.start_date,
                            duration_frequency = excluded.duration_frequency,
                            current_medications = excluded.current_medications,
                            allergies = excluded.allergies,
                            questions = excluded.questions
                    """, (
                        appointment_id,
                        prep_notes["main_concern"],
                        prep_notes["start_date"],
                        prep_notes["duration_frequency"],
                        prep_notes["current_medications"],
                        prep_notes["allergies"],
                        prep_notes["questions"]
                    ))
                    success = True

    return render_template(
        "doctor_visit_prep/doctor_visit_prep.html",
        appointments=appointments,
        appointment=appointment,
        prep_notes=prep_notes,
        success=success,
        error=error
    )