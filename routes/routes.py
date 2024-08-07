from flask import Blueprint, flash, redirect, render_template, request, abort, session, url_for
from functools import wraps
from flask import g
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
import logging

bp = Blueprint('my_blueprint', __name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# ==============HOME==================
@bp.route('/home')
def home():
    if 'user_role' not in session:
        return redirect(url_for('signin'))  # Redirect to signin if 'user_role' is not in session, assuming the user is not logged in
    
    # Retrieve the user's role and verification status from the session
    user_role = session.get('user_role')
    isVerified = session.get('isVerified')

    # Check if the user is verified
    if isVerified ==False:
        return redirect(url_for('my_blueprint.new_user'))
        # Redirect based on user role
    else:
        if user_role == 'registrar':
                return redirect(url_for('my_blueprint.registrar'))  # Assuming you have a route named 'registrar_dashboard' for registrars
        elif user_role == 'admin':
                return redirect(url_for('my_blueprint.admin'))  # Assuming you have a route named 'admin_dashboard' for admins
        elif user_role == 'dept-head':  # Assuming 'dept-head' is the role for department heads
                return redirect(url_for('my_blueprint.program'))  # Assuming 'program' is the route for department heads
        else:
                return redirect(url_for('signin'))  # Redirect back to signin if role is unknown

# ==============Department Head==================
@bp.route('/department-head')
def dep_head():
    return redirect(url_for('my_blueprint.program'))


@bp.route('/department-head/program')
def program():
    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)

    cur = g.mysql.connection.cursor()

    try:
        cur.execute("SELECT * FROM programs WHERE user_id = %s", (session['user_id'],))
        programs = cur.fetchall()
        logger.debug(f"Fetched programs: {programs}")  # Log fetched data
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        cur.close()
    
    form = AddProgramForm()
    return render_template('dep_head/program.html', programs=programs, form=form)

class AddProgramForm(FlaskForm):
    program = StringField('Program', validators=[DataRequired()])
    submit = SubmitField('Add Program')

@bp.route('/add-program', methods=['GET', 'POST'])
def add_program():
    form = AddProgramForm(request.form)
    if form.validate_on_submit():
        program_name = form.program.data
        user_id = session.get('user_id')

        try:
            cur = g.mysql.connection.cursor()
            cur.execute("INSERT INTO programs (program_name, user_id) VALUES (%s, %s)", (program_name, user_id))
            g.mysql.connection.commit()
            cur.close()
            flash('Program added successfully!', 'success')
        except Exception as e:
            print(e)
            flash('Failed to add program.', 'danger')

        return redirect(url_for('my_blueprint.program'))
    else:
        flash('Form validation failed.', 'warning')
    
    return render_template('dep_head/program.html', form=form)


@bp.route('/department-head/faculties')
def faculties():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)
    return render_template('dep_head/faculties.html')

@bp.route('/department-head/generate')
def generate():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)
    return render_template('dep_head/generate.html')

@bp.route('/department-head/create')
def create():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)
    return render_template('dep_head/create_schedule.html')




class AddCourseForm(FlaskForm):
    program_id = HiddenField()  
    course_name = StringField('Course Name', validators=[DataRequired()])
    course_code = StringField('Course Code', validators=[DataRequired()])
    units = StringField('Units', validators=[DataRequired()])
    block = StringField('Block', validators=[DataRequired()])
    type = SelectField('Type', choices=['Lecture', 'Comp Laboratory', 'Engineering Laboratory'], validators=[DataRequired()])
    year_level = SelectField('Year Level', choices=['1st Year', '2nd Year', '3rd Year', '4th Year'], validators=[DataRequired()])
    submit = SubmitField('Add Course')

def add_course_to_db(course_name, course_code, units, block, course_type, year_level, program_id):
    cur = g.mysql.connection.cursor()
    try:
        # Adjust the INSERT statement according to your courses table structure
        cur.execute("INSERT INTO courses (course_name, course_code, units, block, type, year_level, program_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                  (course_name, course_code, units, block, course_type, year_level, program_id))
        g.mysql.connection.commit()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # Handle exception, maybe rollback transaction here
    finally:
        cur.close()

@bp.route('/add_course', methods=['POST'])
def add_course():
    form = AddCourseForm()
    if form.validate_on_submit():
        course_name = form.course_name.data
        course_code = form.course_code.data
        units = form.units.data
        block = form.block.data
        course_type = form.type.data
        year_level = form.year_level.data
        program_id = form.program_id.data
        # Assuming you have a function to insert courses into the database
        add_course_to_db(course_name, course_code, units, block, course_type, year_level, program_id)
        flash('Course added successfully!', 'success')
        return redirect(url_for('my_blueprint.dep_head_content', program_id=program_id))  # Redirect back to the department head content page after adding the course
    else:
        flash('Failed to add course.', 'danger')
        # Redirect back to the form page or handle error appropriately
        return redirect(url_for('my_blueprint.dep_head_content', program_id=program_id))

@bp.route('/department_head_content/<int:program_id>')
def dep_head_content(program_id):
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)

    cur = g.mysql.connection.cursor()
    try:
        # Fetch courses related to the specified program_id
        cur.execute("SELECT * FROM courses WHERE program_id = %s", (program_id,))
        courses = cur.fetchall()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        cur.close()

    return render_template('dep_head/dep_head_content.html', courses=courses)

# ==============Admin==================
@bp.route('/admin')
def admin():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'admin':
        abort(403)
    return render_template('admin/admin.html')




# ==============Registrar==================
@bp.route('/registrar')
def registrar():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'registrar':
        abort(403)
    return render_template('registrar/registrar.html')

# ==============New User==================
@bp.route('/new_user')
def new_user():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('isVerified') == True:
        abort(403)
    return render_template('new_user.html')