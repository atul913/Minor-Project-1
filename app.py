from flask import Flask, jsonify, render_template, request, url_for, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash 
from datetime import timedelta, datetime, timezone
import mysql.connector
from authlib.integrations.flask_client import OAuth
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'haetlullo'

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['UPLOAD_FOLDER1'] = 'uploads'

app.config['SERVER_NAME'] = 'localhost:5000'
oauth = OAuth(app)

@app.route('/google/<user>')
def google(user):
    load_dotenv()
    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

    session['user_type'] = user  # Store user type in session
    
    oauth.register(
        name='google',
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    # Redirect to google_auth function
    redirect_uri = url_for('callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)



@app.route('/callback')
def callback():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')  # contains email, name, etc.
    user_type = session.get('user_type')  # Retrieve user type from session

    if not user_info:
        return "Failed to fetch user info from Google", 400

    email = user_info['email']
    name = user_info.get('name', 'No Name')
    password = name.split()[0].lower() + '1234'

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Check if user exists in learner table
    cursor.execute(f"SELECT * FROM {user_type}_signup WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        
        if user_type == 'instructor':
            session['instructor_id'] = user['id']
        else:
            session['learner_id'] = user['id']
        
    else:
        cursor.execute(
            f"INSERT INTO {user_type}_signup (username, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)  # password None for OAuth users
        )
        conn.commit()
        user_id = cursor.lastrowid
        if user_type == 'instructor':

            session['instructor_id'] = user_id
        else:      
            cursor.execute(
                'INSERT INTO student_detail (id, name, email, enrollment, course, dob, cn, college) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (user_id, name, email, '', '', '', '', ''))
        
            session['learner_id'] =   user_id
        # Optional: insert into student_detail table

        conn.commit()

    cursor.close()
    conn.close()

    # Redirect to learner dashboard
    return redirect(url_for(f'{user_type}_dashboard'))



def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Root@9131",
        database="skillforge"
    )

# ---------------- REGISTER ----------------
@app.route('/register/<user>', methods=['POST', 'GET'])
def register(user):
    if request.method == 'POST':
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        cursor.execute(
            f'SELECT * FROM {user}_signup WHERE username = %s OR email = %s',
            (name, email)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        error = None
        if row:
            if row['username'] == name:
                error = 'Username Already Exists. Please Login!'
            elif row['email'] == email:
                error = 'Email Id Already Exists. Please Login!'
            return render_template(f'{user}/{user}-signup.html', error=error)
        else:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)

            cursor.execute(
                f'INSERT INTO {user}_signup (username, email, password) VALUES (%s, %s, %s)',
                (name, email, hashed_password)
            )
            conn.commit()
            user_id = cursor.lastrowid

            # Set separate session keys
            if user == 'learner':
                session['learner_id'] = user_id
                cursor.execute(
                    'INSERT INTO student_detail (id, name, email, enrollment, course, dob, cn, college) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    (user_id, name, email, '', '', '', '', '')
                )
            else:
                session['instructor_id'] = user_id
                
            conn.commit()
            cursor.close()
            conn.close()

        if user == 'learner':
            return render_template('learner/learner-home.html',
            name=name,
            enrollment='',
            course='',
            dob='',
            cn='',
            email=email,
            college='')
        else:
            return redirect(url_for('instructor_dashboard'))
    else:
        return render_template(f'{user}/{user}-signup.html', error=None)


# ---------------- LOGIN ----------------
@app.route('/login/<user>', methods=['POST', 'GET'])
def login(user):
    if request.method == 'POST':
        name = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute( f"SELECT * FROM {user}_signup WHERE username = %s OR email = %s",
            (name, name)
        )
        row = cursor.fetchone()

        conn.close()

        error = None
        if row:
            if check_password_hash(row['password'], password):
                user_id = row['id']
                session['user_type'] = user
                cursor.close()
                if user == 'learner':
                    session['learner_id'] = user_id
                elif user == 'instructor':
                    session['instructor_id'] = user_id
                else:
                    session['admin_id'] = user_id

                if user == 'learner':
                    return redirect(url_for('learner_dashboard'))
                elif user == 'instructor':
                    return redirect(url_for('instructor_dashboard'))
                else:
                    return redirect(url_for('admin_dashboard'))
            else:
                error = 'Invalid password. Please try again!'
                return render_template(f'{user}/{user}-login.html', error=error)
        else:
            error = "User Doesn't Exist!!"
            return render_template(f'{user}/{user}-login.html', error=error)
    return render_template(f'{user}/{user}-login.html', error=None)





@app.route('/<user>/change_password', methods=['POST', 'GET'] ) 
def change_password(user):
    if request.method == 'POST':
        data = request.form

        if data['new_password'] != data['confirmpass']:
            error = 'New Password and Confirm Password do not match. Please try again!'
            return render_template(f'{user}/{user}-password.html', error=error)
        
        if data['old_password'] == data['new_password']:
            error = 'New Password cannot be the same as Old Password. Please try again!'
            return render_template(f'{user}/{user}-password.html', error=error)

        if user == 'learner':   
            user_id = session.get('learner_id')
        else:
            user_id = session.get('instructor_id')  
        

        conn = get_db_connection()  
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f'SELECT * FROM {user}_signup WHERE id = %s', (user_id,))
        row = cursor.fetchone()
        if row and check_password_hash(row['password'], data['old_password']):
            new_hashed_password = generate_password_hash(data['new_password'])
            cursor.execute(
                f'UPDATE {user}_signup SET password = %s WHERE id = %s',
                (new_hashed_password, user_id)
            )
            conn.commit()
            cursor.close()
            conn.close()
            error = 'Password changed successfully!'
            return render_template(f'{user}/{user}-password.html', error=error, success=True)
        else:
            error = 'Old password is incorrect. Please try again!'
            cursor.close()
            conn.close()
            return render_template(f'{user}/{user}-password.html', error=error)

    return render_template(f'{user}/{user}-password.html', error=None)



# ---------------- MAIN DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard/index.html')


@app.route('/login-page')
def login_page():
    return render_template('dashboard/login.html') 


@app.route('/contact')
def contact():
    return render_template('dashboard/contact.html')


@app.route('/about')
def about():
    return render_template('dashboard/about.html')



# ---------------- ADMIN ----------------


@app.route('/admin/dashboard')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    user = session['admin_id']

    cursor.execute(
        'SELECT * FROM admin_signup WHERE id = %s ',
        (user,)
    )
    data = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('admin/admin-dashboard.html', name=data['username'], email=data['email'] )


@app.route('/admin/manage/<action>')
def manage(action):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if action == 'courses':
        cursor.execute("SELECT * FROM courses")
        data = cursor.fetchall()
    elif action == 'learners':  
        cursor.execute("SELECT * FROM student_detail")
        data = cursor.fetchall()
    elif action == 'instructors':
        cursor.execute("SELECT * FROM instructor_signup")
        data = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template(f'admin/manage-{action}.html', data = data)


@app.route("/admin/<user>/delete/<int:id>")
def admin_delete(user, id):
    conn = get_db_connection()
    cursor = conn.cursor()  
    if user == 'learner':
        cursor.execute("DELETE FROM student_detail WHERE id = %s", (id,))
        cursor.execute("DELETE FROM learner_signup WHERE id = %s", (id,))
    elif user == 'instructor':
        cursor.execute("DELETE FROM instructor_signup WHERE id = %s", (id,))    
    elif user == 'course':
        cursor.execute("DELETE FROM courses WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("manage", action=user + 's'))




# ---------- FETCH DETAILS (AJAX) ----------
@app.route("/admin/learner/details/<int:id>")
def learner_details(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM learners WHERE id = %s", (id,))
    learner = cursor.fetchone()
    conn.close()
    return jsonify(learner)


# ---------- UPDATE LEARNER ----------
@app.route("/admin/learner/edit/<int:id>", methods=["POST"])
def edit_learner(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    name = request.form.get("name")
    email = request.form.get("email")
    enrollment = request.form.get("course_enrolled")

    cursor.execute("""
        UPDATE learners 
        SET name=%s, email=%s, enrollment=%s 
        WHERE id=%s
    """, (name, email, enrollment, id))

    conn.commit()
    conn.close()
    return redirect(url_for("manage_learners"))



# ---------------- LEARNER ----------------
@app.route('/learner/login')
def learner_login():
    return render_template('learner/learner-login.html', error=None)


@app.route('/learner/register')
def learner_signup():
    return render_template('learner/learner-signup.html', error=None)


@app.route('/learner/edit-profile', methods = ['POST', 'GET'] )
def edit_profile():
    if request.method == 'POST':
        data = request.form
        user = session['learner_id']

        conn = get_db_connection()  
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "UPDATE student_detail SET name = %s, enrollment=%s, course=%s, dob=%s, cn=%s, email=%s, college=%s WHERE id=%s",
            (data['name'], data['enrollment'], data['course'], data['dob'],
            data['cn'], data['email'], data['college'], user)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return redirect(url_for('learner_dashboard'))




@app.route('/learner/password')
def learner_password():
    return render_template('learner/learner-password.html')


@app.route('/learner/dashboard')
def learner_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    user = session['learner_id']

    cursor.execute(
        'SELECT * FROM student_detail WHERE id = %s ',
        (user,)
    )
    data = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'learner/learner-home.html',
        name=data['name'],
        enrollment=data['enrollment'],
        course=data['course'],
        dob=data['dob'],
        cn=data['cn'],
        email=data['email'],
        college=data['college']
    )

@app.route('/learner/courses')
def courses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    conn.close()
    return render_template('learner/courses.html', courses=courses)


@app.route('/enroll/<data_course>', methods=['POST', 'GET'])
def enroll(data_course):
    course_id =  data_course

    if 'learner_id' not in session:
        return "User not logged in", 401

    conn = get_db_connection()
    cursor = conn.cursor()
  
    cursor.execute("SELECT course_name FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()
    course_name = course[0] if course else "Unknown Course"

    cursor.execute("SELECT * FROM student_courses WHERE student_id = %s AND course_id = %s",
                   (session['learner_id'], course_id))
    already = cursor.fetchone()

    if already:
        cursor.close()
        conn.close()
        return f"""
            <script>
                alert('You are already enrolled in "{course_name}".');
                window.location.href = '/learner/courses';
            </script>
        """

    cursor.execute("INSERT INTO student_courses (student_id, course_id) VALUES (%s, %s)",
                   (session['learner_id'], course_id))
    
    cursor.execute("UPDATE courses SET learners_enrolled = learners_enrolled + 1 WHERE id = %s", (course_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return f"""
        <script>
            alert('Course "{course_name}" added successfully!');
            window.location.href = '/learner/courses';
        </script>
    """


@app.route('/rate_course', methods=['POST'])
def rate_course():
    data = request.get_json()
    course_id = data.get('course_id')
    rate = data.get('rating')
    user_id = session.get('learner_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Insert or update user rating
    cursor.execute("""
        INSERT INTO user_course_ratings (user_id, course_id, rating)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE rating = VALUES(rating)
    """, (user_id, course_id, rate))

    # ✅ Recalculate course average rating
    cursor.execute("""
        UPDATE courses
        SET rating = (SELECT AVG(rating) FROM user_course_ratings WHERE course_id = %s),
            rated = (SELECT COUNT(*) FROM user_course_ratings WHERE course_id = %s)
        WHERE id = %s
    """, (course_id, course_id, course_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'success': True, 'message': 'Rating updated'})


@app.route('/learner/study') 
def study():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.* 
        FROM courses c
        JOIN student_courses sc ON c.id = sc.course_id
        WHERE sc.student_id = %s
    """, (session['learner_id'],))
    courses = cursor.fetchall()
    conn.close()
    
    return render_template('/learner/study.html', courses = courses, open = False)


@app.route('/learner/unenroll/<course_id>', methods=['POST', 'GET'])
def unenroll(course_id):
    if 'learner_id' not in session:
        return "User not logged in", 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM student_courses WHERE student_id = %s AND course_id = %s",
                   (session['learner_id'], course_id))
    
    cursor.execute("UPDATE courses SET learners_enrolled = learners_enrolled - 1 WHERE id = %s", (course_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('study'))


@app.route('/learner/open_course/<course_id>')
def open_course(course_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()

    conn.close()
    return render_template('learner/study.html', open=True, course=course)


# ---------------- INSTRUCTOR ----------------
@app.route('/instructor/dashboard')
def instructor_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses where created_by = %s", (session['instructor_id'],))
    courses = cursor.fetchall()
    conn.close()
    return render_template('instructor/instructor-home.html', courses=courses)


@app.route('/instructor/login')
def instructor_login():
    return render_template('instructor/instructor-login.html', error=None)


@app.route('/instructor/register')
def instructor_signup():
    return render_template('instructor/instructor-signup.html', error=None)


@app.route('/instructor/password')
def instructor_password():
    return render_template('instructor/instructor-password.html', error=None)


@app.route('/instructor/my_courses')
def my_courses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses where created_by = %s", (session['instructor_id'],))
    courses = cursor.fetchall()

    return render_template('instructor/mycourses.html', courses=courses)

from datetime import datetime

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'instructor_id' not in session:  
        return redirect(url_for('login', user='instructor'))
    
    if request.method == 'POST':
        course_name = request.form['course_name']
        description = request.form['description']
        now = datetime.now()   # current time

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM instructor_signup where id = %s", (session['instructor_id'],))
        creator = cursor.fetchone()

        cursor.execute(
            "INSERT INTO courses (course_name, description, created_by, created_at, creator, rating, learners_enrolled) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (course_name, description, session['instructor_id'], now, creator['username'], 0, 0)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('my_courses'))
    
    return render_template('instructor/mycourses.html')



@app.route('/edit_course', methods=['GET', 'POST'])
def edit_course():
    
    course_id = request.form['course_id']
    name = request.form['course_name']
    desc = request.form['description']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE courses
        SET course_name = %s, description = %s
        WHERE id = %s
    """, (name, desc, course_id))
    conn.commit()
    cursor.close()
    conn.close()

    
    return redirect(url_for('my_courses'))



@app.route('/admin/login') 
def admin_login_page():
    return render_template('admin/admin-login.html')


@app.route('/instructor/search')
def search():
    return render_template('instructor/search.html', student=None)

import shutil

@app.route('/delete_course/<course_id>', methods=['POST', 'GET'])
def delete_course(course_id):
    if 'instructor_id' not in session:  
        return redirect(url_for('login', user='instructor'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM student_courses WHERE course_id = %s", (course_id,))
    cursor.execute("DELETE FROM courses WHERE id = %s AND created_by = %s", (course_id, session['instructor_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    # Delete the course uploads folder (if exists)
    folder_path = os.path.join('static', 'uploads', str(course_id))
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)  # deletes folder + all files inside


    return redirect(url_for('my_courses'))

@app.route('/search_learner', methods=['GET', 'POST'])
def search_learner():
    if request.method == 'POST':
        enrollment = request.form['enrollment']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True, buffered=True)

        cursor.execute(
            'SELECT * FROM student_detail WHERE enrollment = %s',
            (enrollment,)
        )
        data = cursor.fetchone()

        cursor.close()
        conn.close()

        if data:
            return render_template('instructor/search.html', student=data)
        else:
            return render_template('instructor/search.html', student=None , found=False)
    return render_template('instructor/search.html', student=None)



import os
from werkzeug.utils import secure_filename

@app.route('/<user>/courses/course-view/<course_id>')
def course_view(course_id, user):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()

    # ✅ Fetch all uploaded files (PDFs, videos)
    cursor.execute("SELECT * FROM course_uploads WHERE course_id = %s", (course_id,))
    uploads = cursor.fetchall()

    conn.close()


    return render_template(f'{user}/course-view.html', course=course, uploads=uploads)


@app.route('/upload/<int:course_id>', methods=['GET', 'POST'])
def upload(course_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Create upload table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_uploads (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_id INT,
            title VARCHAR(255),
            file_type VARCHAR(50),
            file_path VARCHAR(500),
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # ✅ Handle upload form submission
    if request.method == 'POST':
        title = request.form['title']
        upload_type = request.form['upload_type']  # "pdf" or "video"
        file = request.files['file']

        cursor.execute(
                "select * from course_uploads where file_path = %s",
                (f'uploads/{course_id}/{file}',)
            )
        filedata = cursor.fetchone()
        if file and filedata == None:
            filename = secure_filename(file.filename)
            folder = os.path.join(app.config['UPLOAD_FOLDER'], str(course_id))
            os.makedirs(folder, exist_ok=True)
            file_path = os.path.join(folder, filename).replace('\\', '/')
            file.save(file_path)
            folder = os.path.join(app.config['UPLOAD_FOLDER1'], str(course_id))
            file_path = os.path.join(folder, filename).replace('\\', '/')


            cursor.execute(
                "INSERT INTO course_uploads (course_id, title, file_type, file_path) VALUES (%s, %s, %s, %s)",
                (course_id, title, upload_type, file_path)
            )
            conn.commit()

    # ✅ Fetch course details
    cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()

    # ✅ Fetch all uploaded files (PDFs, videos)
    cursor.execute("SELECT * FROM course_uploads WHERE course_id = %s", (course_id,))
    uploads = cursor.fetchall()

    conn.close()

    return redirect(url_for('course_view', course_id=course_id, user='instructor'))


@app.route('/instructor/mycourses/course-description/edit-description/<course_id>', methods = ['POST', 'GET'])
def edit_course_description(course_id):
    if request.method == 'POST':
        course_description = request.form['description']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        
        cursor.execute(
            "UPDATE courses SET description = %s WHERE id=%s",
            (course_description, course_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
    
    return redirect(url_for('course_view', course_id = course_id))


@app.route('/delete-upload/<course_id>/<upload_id>', methods=['POST', 'GET'])
def delete_upload(course_id, upload_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch file path
    cursor.execute("SELECT file_path FROM course_uploads WHERE id = %s", (upload_id,))
    file = cursor.fetchone()

    if file:
        file_path = os.path.join('static', file['file_path'])
        # Delete the actual file
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete record from DB
        cursor.execute("DELETE FROM course_uploads WHERE id = %s", (upload_id,))
        conn.commit()

    conn.close()
    return redirect(url_for('course_view', course_id=course_id, user='instructor'))



# ---------------- MAIN ----------------
if __name__ == '__main__':
    app.run(debug=True)
