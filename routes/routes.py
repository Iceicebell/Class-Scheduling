from typing import Optional
from flask import Blueprint, flash, jsonify, redirect, render_template, request, abort, session, url_for
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
    return render_template('dep_head/program.html', programs=programs, form=form, current_endpoint=request.endpoint)

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
    
    return render_template('dep_head/program.html', form=form, current_endpoint=request.endpoint)


class AddFacultyForm(FlaskForm):
       first_name = StringField('First Name', validators=[DataRequired()])
       last_name = StringField('Last Name', validators=[DataRequired()])
       faculty_units = StringField('Faculty Units', validators=[DataRequired()])
       faculty_type = SelectField('Faculty Type', choices=[('full_time', 'Full Time'), ('part_time', 'Part time')], validators=[DataRequired()])
       submit = SubmitField('Add Faculty')

def add_faculty_to_db(first_name, last_name, faculty_units, faculty_type,department):
    # Mapping for faculty type to match database expectations
    faculty_type_mapping = {
    'full_time': 'Full Time',
    'part_time': 'Part time'
}
    # Transform course_type input
    db_faculty_type = faculty_type_mapping.get(faculty_type, faculty_type)

    cur = g.mysql.connection.cursor()
    try:
        # Adjust the INSERT statement according to your faculties table structure
        cur.execute("INSERT INTO faculty (first_name, last_name, faculty_units, faculty_type, department) VALUES (%s, %s, %s, %s, %s)",
                  (first_name, last_name, faculty_units, db_faculty_type, department))
        g.mysql.connection.commit()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # Handle exception, maybe rollback transaction here
    finally:
        cur.close()

@bp.route('/department-head/faculties', methods=['GET', 'POST'])
def faculties():
    form = AddFacultyForm()
    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)

    current_user_id = session['user_id']


    # Fetch faculty members from the same department as the current user
    try:
        # First, fetch the department of the current user
        cur = g.mysql.connection.cursor()
        cur.execute("SELECT department FROM users WHERE user_id = %s", (current_user_id,))
        current_user_department = cur.fetchone()
        if current_user_department:
            department = current_user_department[0]  # Assuming the department is the first column in the result
        else:
            department = None  # Handle case where department is not found

        if department:
            # Now, fetch faculty members from the same department
            cur.execute("SELECT * FROM faculty WHERE department = %s", (department,))
            faculty_members = cur.fetchall()
            cur.close()

            # Convert tuples to list of dictionaries for the template
            faculty_list = faculty_members
        else:
            faculty_list = []
    except Exception as e:
        print(e)
        faculty_list = []  # Fallback to empty list on error




    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        faculty_units = form.faculty_units.data
        faculty_type = form.faculty_type.data
        department = session.get('department')
        # Assuming you have a function to insert faculty into the database
        add_faculty_to_db(first_name, last_name, faculty_units, faculty_type, department)

        flash('Faculty added successfully!', 'success')
        return redirect(url_for('my_blueprint.faculties'))

    # Pass the form, the list of programs, and the list of faculty members to the template
    return render_template('dep_head/faculties.html', form=form, faculty=faculty_list, current_endpoint=request.endpoint)

class AddSectionForm(FlaskForm):
    section_name = StringField('Section Name', validators=[DataRequired()])
    submit = SubmitField('Add Section')

@bp.route('/add-section', methods=['GET', 'POST'])
def add_section():
    form = AddSectionForm(request.form)
    if form.validate_on_submit():
        section_name = form.section_name.data
        # Assuming 'department' is another field you need to capture from somewhere, possibly from session or another source
        department = session.get('department')  # Example: Fetching department ID from session; adjust as necessary

        try:
            cur = g.mysql.connection.cursor()
            cur.execute("INSERT INTO sections (section_name, department, created_at, updated_at) VALUES (%s, %s, NOW(), NOW())", (section_name, department))
            g.mysql.connection.commit()
            cur.close()
            flash('Section added successfully!', 'success')
        except Exception as e:
            print(e)
            flash('Failed to add section.', 'danger')

        return redirect(url_for('my_blueprint.section'))  # Adjust the endpoint as necessary
    else:
        flash('Form validation failed.', 'warning')
    
    return render_template('dep_head/section.html', form=form, current_endpoint=request.endpoint)

@bp.route('/department-head/section')
def section():
    form = AddSectionForm(request.form)
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)
    current_department= session.get('department')

    cur = g.mysql.connection.cursor()

    try:
        # Execute the query to fetch sections where the program matches the current user's program
        cur.execute("SELECT * FROM sections WHERE department = %s", (current_department,))
        sections = cur.fetchall()
    except Exception as e:
        logging.error(f"An error occurred while fetching sections: {e}")
        sections = []
        print(sections)
    finally:
        cur.close()

    return render_template('dep_head/section.html', current_endpoint=request.endpoint, form=form, sections=sections)



@bp.route('/department-head/create')
def create():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)
    return render_template('dep_head/create_schedule.html', current_endpoint=request.endpoint)




class AddCourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    course_code = StringField('Course Code', validators=[DataRequired()])
    units = StringField('Units', validators=[DataRequired()])
    course_block = StringField('Block', validators=[DataRequired()])
    course_type = SelectField('Type', choices=[('lecture', 'Lecture'), ('comp_lab', 'Comp Laboratory'), ('eng_lab', 'Engineering Laboratory')], validators=[DataRequired()])
    year_level = SelectField('Year Level', choices=[('1st_year', '1st Year'), ('2nd_year', '2nd Year'), ('3rd_year', '3rd Year'), ('4th_year', '4th Year')], validators=[DataRequired()])
    faculty = SelectField('Faculty')
    submit = SubmitField('Add Course')

def add_course_to_db(course_name, course_code, units, course_block, course_type, year_level, program_id, faculty_id=None):
    # Mapping for course_type to match database expectations
    course_type_mapping = {
        'lecture': 'Lecture',
        'comp_lab': 'Comp Laboratory',
        'eng_lab': 'Engineering Laboratory'
    }

    # Mapping for year_level to match database expectations
    year_level_mapping = {
        '1st_year': '1st Year',
        '2nd_year': '2nd Year',
        '3rd_year': '3rd Year',
        '4th_year': '4th Year'
    }

    # Transform course_type and year_level inputs
    db_course_type = course_type_mapping.get(course_type, course_type)
    db_year_level = year_level_mapping.get(year_level, year_level)

    cur = g.mysql.connection.cursor()
    try:
        # Adjust the INSERT statement according to your courses table structure
        cur.execute("INSERT INTO courses (course_name, course_code, units, course_block, course_type, course_level, program_id, faculty_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                  (course_name, course_code, units, course_block, db_course_type, db_year_level, program_id, faculty_id))
        g.mysql.connection.commit()

        if faculty_id:
            cur.execute("""
                UPDATE faculty 
                SET faculty_used_units = faculty_used_units + %s 
                WHERE faculty_id = %s
            """, (units, faculty_id))
            g.mysql.connection.commit()

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # Handle exception, maybe rollback transaction here
    finally:
        cur.close()

@bp.route('/add_course',  methods=['GET', 'POST'])
def add_course():

    cur = g.mysql.connection.cursor()
    try:
        cur.execute("SELECT faculty_id, CONCAT(first_name, ' ', last_name) AS full_name FROM faculty")
        faculties = cur.fetchall()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        cur.close()
    faculty_choices = [(str(faculty[0]), faculty[1]) for faculty in faculties]
    
    form = AddCourseForm(request.form)  # Ensure you're getting form data from the request
    form.faculty.choices = faculty_choices

    if form.validate_on_submit():
        print("Form is valid")
        course_name = form.course_name.data
        course_code = form.course_code.data
        units = form.units.data
        block = form.course_block.data
        course_type = form.course_type.data
        year_level = form.year_level.data
        program_id=session.get('current_program_id', None)
        faculty_id = form.faculty.data if form.faculty.data else None

        print(course_name)
        print(course_code)
        print(units)
        print(block)
        print(course_type)
        print(year_level )
        print(faculty_id )
        # program_id is already extracted above, so no need to extract again here
        
        # Assuming you have a function to insert courses into the database
        add_course_to_db(course_name, course_code, units, block, course_type, year_level, program_id,faculty_id=faculty_id)
        flash('Course added successfully!', 'success')
        return redirect(url_for('my_blueprint.dep_head_content', program_id=session.get('current_program_id', None)))  # Redirect back to the department head content page after adding the course
    else:
        print("Form validation failed:", form.errors)
        flash('Failed to add course.', 'danger')
        # Redirect back to the form page or handle error appropriately
        return redirect(url_for('my_blueprint.dep_head_content', program_id=session.get('current_program_id', None)))


def execute_query(query, params):
    cur = g.mysql.connection.cursor()
    try:
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        cur.close()


@bp.route('/department_head_content/<int:program_id>')
def dep_head_content(program_id):
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)

    session['current_program_id'] = program_id

    # Adjusted query to join with faculty and select faculty names
    query_template = """
    SELECT courses.course_code, courses.course_name, courses.course_block, courses.course_type, courses.units, CONCAT(faculty.first_name, ' ', faculty.last_name) AS faculty_name
    FROM courses
    LEFT JOIN faculty ON courses.faculty_id = faculty.faculty_id
    WHERE courses.program_id = %s AND courses.course_level = %s
    """

    # Fetch courses for each year level, including faculty names
    courses1 = execute_query(query_template, (program_id, '1st Year'))
    courses2 = execute_query(query_template, (program_id, '2nd Year'))
    courses3 = execute_query(query_template, (program_id, '3rd Year'))
    courses4 = execute_query(query_template, (program_id, '4th Year'))

    faculties = []
    try:
        cur = g.mysql.connection.cursor()
        cur.execute("SELECT faculty_id, CONCAT(first_name, ' ', last_name) AS full_name FROM faculty")
        faculties = cur.fetchall()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        cur.close()

    # Convert tuples to a list of (id, full_name) pairs for the SelectField choices
    faculty_choices = [(str(faculty[0]), faculty[1]) for faculty in faculties]
    print(faculty_choices) 

    # Create the form and set faculty choices
    form = AddCourseForm()
    form.faculty.choices = faculty_choices
    return render_template('dep_head/dep_head_content.html', courses1=courses1, courses2=courses2, courses3=courses3, courses4=courses4, form=form, faculty_choices=faculty_choices, current_endpoint=request.endpoint)

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


