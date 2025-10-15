from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date
from datetime import datetime
from typing import Optional

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///duty.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    rank = db.Column(db.String(50), nullable=True)  # Optional

class Duty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    duty_date = db.Column(db.Date, nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    day_off_given = db.Column(db.Boolean, default=False)
    day_off_date = db.Column(db.Date, nullable=True)
    honorary = db.Column(db.Boolean, default=False)
    staff = db.relationship('Staff', backref=db.backref('duties', lazy=True))
    description = db.Column(db.Text, default="")

@app.before_request
def create_tables():
    db.create_all()

@app.route('/staff')
def staff():
    order_by = request.args.get('order_by', 'name')
    if order_by == 'rank':
        staff = Staff.query.order_by(Staff.rank, Staff.name).all()
    else:  # default: order by name
        staff = Staff.query.order_by(Staff.name).all()
    return render_template('staff.html', staff=staff, order_by=order_by)


@app.route('/add_staff', methods=['POST'])
def add_staff():
    name = request.form['name']
    rank = request.form.get('rank', '')
    db.session.add(Staff(name=name, rank=rank))
    db.session.commit()
    return redirect(url_for('staff'))

# Edit staff
@app.route('/edit_staff/<int:staff_id>', methods=['GET', 'POST'])
def edit_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    if request.method == 'POST':
        staff.name = request.form['name']
        staff.rank = request.form.get('rank', '')
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit_staff.html', staff=staff)

# Delete staff
@app.route('/delete_staff/<int:staff_id>', methods=['POST'])
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    # Optionally: Also delete all duties for this staff (cascade)
    Duty.query.filter_by(staff_id=staff_id).delete()
    db.session.delete(staff)
    db.session.commit()
    return redirect(url_for('staff'))

@app.route('/staff/<int:staff_id>/duties')
def staff_duties(staff_id):
    staff_member = Staff.query.get_or_404(staff_id)
    duties = Duty.query.filter_by(staff_id=staff_id).order_by(Duty.duty_date.desc()).all()
    order_by = request.args.get('order_by', 'date')
    if order_by == 'off':
        duties = sorted(duties, key=lambda d: (not d.day_off_given, d.duty_date))
    elif order_by == 'honorary':
        duties = sorted(duties, key=lambda d: (not d.honorary, d.duty_date))
    else:
        duties = sorted(duties, key=lambda d: d.duty_date)
    return render_template('staff_duties.html', staff=staff_member, duties=duties, order_by=order_by)


@app.route('/duties')
def duties():
    month = request.args.get('month')
    staff_list = Staff.query.order_by(Staff.rank, Staff.name).all()
    staff_dict = {s.id: s for s in staff_list}

    # Get all duties, or filter by selected month
    duties_query = Duty.query
    if month:
        y, m = map(int, month.split('-'))
        duties_query = duties_query.filter(
            db.extract('year', Duty.duty_date) == y,
            db.extract('month', Duty.duty_date) == m
        )
    duties = duties_query.order_by(Duty.duty_date.asc()).all()

    # Gather all months in use, as ("2025-07", "Ιούλιος 2025") pairs
    all_dates = Duty.query.with_entities(Duty.duty_date).all()
    months = sorted({
        (
            f"{d.duty_date.year}-{d.duty_date.month:02d}",
            f"{['Ιανουάριος','Φεβρουάριος','Μάρτιος','Απρίλιος','Μάιος','Ιούνιος','Ιούλιος','Αύγουστος','Σεπτέμβριος','Οκτώβριος','Νοέμβριος','Δεκέμβριος'][d.duty_date.month-1]} {d.duty_date.year}"
        )
        for d in all_dates
    }, reverse=True)

    return render_template(
        'duties.html',
        duties=duties,
        staff=staff_dict,
        months=months,
        selected_month=month
    )


@app.route('/add_duty', methods=['GET', 'POST'])
def add_duty():
    staff_list = Staff.query.order_by(Staff.rank, Staff.name).all()

    if request.method == 'POST':
        redirect_target: Optional[str] = request.form.get('next')
        duty_date_str = request.form['duty_date']
        staff_id = int(request.form['staff_id'])
        day_off_given = 'day_off_given' in request.form
        day_off_date_str = request.form.get('day_off_date') or None
        honorary = 'honorary' in request.form
        description = request.form.get('description', '').strip()

        # Convert strings to date objects
        duty_date = datetime.strptime(duty_date_str, '%d/%m/%Y').date()
        day_off_date = None
        if day_off_date_str:
            day_off_date = datetime.strptime(day_off_date_str, '%d/%m/%Y').date()

        db.session.add(Duty(
            duty_date=duty_date,
            staff_id=staff_id,
            day_off_given=day_off_given,
            honorary=honorary,
            day_off_date=day_off_date,
            description=description
        ))
        db.session.commit()
        if redirect_target:
            return redirect(redirect_target)
        return redirect(url_for('duties'))

    selected_staff_id: Optional[str] = request.args.get('staff_id')
    next_url: Optional[str] = request.args.get('next')
    return render_template(
        'add_duty.html',
        staff_list=staff_list,
        selected_staff_id=selected_staff_id,
        next_url=next_url
    )

# Edit duty
@app.route('/edit_duty/<int:duty_id>', methods=['GET', 'POST'])
def edit_duty(duty_id):
    duty = Duty.query.get_or_404(duty_id)
    staff_list = Staff.query.order_by(Staff.rank, Staff.name).all()
    staff_dict = {s.id: s for s in staff_list}
    if request.method == 'POST':
        next_url: Optional[str] = request.form.get('next')
        duty.duty_date = datetime.strptime(request.form['duty_date'], '%d/%m/%Y').date()
        duty.staff_id = int(request.form['staff_id'])
        duty.honorary = 'honorary' in request.form
        duty.day_off_given = 'day_off_given' in request.form
        duty.description = request.form.get('description', '').strip()
        day_off_date_str = request.form.get('day_off_date', '').strip()
        if day_off_date_str:
            duty.day_off_date = datetime.strptime(day_off_date_str, '%d/%m/%Y').date()
        else:
            duty.day_off_date = None
        db.session.commit()
        if next_url:
            return redirect(next_url)
        return redirect(url_for('duties'))
    next_url: Optional[str] = request.args.get('next')
    return render_template('edit_duty.html', duty=duty, staff=staff_dict, staff_list=staff_list, selected_staff_id=duty.staff_id, next_url=next_url)

# Delete duty
@app.route('/delete_duty/<int:duty_id>', methods=['POST'])
def delete_duty(duty_id):
    duty = Duty.query.get_or_404(duty_id)
    redirect_target: Optional[str] = request.form.get('next')
    db.session.delete(duty)
    db.session.commit()
    if redirect_target:
        return redirect(redirect_target)
    return redirect(url_for('duties'))


@app.route('/')
def index():
    staff = Staff.query.all()
    duties = Duty.query.all()
    order_by = request.args.get('order_by', 'name')

    # 1. Calculate pending and received days off first!
    pending_days_off = {s.id: 0 for s in staff}
    received_days_off = {s.id: 0 for s in staff}

    for duty in duties:
        if not duty.day_off_given:
            pending_days_off[duty.staff_id] += 1
        if duty.day_off_date:
            received_days_off[duty.staff_id] += 1

    # 2. Now build staff_with_pending based on correct numbers
    staff_with_pending = [s for s in staff if pending_days_off[s.id] > 0]

    # 3. Sort
    if order_by == 'rank':
        staff = sorted(staff, key=lambda s: (s.rank or '', s.name or ''))
    elif order_by == 'pending':
        staff = sorted(staff, key=lambda s: (-pending_days_off[s.id], s.name or ''))
    elif order_by == 'received':
        staff = sorted(staff, key=lambda s: (-received_days_off[s.id], s.name or ''))
    else:
        staff = sorted(staff, key=lambda s: (s.name or '', s.rank or ''))

    return render_template(
        'index.html',
        staff=staff,
        staff_with_pending=staff_with_pending,
        pending_days_off=pending_days_off,
        received_days_off=received_days_off,
        order_by=order_by
    )


def greek_date_fmt(dt):
    if not dt:
        return ''
    # Greek day and month names
    days = ['Δευτέρα', 'Τρίτη', 'Τετάρτη', 'Πέμπτη', 'Παρασκευή', 'Σάββατο', 'Κυριακή']
    months = [
        'Ιανουαρίου', 'Φεβρουαρίου', 'Μαρτίου', 'Απριλίου', 'Μαίου', 'Ιουνίου',
        'Ιουλίου', 'Αυγούστου', 'Σεπτεμβρίου', 'Οκτωβρίου', 'Νοεμβρίου', 'Δεκεμβρίου'
    ]
    # dt.weekday() -> 0 is Monday, 6 is Sunday
    day_name = days[dt.weekday()]
    month_name = months[dt.month - 1]
    return f"{day_name}, {dt.day:02d} {month_name} {dt.year}"

def date_ddmmyyyy(dt):
    return dt.strftime('%d/%m/%Y') if dt else ''

app.jinja_env.globals['date_ddmmyyyy'] = date_ddmmyyyy
app.jinja_env.globals['greek_date_fmt'] = greek_date_fmt

if __name__ == '__main__':
    import threading
    import webbrowser


    # Start Flask in a thread so browser opens instantly
    def run_app():
        app.run(debug=False, use_reloader=False)

    threading.Thread(target=run_app).start()
    webbrowser.open('http://localhost:5000')

