from datetime import date, timedelta,datetime
from flask import Flask, render_template, redirect, request, session
import mysql.connector
import plotly.graph_objects as go


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key for session management

db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='G17_db'
)
cursor = db.cursor()


@app.route('/')
def home():
    return render_template('login.html')


@app.route('/login',  methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            "SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = user[1]
            return redirect('/dashboard')
        else:
            error_message = "Invalid credentials. Please try again."
            return render_template('login.html', error_message=error_message)


@app.route('/dashboard')
def dashboard():
    select_query = "SELECT a.student_id, s.name, a.checkin_datetime, IFNULL(a.checkout_datetime, 'Not checked out yet') FROM attendance a INNER JOIN students s ON a.student_id = s.student_id ORDER BY a.checkin_datetime DESC LIMIT 10"
    cursor.execute(select_query)
    records2 = cursor.fetchall()
    
    
    # Count total students
    total_students_query = "SELECT COUNT(*) FROM students"
    cursor.execute(total_students_query)
    total_students = cursor.fetchone()[0]

    # Count today's attendance
    today = date.today().strftime("%Y-%m-%d")
    today_attendance_query = "SELECT COUNT(*) FROM attendance WHERE DATE(checkin_datetime) = %s"
    cursor.execute(today_attendance_query, (today,))
    today_attendance = cursor.fetchone()[0]

    # Count monthly attendance
    first_day_of_month = date.today().replace(day=1).strftime("%Y-%m-%d")
    monthly_attendance_query = "SELECT COUNT(*) FROM attendance WHERE DATE(checkin_datetime) >= %s"
    cursor.execute(monthly_attendance_query, (first_day_of_month,))
    monthly_attendance = cursor.fetchone()[0]

    # Count weekly attendance
    start_of_week = (date.today() - timedelta(days=date.today().weekday())).strftime("%Y-%m-%d")
    weekly_attendance_query = "SELECT COUNT(*) FROM attendance WHERE DATE(checkin_datetime) >= %s"
    cursor.execute(weekly_attendance_query, (start_of_week,))
    weekly_attendance = cursor.fetchone()[0]
    
    
    attendance_data = []
    today = date.today()
    for i in range(30):
        current_date = today - timedelta(days=i)
        attendance_query = "SELECT COUNT(*) FROM attendance WHERE DATE(checkin_datetime) = %s"
        cursor.execute(attendance_query, (current_date,))
        attendance_count = cursor.fetchone()[0]
        attendance_data.append((current_date, attendance_count))


    # Create the attendance graph
    dates = [data[0] for data in attendance_data]
    counts = [data[1] for data in attendance_data]
    fig = go.Figure(data=go.Bar(x=dates, y=counts))
    fig.update_layout(title='Daily Attendance in the Past 30 Days', xaxis_title='Date', yaxis_title='Attendance Count')

    graph_html = fig.to_html(full_html=False)


    attendance_data1 = []
    today1 = date.today()
    for i in range(7):
        start_of_week = today1 - timedelta(weeks=i, days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        attendance_query = "SELECT COUNT(*) FROM attendance WHERE DATE(checkin_datetime) BETWEEN %s AND %s"
        cursor.execute(attendance_query, (start_of_week, end_of_week))
        attendance_count = cursor.fetchone()[0]
        attendance_data1.append((start_of_week, end_of_week, attendance_count))


    # Create the attendance pie chart
    labels = [f"Week {i+1}" for i in range(7)]
    values = [data[2] for data in attendance_data1]
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    fig.update_layout(title='Weekly Attendance in the Past 7 Weeks')

    graph_pie = fig.to_html(full_html=False)
    
    return render_template('dashboard.html', state='dashboard',records2=records2, total_students=total_students, today_attendance=today_attendance, monthly_attendance=monthly_attendance, weekly_attendance=weekly_attendance, graph_html=graph_html,graph_pie=graph_pie)


@app.route('/studentregistration', methods=['GET', 'POST'])
def studentregistration():
    message = ''
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        contact_details = request.form['contact_details']

        insert_query = "INSERT INTO students (student_id, name, contact_details) VALUES (%s, %s, %s)"
        data = (student_id, name, contact_details)
        cursor.execute(insert_query, data)
        db.commit()

        message = 'Student registered successfully!'

    return render_template('dashboard.html', state='studentregistration', message=message)


if __name__ == '__main__':
    app.run(debug=True)
