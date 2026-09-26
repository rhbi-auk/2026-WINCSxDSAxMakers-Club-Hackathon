from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for
)


appointment_blueprint = Blueprint(
    'appointment_bp',
    __name__,
    url_prefix='/appointment'
)


@appointment_blueprint.route('/book', methods=['GET', 'POST'])
def book():

    if request.method == 'POST':

        appointment = {
            'user_name': session.get('user_name', 'Guest'),
            'appointment_type': request.form.get('appointment_type'),
            'doctor': request.form.get('doctor'),
            'date': request.form.get('date'),
            'time': request.form.get('time'),
            'reason': request.form.get('reason'),
            'status': 'Pending'
        }

        # 取出以前保存的预约
        appointments = session.get('appointments', [])

        # 添加新的预约
        appointments.append(appointment)

        # 保存回 session
        session['appointments'] = appointments
        session.modified = True

        # 预约成功后直接进入 My Appointments
        return redirect(
            url_for('appointment_bp.my_appointments')
        )

    return render_template(
        'appointment/book.html'
    )


@appointment_blueprint.route('/my')
def my_appointments():

    appointments = session.get('appointments', [])

    return render_template(
        'appointment/my.html',
        appointments=appointments
    )