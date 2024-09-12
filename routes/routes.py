from typing import Optional
from flask import Blueprint, flash, jsonify, redirect, render_template, request, abort, session, url_for
from functools import wraps
from flask import g
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import HiddenField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo, Optional
import logging
bp = Blueprint('my_blueprint', __name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# ========================================================Home======================================================
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

# ========================================================Department Head======================================================
@bp.route('/department-head')
def dep_head():
    return redirect(url_for('my_blueprint.program'))


# ========================================================FACULTY1======================================================
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
        cur.execute("INSERT INTO faculties (first_name, last_name, faculty_units, faculty_type, department) VALUES (%s, %s, %s, %s, %s)",
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
            cur.execute("SELECT * FROM faculties WHERE department = %s", (department,))
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

@bp.route('/delete-faculty/<int:faculty_id>', methods=['DELETE'])
def delete_faculty(faculty_id):
    logger.debug(f"Received request for faculty_id: {faculty_id}")
    logger.debug(f"Request method: {request.method}")

    # Check if the faculty exists
    cur = g.mysql.connection.cursor()
    try:
        cur.execute("SELECT * FROM faculties WHERE faculty_id = %s", (faculty_id,))
        faculty = cur.fetchone()
        if not faculty:
            logger.error(f"Faculty with ID {faculty_id} not found.")
            return jsonify({'success': False, 'message': 'Faculty not found.'}), 404

        # Log the faculty data for debugging
        logger.debug(f"Faculty data: {faculty}")

        # Check if the faculty belongs to the current user's department
        current_user_department = session.get('department')
        logger.debug(f"Current user's department: {current_user_department}")
        if len(faculty) < 6 or faculty[5] != current_user_department:
            logger.error(f"Faculty with ID {faculty_id} doesn't belong to the current user's department.")
            return jsonify({'success': False, 'message': 'You do not have permission to delete this faculty.'}), 403

        # Fetch all courses associated with this faculty
        cur.execute("SELECT course_id FROM courses WHERE faculty_id = %s", (faculty_id,))
        associated_courses = cur.fetchall()
        logger.debug(f"Associated courses: {associated_courses}")

        # Update courses to remove the faculty association
        for course in associated_courses:
            cur.execute("UPDATE courses SET faculty_id = NULL WHERE course_id = %s", (course[0],))

        # Delete the faculty
        cur.execute("DELETE FROM faculties WHERE faculty_id = %s", (faculty_id,))
        g.mysql.connection.commit()

        logger.info(f"Faculty with ID {faculty_id} and associated courses deleted successfully.")
        return jsonify({'success': True, 'message': 'Faculty and associated courses deleted successfully!'}), 200

    except Exception as e:
        logger.error(f"An error occurred during deletion: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the faculty.'}), 500
    finally:
        cur.close()

class EditFacultyForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    faculty_units = StringField('Faculty Units', validators=[DataRequired()])
    faculty_type = SelectField('Faculty Type', choices=[('Full Time', 'Full Time'), ('Part Time', 'Part time')], validators=[DataRequired()])
    submit = SubmitField('Update Faculty')

@bp.route('/edit-faculty/<int:faculty_id>', methods=['GET', 'POST'])
def edit_faculty(faculty_id):
    logger.debug(f"Received request for faculty_id: {faculty_id}")
    logger.debug(f"Request method: {request.method}")

    # Ownership check
    current_user_department = session.get('department')
    cur = g.mysql.connection.cursor()
    try:
        cur.execute("SELECT department FROM faculties WHERE faculty_id = %s", (faculty_id,))
        faculty_department = cur.fetchone()

        if not faculty_department:
            flash('Faculty not found.', 'error')
            return redirect(url_for('my_blueprint.faculties'))

        if faculty_department[0] != current_user_department:
            flash('You do not have permission to edit this faculty.', 'error')
            return redirect(url_for('my_blueprint.faculties'))

        # If we reach here, the faculty belongs to the current user's department
        session['current_faculty_id'] = faculty_id

        # Fetch the faculty details
        cur.execute("SELECT first_name, last_name, faculty_units, faculty_type FROM faculties WHERE faculty_id = %s", (faculty_id,))
        faculty_data = cur.fetchone()
        if not faculty_data:
            flash('Faculty not found.', 'error')
            return redirect(url_for('my_blueprint.faculties'))
        logger.debug(f"Fetched faculty data: {faculty_data}")

        # Prepare the form
        form = EditFacultyForm()
        

        if form.validate_on_submit():
            logger.debug(f"Form validated successfully. Form data: {form.data}")
            logger.debug(f"First name from form: {form.first_name.data}")
            logger.debug(f"Last name from form: {form.last_name.data}")
            logger.debug(f"Faculty units from form: {form.faculty_units.data}")
            logger.debug(f"Faculty type from form: {form.faculty_type.data}")
            logger.debug(f"First name from database: {faculty_data[0]}")
            logger.debug(f"Last name from database: {faculty_data[1]}")
            logger.debug(f"Faculty units from database: {faculty_data[2]}")
            logger.debug(f"Faculty type from database: {faculty_data[3]}")

            try:
                cur = g.mysql.connection.cursor()
                cur.execute("UPDATE faculties SET first_name = %s, last_name = %s, faculty_units = %s, faculty_type = %s WHERE faculty_id = %s",
                            (form.first_name.data, form.last_name.data, form.faculty_units.data, form.faculty_type.data, faculty_id))
                g.mysql.connection.commit()
                logger.debug(f"Affected rows: {cur.rowcount}")
                if cur.rowcount == 0:
                    logger.warning(f"No rows affected for faculty_id: {faculty_id}")
                    flash('No changes were made to the faculty.', 'warning')
                else:
                    flash('Faculty updated successfully!', 'success')
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                flash('Failed to update faculty.', 'danger')
            finally:
                cur.close()

            return redirect(url_for('my_blueprint.faculties'))
        form.first_name.data = faculty_data[0]
        form.last_name.data = faculty_data[1]
        form.faculty_units.data = faculty_data[2]
        form.faculty_type.data = faculty_data[3]
        return render_template('dep_head/edit_faculty.html', form=form, faculty_id=faculty_id, current_endpoint=request.endpoint)

    except Exception as e:
        logger.error(f"An error occurred during ownership check: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
    finally:
        cur.close()

    return redirect(url_for('my_blueprint.faculties'))




# ========================================================SECTIONS1======================================================
class AddSectionForm(FlaskForm):
    section_name = StringField('Section Name', validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired()])
    year_level = SelectField('Year Level', choices=[
        ('', '-- Please select --'),
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year')
    ], validators=[DataRequired()])
    program = SelectField('Program', validators=[DataRequired()])

@bp.route('/add-section', methods=['GET', 'POST'])
def add_section():
    form = AddSectionForm(request.form)
    cur = g.mysql.connection.cursor()
    logger.debug(f"Received request method: {request.method}")
    cur.execute("SELECT * FROM programs WHERE user_id = %s", (session['user_id'],))
    programs = cur.fetchall()
    program_choices = [(str(program[0]), program[1]) for program in programs]

    # Update the form's program field with the choices
    form.program.choices = program_choices
    
    if form.validate_on_submit():
        logger.debug("Form validated successfully")
        
        section_name = form.section_name.data
        capacity = form.capacity.data
        year_level = form.year_level.data
        program_id = form.program.data
        
        user_id = session.get('user_id')
        department = session.get('department')
        
        if not user_id or not department:
            flash('User or department not found in session.', 'danger')
            return redirect(url_for('my_blueprint.section'))
        
        try:
            cur = g.mysql.connection.cursor()
            
            logger.debug("Executing SQL query...")
            cur.execute("""
                INSERT INTO sections (section_name, capacity, year_level, user_id, program_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """, (section_name, capacity, year_level, user_id, program_id))
            
            logger.debug(f"Affected rows: {cur.rowcount}")
            
            if cur.rowcount == 0:
                logger.warning("No rows were affected by the insert operation")
            
            g.mysql.connection.commit()
            cur.close()
            flash('Section added successfully!', 'success')
        except Exception as e:
            logger.error(f"Error adding section: {str(e)}")
            flash('Failed to add section.', 'danger')
        
        return redirect(url_for('my_blueprint.section'))
    
    else:
        logger.debug(f"Form validation failed. Errors: {form.errors}")
        flash('Form validation failed.', 'warning')
    
    return render_template('dep_head/section.html', form=form, current_endpoint=request.endpoint)

@bp.route('/department-head/section')
def section():
    form = AddSectionForm(request.form)
    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)

    current_user_id = session.get('user_id')

    cur = g.mysql.connection.cursor()

    cur.execute("SELECT * FROM programs WHERE user_id = %s", (session['user_id'],))
    programs = cur.fetchall()


    logger.debug(f"Fetched programs: {programs}")

    program_choices = [(str(program[0]), program[1]) for program in programs]
    form.program.choices = program_choices
    try:
        # Execute the query to fetch sections belonging to the current user
        
        cur.execute("SELECT * FROM sections WHERE user_id = %s", (current_user_id,))
        sections = cur.fetchall()
    except Exception as e:
        logging.error(f"An error occurred while fetching sections: {e}")
        sections = []
        print(sections)
    finally:
        cur.close()

    return render_template('dep_head/section.html', current_endpoint=request.endpoint, form=form, program_choices=program_choices, sections=sections)


class EditSectionForm(FlaskForm):
    section_name = StringField('Section Name', validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired()])
    year_level = SelectField('Year Level', choices=[
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year')
    ], validators=[DataRequired()])

@bp.route('/edit-section/<int:section_id>', methods=['GET', 'POST'])
def edit_section(section_id):
    logger.debug(f"Received request for section_id: {section_id}")
    logger.debug(f"Request method: {request.method}")

    # Ownership check
    current_user_id = session.get('user_id')
    cur = g.mysql.connection.cursor()
    try:
        cur.execute("SELECT user_id FROM sections WHERE section_id = %s", (section_id,))
        section_user_id = cur.fetchone()

        if not section_user_id:
            flash('Section not found.', 'error')
            return redirect(url_for('my_blueprint.section'))

        if section_user_id[0] != current_user_id:
            flash('You do not have permission to edit this section.', 'error')
            return redirect(url_for('my_blueprint.section'))

        # If we reach here, the section belongs to the current user
        session['current_section_id'] = section_id

        # Fetch the section details
        cur.execute("""
            SELECT section_name, capacity, year_level
            FROM sections
            WHERE section_id = %s
        """, (section_id,))
        section_data = cur.fetchone()
        if not section_data:
            flash('Section not found.', 'error')
            return redirect(url_for('my_blueprint.section'))
        logger.debug(f"Fetched section data: {section_data}")

        # Prepare the form
        form = EditSectionForm()

        if form.validate_on_submit():
            logger.debug(f"Form validated successfully. Form data: {form.data}")
            logger.debug(f"Section name from form: {form.section_name.data}")
            logger.debug(f"Capacity from form: {form.capacity.data}")
            logger.debug(f"Year level from form: {form.year_level.data}")
            logger.debug(f"Section name from database: {section_data[0]}")
            logger.debug(f"Capacity from database: {section_data[1]}")
            logger.debug(f"Year level from database: {section_data[2]}")

            try:
                cur = g.mysql.connection.cursor()
                cur.execute("""
                    UPDATE sections
                    SET section_name = %s, capacity = %s, year_level = %s
                    WHERE section_id = %s
                """, (
                    form.section_name.data,
                    form.capacity.data,
                    form.year_level.data,
                    section_id
                ))
                logger.debug(f"Affected rows: {cur.rowcount}")
                if cur.rowcount == 0:
                    logger.warning(f"No rows affected for section_id: {section_id}")
                    flash('No changes were made to the section.', 'warning')
                else:
                    g.mysql.connection.commit()
                    logger.debug("Changes committed to the database")
                    flash('Section updated successfully!', 'success')
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                flash('Failed to update section.', 'danger')
            finally:
                cur.close()

            return redirect(url_for('my_blueprint.section'))

        # Pre-populate the form with existing data
        form.section_name.data = section_data[0]
        form.capacity.data = section_data[1]
        form.year_level.data = section_data[2]

        return render_template('dep_head/edit_section.html',
                               form=form,
                               section_id=section_id,
                               current_endpoint=request.endpoint)
    except Exception as e:
        logger.error(f"An error occurred during ownership check: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
    finally:
        cur.close()

    return redirect(url_for('my_blueprint.section'))


@bp.route('/delete-section/<int:section_id>', methods=['DELETE'])
def delete_section(section_id):
    try:
        cur = g.mysql.connection.cursor()
        
        # Start a transaction
        g.mysql.connection.begin()
        
        # Delete associated entries from section_courses table
        cur.execute("DELETE FROM section_courses WHERE section_id = %s", (section_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from section_courses table")
        
        # Delete associated entries from user_solutions table
        cur.execute("DELETE FROM user_solutions WHERE section_id = %s", (section_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from user_solutions table")
        
        # Delete associated entries from unavailable_times table
        cur.execute("DELETE FROM unavailable_times WHERE section_id = %s", (section_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from unavailable_times table")
        
        # Delete the section itself
        cur.execute("DELETE FROM sections WHERE section_id = %s", (section_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from sections table")
        
        # Commit the transaction
        g.mysql.connection.commit()
        logger.debug("Changes committed to the database")
        
        cur.close()
        return jsonify({'success': True, 'message': 'Section and associated data deleted successfully'})
    
    except Exception as e:
        # Rollback the transaction if an error occurs
        g.mysql.connection.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/view-section/<int:section_id>')
def view_section(section_id):
    # Fetch section details from database
    cur = g.mysql.connection.cursor()
    cur.execute("SELECT * FROM sections WHERE section_id = %s", (section_id,))
    section_data = cur.fetchone()
    
    # Convert the tuple to a dictionary for easier access
    section = dict(zip([desc[0] for desc in cur.description], section_data))
    
    # Fetch program_id from the section
    program_id = section['program_id']
    
    # Fetch all courses for the program that are not yet in the section
    cur.execute("""
        SELECT c.course_id, c.course_code, c.course_name, c.course_block, c.course_type, c.units, f.first_name, f.last_name
        FROM courses c
        LEFT JOIN faculties f ON c.faculty_id = f.faculty_id
        WHERE c.program_id = %s
          AND c.course_level = %s
          AND c.course_id NOT IN (
              SELECT course_id FROM section_courses WHERE section_id = %s
          )
    """, (program_id, section['year_level'], section_id))
    all_courses = cur.fetchall()

    # Fetch selected courses for the section
    cur.execute("SELECT c.course_id, c.course_code, c.course_name FROM courses c JOIN section_courses sc ON c.course_id = sc.course_id WHERE sc.section_id = %s", (section_id,))
    selected_courses = cur.fetchall()

    cur.close()
    return render_template('dep_head/view_section.html', section=section, all_courses=all_courses, selected_courses=selected_courses)

@bp.route('/api/add-to-section', methods=['POST'])
def add_to_section():
    data = request.json
    section_id = data['section_id']
    course_ids = data['course_ids']
    
    cur = g.mysql.connection.cursor()
    try:
        for course_id in course_ids:
            cur.execute("INSERT INTO section_courses (section_id, course_id) VALUES (%s, %s)", (section_id, course_id))
        g.mysql.connection.commit()
        return jsonify({'message': f'Courses added to section {section_id}'}), 200
    except Exception as e:
        return jsonify({'message': f'Failed to add courses: {str(e)}'}), 400
    finally:
        cur.close()

@bp.route('/api/get-selected-courses', methods=['GET'])
def get_selected_courses():
    section_id = request.args.get('section_id')
    if not section_id:
        return jsonify({'message': 'Missing section_id parameter'}), 400

    cur = g.mysql.connection.cursor()
    try:
        
        cur.execute("SELECT c.course_code, c.course_name,c.course_block FROM courses c JOIN section_courses sc ON c.course_id = sc.course_id WHERE sc.section_id = %s", (section_id,))
        selected_courses = cur.fetchall()
        return jsonify([{'course_code': c[0], 'course_name': c[1], 'course_block': c[2]} for c in selected_courses])
    except Exception as e:
        return jsonify({'message': f'Failed to fetch selected courses: {str(e)}'}), 400
    finally:
        cur.close()












# ========================================================CREATE SCHEDULE======================================================
@bp.route('/department-head/create')
def create():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)
    return render_template('dep_head/create_schedule.html', current_endpoint=request.endpoint)



# ========================================================Course1======================================================

class AddCourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    course_code = StringField('Course Code', validators=[DataRequired()])
    units = StringField('Units', validators=[DataRequired()])
    hours_per_week = StringField('Hours Per Week', validators=[DataRequired()])
    course_block = StringField('Block', validators=[DataRequired()])
    course_type = SelectField('Type', choices=[('lecture', 'Lecture'), ('comp_lab', 'Comp Laboratory'), ('eng_lab', 'Engineering Laboratory')], validators=[DataRequired()])
    year_level = SelectField('Year Level', choices=[('1st_year', '1st Year'), ('2nd_year', '2nd Year'), ('3rd_year', '3rd Year'), ('4th_year', '4th Year')], validators=[DataRequired()])
    faculty = SelectField('Faculty', validators=[Optional()])
    submit = SubmitField('Add Course')

def add_course_to_db(course_name, course_code, units, hours_per_week, course_block, course_type, year_level, program_id, faculty_id=None):
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
        cur.execute("INSERT INTO courses (course_name, course_code, units, hours_per_week, course_block, course_type, course_level, program_id, faculty_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                  (course_name, course_code, units, hours_per_week, course_block, db_course_type, db_year_level, program_id, faculty_id))
        g.mysql.connection.commit()

        if faculty_id:
            cur.execute("""
                UPDATE faculties 
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
        # Update this query to use the new table name 'faculties'
        cur.execute("SELECT faculty_id, CONCAT(first_name, ' ', last_name) AS full_name FROM faculties")
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
        hours_per_week = form.hours_per_week.data
        block = form.course_block.data
        course_type = form.course_type.data
        year_level = form.year_level.data
        program_id=session.get('current_program_id', None)
        faculty_id = form.faculty.data if form.faculty.data else None

        print(course_name)
        print(course_code)
        print(hours_per_week)
        print(block)
        print(course_type)
        print(year_level )
        print(faculty_id )
        
        add_course_to_db(course_name, course_code,units, hours_per_week, block, course_type, year_level, program_id,faculty_id=faculty_id)
        flash('Course added successfully!', 'success')
        return redirect(url_for('my_blueprint.dep_head_content', program_id=session.get('current_program_id', None)))  # Redirect back to the department head content page after adding the course
    else:
        print("Form validation failed:", form.errors)
        flash('Failed to add course.', 'danger')
        return redirect(url_for('my_blueprint.dep_head_content', program_id=session.get('current_program_id', None)))


def execute_query(query, params):
    cur = g.mysql.connection.cursor()
    try:
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        cur.close()


# Edit Course Form
class EditCourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    course_code = StringField('Course Code', validators=[DataRequired()])
    units = StringField('Units', validators=[DataRequired()])
    hours_per_week = StringField('Hours Per Week', validators=[DataRequired()])
    course_block = StringField('Block', validators=[DataRequired()])
    course_type = SelectField('Type', choices=[('lecture', 'Lecture'), ('comp_lab', 'Comp Laboratory'), ('eng_lab', 'Engineering Laboratory')], validators=[DataRequired()])
    year_level = SelectField('Year Level', choices=[('1st Year', '1st Year'), ('2nd Year', '2nd Year'), ('3rd Year', '3rd Year'), ('4th Year', '4th Year')], validators=[DataRequired()])
    faculty = SelectField('Faculty', choices=[], validators=[Optional()])
    submit = SubmitField('Update Course')

# Function to update course in the database
def update_course_to_db(course_id, course_name, course_code, units, hours_per_week, course_block, course_type, year_level, program_id, faculty_id=None, new_faculty_id=None):
    # Mapping for course_type to match database expectations
    course_type_mapping = {
        'lecture': 'Lecture',
        'comp_lab': 'Comp Laboratory',
        'eng_lab': 'Engineering Laboratory'
    }

    # Mapping for year_level to match database expectations
    year_level_mapping = {
        '1st Year': '1st Year',
        '2nd Year': '2nd Year',
        '3rd Year': '3rd Year',
        '4th Year': '4th Year'
    }

    # Transform course_type and year_level inputs
    db_course_type = course_type_mapping.get(course_type, course_type)
    db_year_level = year_level_mapping.get(year_level, year_level)

    try:
        cur = g.mysql.connection.cursor()
        
        # First, fetch the current faculty_id for the course
        cur.execute("SELECT faculty_id FROM courses WHERE course_id = %s", (course_id,))
        old_faculty_id = cur.fetchone()[0] if cur.rowcount > 0 else None

        # Update the course
        cur.execute("UPDATE courses SET course_name = %s, course_code = %s, units = %s, hours_per_week = %s, course_block = %s, course_type = %s, course_level = %s, program_id = %s, faculty_id = %s WHERE course_id = %s",
                    (course_name, course_code, units, hours_per_week, course_block, course_type, year_level, program_id, new_faculty_id, course_id))


        # Update faculty_used_units for the old faculty (if it exists)
        if old_faculty_id:
            cur.execute("UPDATE faculties SET faculty_used_units = faculty_used_units - %s WHERE faculty_id = %s", (units, old_faculty_id))

        # Update faculty_used_units for the new faculty (if it exists)
        if new_faculty_id:
            cur.execute("UPDATE faculties SET faculty_used_units = faculty_used_units + %s WHERE faculty_id = %s", (units, new_faculty_id))

        g.mysql.connection.commit()

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # Handle exception, maybe rollback transaction here
    finally:
        cur.close()

# Route for editing a course
@bp.route('/edit-course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    logger.debug(f"Received request for course_id: {course_id}")
    logger.debug(f"Request method: {request.method}")

    # Ownership check
    current_user_id = session.get('user_id')
    cur = g.mysql.connection.cursor()
    try:
        # Fetch the program_id for the given course
        cur.execute("SELECT program_id FROM courses WHERE course_id = %s", (course_id,))
        course_program = cur.fetchone()
        
        if not course_program:
            flash('Course not found.', 'error')
            return redirect(url_for('my_blueprint.dep_head_content', program_id=session.get('current_program_id', None)))

        # Check if the program belongs to the current user
        cur.execute("SELECT user_id FROM programs WHERE program_id = %s", (course_program[0],))
        program_user = cur.fetchone()

        if not program_user or program_user[0] != current_user_id:
            flash('You do not have permission to edit this course.', 'error')
            return redirect(url_for('my_blueprint.dep_head_content', program_id=session.get('current_program_id', None)))

        # If we reach here, the course belongs to a program owned by the current user
        session['current_course_id'] = course_id

        # Fetch the course details
        cur.execute("SELECT course_name, course_code, units, hours_per_week, course_block, course_type, course_level, program_id, faculty_id FROM courses WHERE course_id = %s", (course_id,))
        course_data = cur.fetchone()
        if not course_data:
            flash('Course not found.', 'error')
            return redirect(url_for('my_blueprint.dep_head_content', program_id=session.get('current_program_id', None)))

        # Fetch all faculties for the current user's department
        cur.execute("SELECT faculty_id, CONCAT(first_name, ' ', last_name) AS full_name FROM faculties WHERE department = %s", (session.get('department'),))
        faculties = cur.fetchall()

        # Create the form and set faculty choices
        form = EditCourseForm()
        form.faculty.choices = [('','No Faculty')] + [(str(faculty[0]), faculty[1]) for faculty in faculties]

        # Set the default faculty to the current faculty
        current_faculty_id = course_data[8]
        if current_faculty_id is not None:
            form.faculty.default = str(current_faculty_id)
        else:
            form.faculty.default = ''
        form.faculty.process_data(form.faculty.default)

        if form.validate_on_submit():

            try:
                update_course_to_db(
                    course_id,
                    form.course_name.data,
                    form.course_code.data,
                    form.units.data,
                    form.hours_per_week.data,
                    form.course_block.data,
                    form.course_type.data,
                    form.year_level.data,
                    program_id=session.get('current_program_id', None),
                    new_faculty_id=None if form.faculty.data == '' else form.faculty.data
                )
                flash('Course updated successfully!', 'success')
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                flash('Failed to update course.', 'danger')

            return redirect(url_for('my_blueprint.dep_head_content', program_id=session.get('current_program_id', None)))

        # Pre-populate the form with existing data
        form.course_name.data = course_data[0]
        form.course_code.data = course_data[1]
        form.units.data = course_data[2]
        form.hours_per_week.data = course_data[3]
        form.course_block.data = course_data[4]
        form.course_type.data = course_data[5]
        form.year_level.data = course_data[6]

        return render_template('dep_head/edit_course.html',
                               form=form,
                               course_id=course_id,
                               current_endpoint=request.endpoint)

    except Exception as e:
        logger.error(f"An error occurred during ownership check: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
    finally:
        cur.close()

    return redirect(url_for('my_blueprint.dep_head_content', program_id=session.get('current_program_id', None)))

# Route for deleting a course
@bp.route('/delete-course/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    try:
        cur = g.mysql.connection.cursor()
        
        # Fetch the program_id for the given course
        cur.execute("SELECT program_id FROM courses WHERE course_id = %s", (course_id,))
        course_program = cur.fetchone()

        if not course_program:
            return jsonify({'success': False, 'message': 'Course not found.'}), 404

        # Check if the program belongs to the current user
        cur.execute("SELECT user_id FROM programs WHERE program_id = %s", (course_program[0],))
        program_user = cur.fetchone()

        if not program_user or program_user[0] != session.get('user_id'):
            return jsonify({'success': False, 'message': 'You do not have permission to delete this course.'}), 403

        # Delete associated entries from section_courses table
        cur.execute("DELETE FROM section_courses WHERE course_id = %s", (course_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from section_courses table")

        # Delete the course itself
        cur.execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from courses table")

        g.mysql.connection.commit()
        logger.debug("Changes committed to the database")

        return jsonify({'success': True, 'message': 'Course deleted successfully'}), 200

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()


# ========================================================Program1======================================================
@bp.route('/department_head_content/<int:program_id>')
def dep_head_content(program_id):
    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)

    # Get the current user's ID
    current_user_id = session.get('user_id')

    # Check if the program belongs to the current user
    cur = g.mysql.connection.cursor()
    try:
        cur.execute("SELECT user_id FROM programs WHERE program_id = %s", (program_id,))
        program_user_id = cur.fetchone()
        
        if not program_user_id:
            flash('Program not found.', 'error')
            return redirect(url_for('my_blueprint.program'))
        
        if program_user_id[0] != current_user_id:
            flash('You do not have permission to access this program.', 'error')
            return redirect(url_for('my_blueprint.program'))
        
        # If we reach here, the program belongs to the current user
        session['current_program_id'] = program_id

        # Adjusted query to join with faculty and select faculty names, including hours_per_week
        query_template = """
        SELECT courses.course_id, courses.course_code, courses.course_name, courses.course_block, courses.course_type, courses.units, courses.hours_per_week, CONCAT(faculties.first_name, ' ', faculties.last_name) AS faculty_name
        FROM courses
        LEFT JOIN faculties ON courses.faculty_id = faculties.faculty_id
        WHERE courses.program_id = %s AND courses.course_level = %s
        """

        # Fetch courses for each year level, including faculty names and hours_per_week
        courses1 = execute_query(query_template, (program_id, '1st Year'))
        courses2 = execute_query(query_template, (program_id, '2nd Year'))
        courses3 = execute_query(query_template, (program_id, '3rd Year'))
        courses4 = execute_query(query_template, (program_id, '4th Year'))

        faculties = []
        try:
            cur = g.mysql.connection.cursor()
            cur.execute("SELECT faculty_id, CONCAT(first_name, ' ', last_name) AS full_name FROM faculties WHERE department = %s",(session.get('department'),))
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
        return render_template('dep_head/dep_head_content.html',
                                courses1=courses1, courses2=courses2,
                                  courses3=courses3, courses4=courses4,
                                    form=form, faculty_choices=faculty_choices,
                                      current_endpoint=request.endpoint)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        flash('An error occurred while accessing the program.', 'error')
        return redirect(url_for('my_blueprint.program'))
    finally:
        cur.close()

class EditProgramForm(FlaskForm):
    program_name = StringField('Program Name', validators=[DataRequired()])
    submit = SubmitField('Update Program')

@bp.route('/edit-program/<int:program_id>', methods=['GET', 'POST'])
def edit_program(program_id):
    logger.debug(f"Received request for program_id: {program_id}")
    logger.debug(f"Request method: {request.method}")

    # Ownership check
    current_user_id = session.get('user_id')
    cur = g.mysql.connection.cursor()
    try:
        cur.execute("SELECT user_id FROM programs WHERE program_id = %s", (program_id,))
        program_user_id = cur.fetchone()

        if not program_user_id:
            flash('Program not found.', 'error')
            return redirect(url_for('my_blueprint.program'))

        if program_user_id[0] != current_user_id:
            flash('You do not have permission to edit this program.', 'error')
            return redirect(url_for('my_blueprint.program'))

        # If we reach here, the program belongs to the current user
        session['current_program_id'] = program_id

        # Fetch the program details
        cur.execute("SELECT program_name FROM programs WHERE program_id = %s", (program_id,))
        program_data = cur.fetchone()
        if not program_data:
            flash('Program not found.', 'error')
            return redirect(url_for('my_blueprint.program'))
        logger.debug(f"Fetched program data: {program_data}")

        # Prepare the form
        form = EditProgramForm()

        if form.validate_on_submit():
            logger.debug(f"Form validated successfully. Form data: {form.data}")
            logger.debug(f"Program name from form: {form.program_name.data}")
            logger.debug(f"Program name from database: {program_data[0]}")

            try:
                cur = g.mysql.connection.cursor()
                cur.execute("UPDATE programs SET program_name = %s WHERE program_id = %s",
                            (form.program_name.data, program_id))
                logger.debug(f"Affected rows: {cur.rowcount}")
                if cur.rowcount == 0:
                    logger.warning(f"No rows affected for program_id: {program_id}")
                    flash('No changes were made to the program.', 'warning')
                else:
                    g.mysql.connection.commit()
                    logger.debug("Changes committed to the database")
                    flash('Program updated successfully!', 'success')
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                flash('Failed to update program.', 'danger')
            finally:
                cur.close()

            return redirect(url_for('my_blueprint.program'))

        # Pre-populate the form with existing data
        form.program_name.data = program_data[0]

        return render_template('dep_head/edit_program.html',
                               form=form,
                               program_id=program_id,
                               current_endpoint=request.endpoint)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        flash('An error occurred while editing the program.', 'error')
        return redirect(url_for('my_blueprint.program'))
    finally:
        cur.close()



@bp.route('/delete-program/<int:program_id>', methods=['POST'])
def delete_program(program_id):
    logger.debug(f"Received request to delete program_id: {program_id}")
    
    # Ownership check
    current_user_id = session.get('user_id')
    cur = g.mysql.connection.cursor()
    try:
        cur.execute("SELECT user_id FROM programs WHERE program_id = %s", (program_id,))
        program_user_id = cur.fetchone()
        
        if not program_user_id:
            flash('Program not found.', 'error')
            return jsonify({"success": False, "message": "Program not found"}), 404
        
        if program_user_id[0] != current_user_id:
            flash('You do not have permission to delete this program.', 'error')
            return jsonify({"success": False, "message": "Permission denied"}), 403
        
        # Start a transaction
        g.mysql.connection.begin()
        
        # Delete associated sections from section_courses table
        cur.execute("DELETE FROM section_courses WHERE section_id IN (SELECT section_id FROM sections WHERE program_id = %s)", (program_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from section_courses table")
        
        # Delete associated sections from sections table
        cur.execute("DELETE FROM sections WHERE program_id = %s", (program_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from sections table")
        
        # Delete associated user_solutions for the deleted sections
        cur.execute("DELETE FROM user_solutions WHERE section_id IN (SELECT section_id FROM sections WHERE program_id = %s)", (program_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from user_solutions table")
        
        # Delete associated courses from courses table
        cur.execute("DELETE FROM courses WHERE program_id = %s", (program_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from courses table")
        
        # Now delete the program
        cur.execute("DELETE FROM programs WHERE program_id = %s", (program_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from programs table")
        
        # Commit the transaction
        g.mysql.connection.commit()
        logger.debug("Changes committed to the database")
        
        flash('Program and associated courses deleted successfully!', 'success')
        return jsonify({"success": True, "message": "Program and associated courses deleted successfully"}), 200
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # Rollback the transaction if an error occurs
        g.mysql.connection.rollback()
        flash('Failed to delete program.', 'danger')
        return jsonify({"success": False, "message": "Failed to delete program"}), 500
    
    finally:
        cur.close()


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



















# ========================================================Admin======================================================



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

@bp.route('/registrar/room')
def room():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'registrar':
        abort(403)
    return render_template('registrar/room.html')



@bp.route('/trial')
def trial():
    return render_template('dep_head/for_trial.html')