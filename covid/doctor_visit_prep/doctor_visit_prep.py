from flask import Blueprint, render_template, request
import csv
import os


doctor_visit_prep_blueprint = Blueprint(
    "doctor_visit_prep_bp",
    __name__
)


CSV_FILE = os.path.join(
    os.path.dirname(__file__),
    "..",
    "adapters",
    "data",
    "doctor_visit_prep.csv"
)


@doctor_visit_prep_blueprint.route(
    "/doctor-visit-prep",
    methods=["GET", "POST"]
)
def doctor_visit_prep():

    if request.method == "POST":

        main_concern = request.form.get(
            "main_concern",
            ""
        )

        start_date = request.form.get(
            "start_date",
            ""
        )

        duration_frequency = request.form.get(
            "duration_frequency",
            ""
        )

        current_medications = request.form.get(
            "current_medications",
            ""
        )

        allergies = request.form.get(
            "allergies",
            ""
        )

        questions = request.form.get(
            "questions",
            ""
        )


        with open(
            CSV_FILE,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                main_concern,
                start_date,
                duration_frequency,
                current_medications,
                allergies,
                questions
            ])


        return render_template(
            "doctor_visit_prep/doctor_visit_prep.html",
            success=True
        )


    return render_template(
        "doctor_visit_prep/doctor_visit_prep.html",
        success=False
    )