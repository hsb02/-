from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 设置一个安全的密钥

# 初始化数据库
def init_db():
    conn = sqlite3.connect('educational.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS students
                 (student_id TEXT PRIMARY KEY, name TEXT, age INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS courses
                 (course_id TEXT PRIMARY KEY, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS scores
                 (student_id TEXT, course_id TEXT, score REAL,
                 FOREIGN KEY (student_id) REFERENCES students(student_id),
                 FOREIGN KEY (course_id) REFERENCES courses(course_id))''')
    conn.commit()
    conn.close()

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 修改登录界面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('educational.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="用户名或密码错误")
    return render_template('login.html')

# 添加登出功能
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# 修改主页路由
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# 修改其他路由，添加登录验证
@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        age = request.form['age']
        conn = sqlite3.connect('educational.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO students VALUES (?,?,?)", (student_id, name, age))
            conn.commit()
            message = f"学生 {name}（ID: {student_id}）已添加。"
        except sqlite3.IntegrityError:
            message = f"学生 ID {student_id} 已存在。"
        conn.close()
        return render_template('add_student.html', message=message)
    return render_template('add_student.html')

# 添加课程
@app.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        course_id = request.form['course_id']
        name = request.form['name']
        conn = sqlite3.connect('educational.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO courses VALUES (?,?)", (course_id, name))
            conn.commit()
            message = f"课程 {name}（ID: {course_id}）已添加。"
        except sqlite3.IntegrityError:
            message = f"课程 ID {course_id} 已存在。"
        conn.close()
        return render_template('add_course.html', message=message)
    return render_template('add_course.html')

# 添加成绩
@app.route('/add_score', methods=['GET', 'POST'])
@login_required
def add_score():
    if request.method == 'POST':
        student_id = request.form['student_id']
        course_id = request.form['course_id']
        score = request.form['score']
        conn = sqlite3.connect('educational.db')
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE student_id =?", (student_id,))
        student = c.fetchone()
        c.execute("SELECT * FROM courses WHERE course_id =?", (course_id,))
        course = c.fetchone()
        if student and course:
            try:
                c.execute("INSERT INTO scores VALUES (?,?,?)", (student_id, course_id, score))
                conn.commit()
                message = f"学生 {student[1]} 的课程 {course[1]} 成绩 {score} 已添加。"
            except sqlite3.IntegrityError:
                message = "该成绩记录已存在。"
        else:
            message = "学生或课程 ID 不存在。"
        conn.close()
        return render_template('add_score.html', message=message)
    conn = sqlite3.connect('educational.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    c.execute("SELECT * FROM courses")
    courses = c.fetchall()
    conn.close()
    return render_template('add_score.html', students=students, courses=courses)

# 查看学生课程成绩
@app.route('/show_student_courses', methods=['GET', 'POST'])
@login_required
def show_student_courses():
    if request.method == 'POST':
        student_id = request.form['student_id']
        conn = sqlite3.connect('educational.db')
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE student_id =?", (student_id,))
        student = c.fetchone()
        if student:
            c.execute("""SELECT courses.name, scores.score
                         FROM courses
                         JOIN scores ON courses.course_id = scores.course_id
                         WHERE scores.student_id =?""", (student_id,))
            courses = c.fetchall()
            return render_template('show_student_courses.html', student=student, courses=courses)
        else:
            message = f"学生 ID {student_id} 不存在。"
            return render_template('show_student_courses.html', message=message)
    conn = sqlite3.connect('educational.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    conn.close()
    return render_template('show_student_courses.html', students=students)

# 添加注册界面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('educational.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error="用户名已存在")
    return render_template('register.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    