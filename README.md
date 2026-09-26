# Health Companion

## Description

Health Companion is a web application built for the WINCSxDSAxMakers Club Hackathon, designed to help people keep track of their healthcare journey in one place. It was built using Python's Flask framework, with the Jinja templating library and WTForms handling forms and validation. The application uses Flask Blueprints to keep the authentication, appointment, doctor visit prep, medication tracking, and health timeline features cleanly separated. Data is stored using SQLite, with a Repository pattern used for the underlying application data (users, articles).

### Features

- **Accounts** — register and log in with a username and password (hashed, never stored in plain text), with a profile page for managing your details.
- **Log an Appointment** — record upcoming or past doctor visits, including doctor name, appointment type, date, time, and reason for the visit.
- **My Appointments** — view all your logged appointments in a monthly calendar view alongside a sortable list, with the ability to delete entries.
- **Doctor Visit Prep** — prepare for an appointment by noting your main concern, when it started, current medications, allergies, and questions to ask, all linked to a specific appointment.
- **Medication Tracker** — keep a record of medications, including dose, frequency, and start date, linked to the appointment that prescribed them.
- **Health Timeline** — log significant health events over time (symptoms, medications, doctor visits, test results) with severity ratings, to build a picture of your health history.

## Installation

**Installation via requirements.txt**

**Windows**

```
$ cd 2026-WINCSxDSAxMakers-Club-Hackathon
$ py -3 -m venv venv
$ venv\Scripts\activate
$ pip install -r requirements.txt
```

**MacOS**

```
$ cd 2026-WINCSxDSAxMakers-Club-Hackathon
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

When using PyCharm, set the virtual environment using 'File'->'Settings' and select 'Project:2026-WINCSxDSAxMakers-Club-Hackathon' from the left menu. Select 'Project Interpreter', click on the gearwheel button and select 'Add'. Click the 'Existing environment' radio button to select the virtual environment.

## Execution

**Running the application**

From the *2026-WINCSxDSAxMakers-Club-Hackathon* directory, and within the activated virtual environment (see *venv\Scripts\activate* above):

```
$ flask run
```

Once running, register an account and log in to start logging appointments and using the health tracking features.

## Configuration

The *2026-WINCSxDSAxMakers-Club-Hackathon/.env* file contains variable settings. They are set with appropriate values.

- `FLASK_APP`: Entry point of the application (should always be `wsgi.py`).
- `FLASK_ENV`: The environment in which to run the application (either `development` or `production`).
- `SECRET_KEY`: Secret key used to encrypt session data.
- `TESTING`: Set to False for running the application. Overridden and set to True automatically when testing the application.
- `WTF_CSRF_SECRET_KEY`: Secret key used by the WTForm library.

## Data storage

Appointments, doctor visit prep notes, medication entries, and health timeline events are stored in a local SQLite database (`instance/appointments.db`), created automatically the first time the app runs. User accounts are managed separately through the application's repository layer.

## Testing

After you have configured pytest as the testing tool for PyCharm (File - Settings - Tools - Python Integrated Tools - Testing), you can then run tests from within PyCharm by right clicking the tests folder and selecting "Run pytest in tests".

Alternatively, from a terminal in the root folder of the project, you can also call `python -m pytest tests` to run all the tests. PyCharm also provides a built-in terminal, which uses the configured virtual environment.

## Acknowledgements

This project began as a fork of the [CS235 Sample Web App (COVID News Portal)](https://github.com/UoA-CS-Project-CS235-S2-2026/CS235-SampleWebApp-CovidNewsPortal), whose authentication system and application architecture (Flask Blueprints, Repository pattern) were adapted and extended to build Health Companion.
