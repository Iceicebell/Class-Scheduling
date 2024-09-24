import csv
from io import StringIO
import io
import os
import re
import MySQLdb
import bcrypt
import logging
from werkzeug.utils import secure_filename
import os
import re
from typing import Optional
import bcrypt
from flask import Blueprint, Response, current_app, flash, jsonify, make_response, redirect, render_template, render_template_string, request, abort, session, url_for
from functools import wraps
from flask import g
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import BooleanField, FloatField, HiddenField, IntegerField, PasswordField, SelectField, StringField, SubmitField, TimeField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo, Optional
import logging
from datetime import datetime


bp = Blueprint('my_blueprint', __name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
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
        elif user_role == 'gen-ed': 
                return redirect(url_for('my_blueprint.gened'))  # Assuming 'program' is the route for department heads
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
        abort(403)
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') not in ['dept-head', 'gen-ed']:
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

        # flash('Faculty added successfully!', 'success')
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




# ========================================================SECTION1======================================================
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



def decimal_to_time(decimal_time):
    """Convert a decimal time (e.g., 8.5) to HH:MM format."""
    hours = int(decimal_time)
    minutes = int((decimal_time - hours) * 60)
    return f"{hours:02}:{minutes:02}"


@bp.route('/view-section/<int:section_id>')
def view_section(section_id):
    # Fetch section details from database
    form=AddUnavailableForm()
    cur = g.mysql.connection.cursor()
    cur.execute("SELECT * FROM sections WHERE section_id = %s", (section_id,))
    section_data = cur.fetchone()
    
    # Convert the tuple to a dictionary for easier access
    section = dict(zip([desc[0] for desc in cur.description], section_data))
    
    # Fetch program_id from the section
    program_id = section['program_id']
    session['current_section_id'] = section_id
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
    cur.execute("SELECT c.course_id, c.course_code, c.course_name, c.course_block FROM courses c JOIN section_courses sc ON c.course_id = sc.course_id WHERE sc.section_id = %s", (section_id,))
    selected_courses = cur.fetchall()

    cur.execute("""
        SELECT ut.id, ut.day_of_week, ut.start_time, ut.end_time
        FROM unavailable_times ut
        WHERE ut.section_id = %s
    """, (section_id,))
    unavailable_times_raw = cur.fetchall()

    unavailable_times = []
    for ut in unavailable_times_raw:
        start_time = decimal_to_time(ut[2])  # Convert start_time from decimal to HH:MM
        end_time = decimal_to_time(ut[3])    # Convert end_time from decimal to HH:MM
        unavailable_times.append((ut[0], ut[1], start_time, end_time))


    cur.close()
    return render_template('dep_head/view_section.html', section=section, all_courses=all_courses, selected_courses=selected_courses,unavailable_times=unavailable_times, form=form)

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

@bp.route('/api/delete-unavailable-time/<int:ut_id>', methods=['DELETE'])
def delete_unavailable_time(ut_id):
    cur = g.mysql.connection.cursor()
    try:
        cur.execute("DELETE FROM unavailable_times WHERE id = %s", (ut_id,))
        g.mysql.connection.commit()
        return jsonify({'success': True, 'message': 'Unavailable time deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()

@bp.route('/api/remove-course/<int:course_id>', methods=['DELETE'])
def remove_course(course_id):
    cur = g.mysql.connection.cursor()
    try:
        # Get the current section_id from the session
        section_id = session.get('current_section_id')
        
        if not section_id:
            return jsonify({'success': False, 'message': 'Section not found'}), 404
        
        # Delete the course from the section
        cur.execute("DELETE FROM section_courses WHERE course_id = %s AND section_id = %s", (course_id, section_id))
        
        if cur.rowcount == 0:
            return jsonify({'success': False, 'message': 'Course not found in this section'}), 404
        
        g.mysql.connection.commit()
        return jsonify({'success': True, 'message': 'Course removed from section successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()




class AddUnavailableForm(FlaskForm):
    day_of_week  = SelectField('Day Of Week', choices=[
        ('', '-- Please select --'),
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    ], validators=[DataRequired()])
    start_time = TimeField('Starting Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])


@bp.route('/add-unavaibletimes', methods=['GET', 'POST'])
def addUnavaibleTimes():
    form = AddUnavailableForm(request.form)
    cur = g.mysql.connection.cursor()
    logger.debug(f"Received request method: {request.method}")
    
    # Ensure user is logged in and has the correct role
    if session.get('isVerified') == False or 'user_id' not in session or session.get('user_role') != 'dept-head':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('signin'))
    
    if form.validate_on_submit():
        logger.debug("Form validated successfully")
        
        day_of_week = form.day_of_week.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        
        # Convert start and end times to decimal
        start_time_decimal = time_to_decimal(start_time)
        end_time_decimal = time_to_decimal(end_time)
        
        section_id = request.form.get('section_id')  # This value should be passed from the form or session

        try:
            cur = g.mysql.connection.cursor()
            logger.debug("Executing SQL query to add unavailable time...")
            
            cur.execute("""
                INSERT INTO unavailable_times (start_time, end_time, section_id, day_of_week)
                VALUES (%s, %s, %s, %s)
            """, (start_time_decimal, end_time_decimal, section_id, day_of_week))
            
            logger.debug(f"Affected rows: {cur.rowcount}")
            
            if cur.rowcount == 0:
                logger.warning("No rows were affected by the insert operation")
            
            g.mysql.connection.commit()
            cur.close()
            flash('Unavailable time added successfully!', 'success')
        except Exception as e:
            logger.error(f"Error adding unavailable time: {str(e)}")
            flash('Failed to add unavailable time.', 'danger')
        
        return redirect(url_for('my_blueprint.view_section',section_id=section_id))  # Redirect to the appropriate page
    
    else:
        logger.debug(f"Form validation failed. Errors: {form.errors}")
        flash('Form validation failed.', 'warning')
    
    return redirect(url_for('my_blueprint.view_section',section_id=section_id, form=form, current_endpoint=request.endpoint))

def time_to_decimal(time_value):
    """Convert time to decimal representation."""
    return time_value.hour + time_value.minute / 60

    















# ========================================================Course1======================================================

class AddCourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    course_code = StringField('Course Code', validators=[DataRequired()])
    units = StringField('Units', validators=[DataRequired()])
    hours_per_week = StringField('Hours Per Week', validators=[DataRequired()])
    course_block = StringField('Block', validators=[DataRequired()])
    course_type = SelectField('Type', choices=[ ('', '-- Please select --'),
        ('Lecture', 'Lecture'),
        ('Networking', 'Networking'),
        ('Comp Laboratory', 'Comp Laboratory'),
        ('Engineering Laboratory', 'Engineering Laboratory')], validators=[DataRequired()])
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
    course_type = SelectField('Type', choices=[ 
        ('', '-- Please select --'),
        ('Lecture', 'Lecture'),
        ('Networking', 'Networking'),
        ('Comp Laboratory', 'Comp Laboratory'),
        ('Engineering Laboratory', 'Engineering Laboratory')], validators=[DataRequired()])
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
        
        # Update the course
        cur.execute("UPDATE courses SET course_name = %s, course_code = %s, units = %s, hours_per_week = %s, course_block = %s, course_type = %s, course_level = %s, program_id = %s, faculty_id = %s WHERE course_id = %s",
                    (course_name, course_code, units, hours_per_week, course_block, db_course_type, db_year_level, program_id, new_faculty_id, course_id))
        logger.debug(f"Course updated successfully")

        # Update faculty_used_units for the old faculty (if it exists)
        if faculty_id:
            cur.execute("UPDATE faculties SET faculty_used_units = faculty_used_units - %s WHERE faculty_id = %s", (units, faculty_id))
            logger.debug(f"Updated faculty_used_units for old faculty {faculty_id}")

        # Update faculty_used_units for the new faculty (if it exists)
        if new_faculty_id:
            cur.execute("UPDATE faculties SET faculty_used_units = faculty_used_units + %s WHERE faculty_id = %s", (units, new_faculty_id))
            logger.debug(f"Updated faculty_used_units for new faculty {new_faculty_id}")

        g.mysql.connection.commit()
        logger.debug("Transaction committed")

    except Exception as e:
        logger.error(f"An error occurred during database operation: {str(e)}")
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
        

        if form.validate_on_submit():
            logger.debug(f"Form data: {form.data}")
            logger.debug(f"Faculty data: {form.faculty.data}")

            try:
                new_faculty_id = None if form.faculty.data == '' else form.faculty.data
                logger.debug(f"New faculty ID: {new_faculty_id}")

                # Fetch the current faculty ID
                cur = g.mysql.connection.cursor()
                cur.execute("SELECT faculty_id FROM courses WHERE course_id = %s", (course_id,))
                old_faculty_id = cur.fetchone()[0] if cur.rowcount > 0 else None
                logger.debug(f"Old faculty ID: {old_faculty_id}")

                if old_faculty_id == new_faculty_id:
                    logger.warning("New faculty is the same as old faculty. No change will occur.")
                    flash('No change was made to the course faculty.', 'warning')
                else:
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
                        faculty_id=old_faculty_id,
                        new_faculty_id=new_faculty_id
                    )
                    flash('Course updated successfully!', 'success')
            except Exception as e:
                logger.error(f"An error occurred during course update: {str(e)}")
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
        current_faculty_id = course_data[8]
        if current_faculty_id is not None:
            form.faculty.default = str(current_faculty_id)
        else:
            form.faculty.default = ''
        form.faculty.process_data(form.faculty.default)

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

















# ========================================================Admin1======================================================



@bp.route('/admin')
def admin():
    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'admin':
        abort(403)

    cur = g.mysql.connection.cursor()

    try:
        cur.execute("SELECT user_id, username, email, role, department, is_verified FROM users ORDER BY user_id ASC")
        users = cur.fetchall()
        logger.debug(f"Fetched users: {users}")  # Log fetched data
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        cur.close()
    
    return render_template('admin/user_table.html', users=users, current_endpoint=request.endpoint)



class EditUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("New Password")
    confirmPassword = PasswordField("Confirm Password", validators=[EqualTo('password')])
    role = SelectField("Role", choices=[
        ('admin', 'Admin'),
        ('gen-ed', 'Gen Ed'),
        ('registrar', 'Registrar'),
        ('dept-head', 'Department Head')], validators=[DataRequired()])
    department = SelectField("Department", choices=[
        ('REGISTRAR', 'REGISTRAR'),
        ('GENED', 'GENED'),
        ('CSIT', 'CSIT'),
        ('ENGINEERING', 'ENGINEERING'),
        ('SON', 'SON'),
        ('SBMA', 'SBMA'),
        ('SHOM', 'SHOM'),
        ('SEAS', 'SEAS')
    ], validators=[DataRequired()])
    submit = SubmitField("Update")

    def validate_password(self, field):
        if self.password.data != self.confirmPassword.data:
            raise ValidationError("Passwords do not match.")
        
    def validate_email(self, field):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', field.data):
            raise ValidationError("Invalid email address.")


@bp.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    logger.debug(f"Received request for user_id: {user_id}")
    logger.debug(f"Request method: {request.method}")

    # Ownership check
    current_user_role = session.get('user_role')
    cur = g.mysql.connection.cursor()
    try:
        cur.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
        user_role = cur.fetchone()

        if not user_role:
            flash('User not found.', 'error')
            return redirect(url_for('my_blueprint.admin'))

        if user_role[0] != 'admin' and current_user_role != 'admin':
            flash('You do not have permission to edit this user.', 'error')
            return redirect(url_for('my_blueprint.admin'))

        # If we reach here, the user can be edited
        session['current_user_id'] = user_id

        # Fetch the user details
        cur.execute("SELECT username, email, role, department FROM users WHERE user_id = %s", (user_id,))
        user_data = cur.fetchone()
        if not user_data:
            flash('User not found.', 'error')
            return redirect(url_for('my_blueprint.admin'))
        logger.debug(f"Fetched user data: {user_data}")

        # Prepare the form
        form = EditUserForm()

        if form.validate_on_submit():
            try:
                # Update user information
                cur.execute("UPDATE users SET username = %s, email = %s, role = %s, department = %s WHERE user_id = %s",
                            (form.username.data, form.email.data, form.role.data, form.department.data, user_id))
                g.mysql.connection.commit()
                logger.debug(f"Affected rows: {cur.rowcount}")
                if cur.rowcount == 0:
                    logger.warning(f"No rows affected for user_id: {user_id}")
                    flash('No changes were made to the user information.', 'warning')
                else:
                    flash('User information updated successfully!', 'success')

                # Update password only if provided
                if form.password.data:
                    hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())
                    cur.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_password, user_id))
                    g.mysql.connection.commit()
                    logger.debug(f"Password updated for user_id: {user_id}")
                    flash('Password updated successfully!', 'success')
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                flash('Failed to update user.', 'danger')
            finally:
                cur.close()

            return redirect(url_for('my_blueprint.admin'))
        else:
            # If form doesn't validate, populate form with user data and render the template
            form.username.data = user_data[0]
            form.email.data = user_data[1]
            form.role.data = user_data[2]
            form.department.data = user_data[3]

            # Check for validation errors
            if form.password.errors:
                flash(' '.join(form.password.errors), 'error')
            if form.confirmPassword.errors:
                flash(' '.join(form.confirmPassword.errors), 'error')
            
            # Check for email validation error specifically
            if form.email.errors:
                flash(form.email.errors[0], 'error')

            return render_template('admin/edit_account.html', form=form, user_id=user_id, current_endpoint=request.endpoint)

    except Exception as e:
        logger.error(f"An error occurred during ownership check: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
    finally:
        cur.close()

    return redirect(url_for('my_blueprint.admin'))

@bp.route('/disable-user/<int:user_id>', methods=['POST'])
def disable_user(user_id):
    try:
        cur = g.mysql.connection.cursor()
        cur.execute("UPDATE users SET is_verified = 0 WHERE user_id = %s", (user_id,))
        g.mysql.connection.commit()
        return jsonify({'success': True, 'message': 'User disabled successfully'})
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'success': False, 'message': 'Failed to disable user'}), 500
    finally:
        cur.close()

@bp.route('/enable-user/<int:user_id>', methods=['POST'])
def enable_user(user_id):
    try:
        cur = g.mysql.connection.cursor()
        cur.execute("UPDATE users SET is_verified = 1 WHERE user_id = %s", (user_id,))
        g.mysql.connection.commit()
        return jsonify({'success': True, 'message': 'User enabled successfully'})
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'success': False, 'message': 'Failed to enable user'}), 500
    finally:
        cur.close()


# ========================================================gened1======================================================
@bp.route('/gened', methods=['GET', 'POST'])
def gened():
    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'gen-ed':
        abort(403)
    return redirect(url_for('my_blueprint.genEd_courses'))


@bp.route('/gened_courses', methods=['GET', 'POST'])
def genEd_courses():
    form = AddGenEdCourseForm()
    if session.get('isVerified') == False:
        abort(403)
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'gen-ed':
        abort(403)

    # Fetch courses from gened_courses table
    try:
        cur = g.mysql.connection.cursor()
        query_template = """
            SELECT gc.course_id, gc.course_code, gc.course_name, gc.course_block, gc.units, gc.hours_per_week, gc.capacity,gc.type,
                CONCAT(f.first_name, ' ', f.last_name) AS faculty_name
            FROM gened_courses gc
            LEFT JOIN faculties f ON gc.faculty_id = f.faculty_id
            ORDER BY gc.course_code ASC
        """
        cur.execute(query_template)
        courses = cur.fetchall()
        cur.close()

        # Convert tuples to list of dictionaries for the template
        course_list = courses
    except Exception as e:
        print(e)
        course_list = []  # Fallback to empty list on error

    # Fetch faculty choices from the current user's department
    try:
        cur = g.mysql.connection.cursor()
        current_user_id = session.get('user_id')
        
        # First, fetch the department of the current user
        cur.execute("SELECT department FROM users WHERE user_id = %s", (current_user_id,))
        current_user_department = cur.fetchone()
        
        if current_user_department:
            department = current_user_department[0]
            # Now, fetch faculty members from the same department
            cur.execute("SELECT faculty_id, CONCAT(first_name, ' ', last_name) AS full_name FROM faculties WHERE department = %s", (department,))
            faculties = cur.fetchall()
            cur.close()

            # Convert tuples to list of (id, full_name) pairs for the SelectField choices
            faculty_choices = [(str(faculty[0]), faculty[1]) for faculty in faculties]
            logger.debug(f"Faculty choices: {faculty_choices}")
        else:
            faculty_choices = []
            logger.warning("User's department not found")
    except Exception as e:
        logger.error(f"Error fetching faculty choices: {e}")
        faculty_choices = []

    # Set the faculty choices for the form
    form.faculty.choices = faculty_choices

    return render_template('genEd/genEd_courses.html', form=form, course=course_list, faculty_choices=faculty_choices, current_endpoint=request.endpoint)



class AddGenEdCourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    course_code = StringField('Course Code', validators=[DataRequired()])
    units = StringField('Units', validators=[DataRequired()])
    hours_per_week = StringField('Hours Per Week', validators=[DataRequired()])
    course_block = StringField('Block', validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired()])
    course_type = SelectField('Type', choices=[ 
        ('', '-- Please select --'),
        ('Lecture', 'Lecture'),
        ('Networking', 'Networking'),
        ('Comp Laboratory', 'Comp Laboratory'),
        ('Engineering Laboratory', 'Engineering Laboratory')], validators=[DataRequired()])
    faculty = SelectField('Faculty', choices=[], validators=[Optional()])
    submit = SubmitField('Add Course')

def add_gen_ed_course_to_db(course_name, course_code, units, hours_per_week, course_block,capacity, course_type, faculty_id=None):
    cur = g.mysql.connection.cursor()
    try:
        # Adjust the INSERT statement according to your courses table structure
        cur.execute("INSERT INTO gened_courses (course_name, course_code, units, hours_per_week, course_block,capacity, type, faculty_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (course_name, course_code, units, hours_per_week, course_block,capacity, course_type, faculty_id))
        g.mysql.connection.commit()
        
        if faculty_id:
            cur.execute("""UPDATE faculties SET faculty_used_units = faculty_used_units + %s WHERE faculty_id = %s""", (units, faculty_id))
            g.mysql.connection.commit()
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # Handle exception, maybe rollback transaction here
    finally:
        cur.close()

@bp.route('/add_gened_course', methods=['GET', 'POST'])
def add_gened_course():
    # Initialize the form
    form = AddGenEdCourseForm(request.form)
    
    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'gen-ed':
        abort(403)
    
    # Fetch faculty choices
    try:
        cur = g.mysql.connection.cursor()
        cur.execute("SELECT faculty_id, CONCAT(first_name, ' ', last_name) AS full_name FROM faculties")
        faculties = cur.fetchall()
        cur.close()
        
        # Convert tuples to list of (id, full_name) pairs for the SelectField choices
        faculty_choices = [(str(faculty[0]), faculty[1]) for faculty in faculties]
        logger.debug(f"Faculty choices: {faculty_choices}")
        
        # Set the faculty choices for the form
        form.faculty.choices = faculty_choices
        
    except Exception as e:
        logger.error(f"Error fetching faculty choices: {e}")
        faculty_choices = []
    
    if form.validate_on_submit():
        logger.info("Form is valid")
        course_name = form.course_name.data
        course_code = form.course_code.data
        units = form.units.data
        hours_per_week = form.hours_per_week.data
        course_block = form.course_block.data
        capacity = form.capacity.data
        course_type = form.course_type.data
        faculty_id = form.faculty.data if form.faculty.data else None
        
        logger.info(f"Form data: course_name={course_name}, course_code={course_code}, units={units}, hours_per_week={hours_per_week}, course_block={course_block}, course_type={course_type}, faculty_id={faculty_id}")
        
        add_gen_ed_course_to_db(course_name, course_code, units, hours_per_week, course_block,capacity, course_type, faculty_id=faculty_id)
        flash('Course added successfully!', 'success')
        return redirect(url_for('my_blueprint.genEd_courses'))
    else:
        logger.error(f"Form validation failed: {form.errors}")
        flash('Failed to add course.', 'danger')
    
    # Render the template with the form
    return render_template('genEd/add_gened_course.html', form=form)


def update_gen_ed_course_to_db(course_id, course_name, course_code, units, hours_per_week, course_block, course_type, faculty_id=None, capacity=None):
    try:
        cur = g.mysql.connection.cursor()
        
        # Update the course
        cur.execute("UPDATE gened_courses SET course_name = %s, course_code = %s, units = %s, hours_per_week = %s, course_block = %s, type = %s, faculty_id = %s, capacity = %s WHERE course_id = %s",
                    (course_name, course_code, units, hours_per_week, course_block, course_type, faculty_id, capacity, course_id))
        g.mysql.connection.commit()
        
        # Update faculty_used_units for the faculty (if it exists)
        if faculty_id:
            cur.execute("UPDATE faculties SET faculty_used_units = faculty_used_units + %s WHERE faculty_id = %s", (units, faculty_id))
            g.mysql.connection.commit()
        
    except Exception as e:
        logger.error(f"An error occurred during database operation: {str(e)}")
        # Handle exception, maybe rollback transaction here
    finally:
        cur.close()


class EditGenEdCourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    course_code = StringField('Course Code', validators=[DataRequired()])
    units = StringField('Units', validators=[DataRequired()])
    hours_per_week = StringField('Hours Per Week', validators=[DataRequired()])
    course_block = StringField('Block', validators=[DataRequired()])
    course_type = SelectField('Type', choices=[ 
        ('', '-- Please select --'),
        ('Lecture', 'Lecture'),
        ('Networking', 'Networking'),
        ('Comp Laboratory', 'Comp Laboratory'),
        ('Engineering Laboratory', 'Engineering Laboratory')], validators=[DataRequired()])
    faculty = SelectField('Faculty', choices=[], validators=[Optional()])
    capacity = IntegerField('Capacity', validators=[DataRequired()])
    submit = SubmitField('Update Course')

# Route for editing a Gen Ed course
@bp.route('/edit-gened-course/<int:course_id>', methods=['GET', 'POST'])
def edit_gened_course(course_id):
    logger.debug(f"Received request for course_id: {course_id}")
    logger.debug(f"Request method: {request.method}")

    # Ownership check
    current_user_role = session.get('user_role')
    cur = g.mysql.connection.cursor()
    try:
        # Fetch the course details
        cur.execute("SELECT course_name, course_code, units, hours_per_week, course_block, type, faculty_id, capacity FROM gened_courses WHERE course_id = %s", (course_id,))
        course_data = cur.fetchone()
        if not course_data:
            flash('Course not found.', 'error')
            return redirect(url_for('my_blueprint.genEd_courses'))

        # Check if the user has permission to edit this course
        if current_user_role != 'gen-ed':
            flash('You do not have permission to edit this course.', 'error')
            return redirect(url_for('my_blueprint.genEd_courses'))

        # Fetch all faculties
        cur.execute("SELECT faculty_id, CONCAT(first_name, ' ', last_name) AS full_name FROM faculties WHERE department = %s", (session.get('department'),))
        faculties = cur.fetchall()

        # Create the form and set faculty choices
        form = EditGenEdCourseForm()
        form.faculty.choices = [('','No Faculty')] + [(str(faculty[0]), faculty[1]) for faculty in faculties]

        if form.validate_on_submit():
            logger.debug(f"Form data: {form.data}")
            logger.debug(f"Faculty data: {form.faculty.data}")

            try:
                new_faculty_id = None if form.faculty.data == '' else form.faculty.data
                logger.debug(f"New faculty ID: {new_faculty_id}")

                update_gen_ed_course_to_db(
                    course_id,
                    form.course_name.data,
                    form.course_code.data,
                    form.units.data,
                    form.hours_per_week.data,
                    form.course_block.data,
                    course_type=form.course_type.data,
                    faculty_id=new_faculty_id,
                    capacity=form.capacity.data
                )
                flash('Gen Ed course updated successfully!', 'success')
            except Exception as e:
                logger.error(f"An error occurred during course update: {str(e)}")
                flash('Failed to update course.', 'danger')

            return redirect(url_for('my_blueprint.genEd_courses'))

        # Pre-populate the form with existing data
        form.course_name.data = course_data[0]
        form.course_code.data = course_data[1]
        form.units.data = course_data[2]
        form.hours_per_week.data = course_data[3]
        form.course_block.data = course_data[4]
        form.course_type.data = course_data[5]
        form.faculty.data = str(course_data[6])
        form.capacity.data = course_data[7]

        return render_template('genEd/edit_gened_course.html',
                               form=form,
                               course_id=course_id,
                               current_endpoint=request.endpoint)

    except Exception as e:
        logger.error(f"An error occurred during ownership check: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
    finally:
        cur.close()

    return redirect(url_for('my_blueprint.genEd_courses'))

# Route for deleting a Gen Ed course
@bp.route('/delete-gened-course/<int:course_id>', methods=['DELETE'])
def delete_gened_course(course_id):
    try:
        cur = g.mysql.connection.cursor()
        
        # Check if the course exists
        cur.execute("SELECT * FROM gened_courses WHERE course_id = %s", (course_id,))
        course = cur.fetchone()
        if not course:
            return jsonify({'success': False, 'message': 'Course not found.'}), 404

        # Delete the course
        cur.execute("DELETE FROM gened_courses WHERE course_id = %s", (course_id,))
        g.mysql.connection.commit()
        logger.debug(f"Gen Ed course with ID {course_id} deleted successfully")

        # Update faculty_used_units if the course had a faculty assigned
        if course[5]:  # Check if faculty_id is not None
            cur.execute("UPDATE faculties SET faculty_used_units = faculty_used_units - %s WHERE faculty_id = %s", (course[2], course[5]))
            logger.debug(f"Updated faculty_used_units for faculty {course[5]}")

        return jsonify({'success': True, 'message': 'Gen Ed course deleted successfully'}), 200

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()


@bp.route('/gened-create', methods=['GET', 'POST'])
def gened_create():
    if session.get('isVerified') == False:
        abort(403)
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'gen-ed':
        abort(403)

    cur = g.mysql.connection.cursor()

    display_schedule = {}
    faculty_timetable = {}

    # Fetch the existing schedule from created_gened_schedules table
    cur.execute("""
        SELECT gs.course_id, gs.day, gs.start_hour, gs.duration, gc.course_code, gc.course_block, f.first_name, f.last_name
        FROM created_gened_schedules gs
        JOIN gened_courses gc ON gs.course_id = gc.course_id
        JOIN faculties f ON gc.faculty_id = f.faculty_id
        WHERE gs.user_id = %s
    """, (session['user_id'],))
    saved_solutions = cur.fetchall()

    # Process the schedule data
    for course_id, day, start_hour, duration, course_code, course_block, first_name, last_name in saved_solutions:
        if course_id != -1:  # Ignore unavailable times
            course_key = f"{course_code}/{course_block}"

            # Update student timetable
            if course_key not in display_schedule:
                display_schedule[course_key] = {}
            if day not in display_schedule[course_key]:
                display_schedule[course_key][day] = []
            display_schedule[course_key][day].append({
                'start_hour': f"{int(start_hour)}:{int((start_hour % 1) * 60):02d}",
                'end_hour': f"{int(start_hour + duration)}:{int(((start_hour + duration) % 1) * 60):02d}"
            })

            # Update faculty timetable
            full_name = f"{first_name} {last_name}"
            if full_name not in faculty_timetable:
                faculty_timetable[full_name] = {'courses': {}}
            if course_key not in faculty_timetable[full_name]['courses']:
                faculty_timetable[full_name]['courses'][course_key] = {}
            if day not in faculty_timetable[full_name]['courses'][course_key]:
                faculty_timetable[full_name]['courses'][course_key][day] = {
                    'start_hour': f"{int(start_hour)}:{int((start_hour % 1) * 60):02d}",
                    'end_hour': f"{int(start_hour + duration)}:{int(((start_hour + duration) % 1) * 60):02d}"
                }

    # Handle POST request to apply the generated schedule
    if request.method == 'POST':
        try:
            g.mysql.connection.begin()

            # Remove existing data from the created_schedules table for the current user
            cur.execute("DELETE FROM created_gened_schedules WHERE user_id = %s", (session['user_id'],))
            
            # Fetch the current user's data from the user_solutions table
            cur.execute("""
                SELECT user_id, course_id, day, start_hour, duration, course_code, course_block
                FROM gened_solutions
                WHERE user_id = %s
            """, (session['user_id'],))
            user_solutions = cur.fetchall()

            # Insert the fetched data into the created_schedules table
            for user_id, course_id, day, start_hour, duration, course_code, course_block in user_solutions:
                cur.execute("""
                    INSERT INTO created_gened_schedules (user_id, course_id, day, start_hour, duration, course_code, course_block)
                    VALUES ( %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, course_id, day, start_hour, duration, course_code, course_block))
            
            g.mysql.connection.commit()
            flash("Generated schedule applied successfully!", "success")
            return redirect(url_for('my_blueprint.gened_create'))
        except Exception as e:
            g.mysql.connection.rollback()
            print(f"Error: {e}")
            flash("An error occurred while applying the generated schedule. Please try again.", "danger")

    # Render the template with both student and faculty timetables
    return render_template('genEd/gened_create.html',
                           student_schedule=display_schedule,
                           faculty_timetable=faculty_timetable,
                           current_endpoint=request.endpoint)




class EditGenEdScheduleForm(FlaskForm):
    day = SelectField('Day', choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday')
    ], validators=[DataRequired()])
    start_hour = TimeField('Start Hour', validators=[DataRequired()])
    duration = FloatField('Duration', validators=[DataRequired()])
    submit = SubmitField('Update Schedule')

@bp.route('/edit-gened-schedule/<string:course_code>/<string:course_block>', methods=['GET', 'POST'])
def edit_gened_schedule(course_code, course_block):
    logger.debug(f"Received request for course_code: {course_code}, course_block: {course_block}")
    logger.debug(f"Request method: {request.method}")

    # Ownership check
    current_user_role = session.get('user_role')
    logger.debug(f"Current user role: {current_user_role}")
    cur = g.mysql.connection.cursor()
    try:
        # Fetch the course_id using course_code and course_block
        cur.execute("SELECT course_id FROM gened_courses WHERE course_code = %s AND course_block = %s", (course_code, course_block))
        course_data = cur.fetchone()
        if not course_data:
            flash('Course not found.', 'error')
            return redirect(url_for('my_blueprint.gened_create'))

        course_id = course_data[0]

        # Fetch the schedule data
        cur.execute("SELECT id FROM created_gened_schedules WHERE course_id = %s", (course_id,))
        schedule_data = cur.fetchall()
        logger.debug(f"Fetched schedule data: {schedule_data}")

        if not schedule_data:
            flash('Schedule not found.', 'error')
            return redirect(url_for('my_blueprint.gened_create'))

        if current_user_role != 'gen-ed':
            flash('You do not have permission to edit this schedule.', 'error')
            return redirect(url_for('my_blueprint.gened_create'))

        # If we reach here, the schedule can be edited
        session['current_schedule_ids'] = [data[0] for data in schedule_data]
        logger.debug(f"Current schedule IDs: {session['current_schedule_ids']}")

        # Fetch the schedule details
        cur.execute("SELECT id, day, start_hour, duration FROM created_gened_schedules WHERE course_id = %s", (course_id,))
        schedule_details = cur.fetchall()
        logger.debug(f"Fetched schedule details: {schedule_details}")

        if not schedule_details:
            flash('Schedule not found.', 'error')
            return redirect(url_for('my_blueprint.gened_create'))

        # Prepare the forms
        forms = []
        if request.method == 'POST':
            for schedule in schedule_details:
                form = EditGenEdScheduleForm(request.form, prefix=str(schedule[0]))
                forms.append((form, schedule[0]))

            all_valid = True
            for form, schedule_id in forms:
                if form.validate_on_submit():
                    try:
                        # Convert start_hour to decimal
                        start_hour_time = form.start_hour.data
                        start_hour_decimal = start_hour_time.hour + start_hour_time.minute / 60
                        logger.debug(f"Converted start hour to decimal: {start_hour_decimal}")

                        # Update schedule information
                        cur.execute("UPDATE created_gened_schedules SET day = %s, start_hour = %s, duration = %s WHERE id = %s",
                                    (form.day.data, start_hour_decimal, form.duration.data, schedule_id))
                    except Exception as e:
                        logger.error(f"An error occurred during update: {e}")
                        flash('Failed to update schedule.', 'danger')
                        all_valid = False
                else:
                    all_valid = False

            if all_valid:
                g.mysql.connection.commit()
                logger.debug(f"Affected rows: {cur.rowcount}")
                flash('Schedule information updated successfully!', 'success')
            else:
                flash('Some forms contain errors. Please correct them and try again.', 'danger')

            return redirect(url_for('my_blueprint.gened_create'))
        else:
            for schedule in schedule_details:
                form = EditGenEdScheduleForm(prefix=str(schedule[0]))
                form.day.data = schedule[1]
                form.start_hour.data = datetime.strptime(str(schedule[2]), '%H.%M').time()
                form.duration.data = schedule[3]
                forms.append((form, schedule[0]))

        return render_template('genEd/edit_gened_schedule.html', forms=forms, course_code=course_code, course_block=course_block, current_endpoint=request.endpoint)

    except Exception as e:
        logger.error(f"An error occurred during ownership check: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
    finally:
        cur.close()

    return redirect(url_for('my_blueprint.gened_create'))

















# ==============Registrar1==================
@bp.route('/registrar')
def registrar():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'registrar':
        abort(403)
    return redirect(url_for('my_blueprint.room'))

@bp.route('/registrar/room')
def room():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'registrar':
        abort(403)

    form=AddRoomForm()

    cur = g.mysql.connection.cursor()
    try:
        # Adjusted query to select rooms, including floor levels
        query_template = """
        SELECT classrooms.room_id, classrooms.room_no, classrooms.capacity, classrooms.type, classrooms.floor_level
        FROM classrooms
        WHERE classrooms.floor_level = %s
        """

        # Fetch rooms for each floor level
        rooms1 = execute_query(query_template, ('1',))
        rooms2 = execute_query(query_template, ('2',))
        rooms3 = execute_query(query_template, ('3',))
        rooms4 = execute_query(query_template, ('4',))

        return render_template('registrar/room.html',rooms1=rooms1,rooms2=rooms2,rooms3=rooms3,rooms4=rooms4, form=form,current_endpoint=request.endpoint)
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        flash('An error occurred while accessing the rooms.', 'error')
        return redirect(url_for('my_blueprint.room'))
    finally:
        cur.close()
    




class AddRoomForm(FlaskForm):
    room_number = StringField('Room No', validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired()])
    room_type = SelectField('Room Type', choices=[
        ('', '-- Please select --'),
        ('Lecture', 'Lecture'),
        ('Networking', 'Networking'),
        ('Comp Laboratory', 'Comp Laboratory'),
        ('Engineering Laboratory', 'Engineering Laboratory')
    ], validators=[DataRequired()])
    floor_level = SelectField('Floor Level', choices=[
        ('', '-- Please select --'),
        ('1', '1st Floor'),
        ('2', '2nd Floor'),
        ('3', '3rd Floor'),
        ('4', '4th Floor')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Room')

def add_room_to_db(room_number, capacity, room_type, floor_level):
    from flask import g
    cur = g.mysql.connection.cursor()
    try:
        # Adjust the INSERT statement according to your rooms table structure
        cur.execute("INSERT INTO classrooms (room_no, capacity, type, floor_level) VALUES (%s, %s, %s, %s)",
                    (room_number, capacity, room_type, floor_level))
        g.mysql.connection.commit()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        # Handle exception, maybe rollback transaction here
    finally:
        cur.close()

@bp.route('/add_room', methods=['GET', 'POST'])
def add_room():
    # Initialize the form
    form = AddRoomForm(request.form)

    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'registrar':
        abort(403)

    if form.validate_on_submit():
        logger.info("Form is valid")
        room_number = form.room_number.data
        capacity = form.capacity.data
        room_type = form.room_type.data
        floor_level = form.floor_level.data

        logger.info(f"Form data: room_no={room_number}, capacity={capacity}, room_type={room_type}, floor_level={floor_level}")

        # Check if the room_no already exists
        from flask import g
        cur = g.mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM classrooms WHERE room_no = %s", (room_number,))
            existing_room = cur.fetchone()
            if existing_room:
                logger.warning(f"Room with number {room_number} already exists.")
                return render_template_string('''
                <script>
                alert("Room with this number already exists. Please choose a different number.");
                window.location.href = "{{ url_for('my_blueprint.room') }}";
                </script>
                ''')
        except Exception as e:
            logger.error(f"An error occurred while checking for existing room: {str(e)}")
            flash('An error occurred while processing your request.', 'error')
            return redirect(url_for('my_blueprint.room', form=form))
        finally:
            cur.close()

        # If the room doesn't exist, add it to the database
        add_room_to_db(room_number, capacity, room_type, floor_level)
        flash('Room added successfully!', 'success')
        return redirect(url_for('my_blueprint.room'))
    else:
        logger.error(f"Form validation failed: {form.errors}")
        flash('Failed to add room.', 'danger')

    # Render the template with the form
    return redirect(url_for('my_blueprint.room', form=form))

class EditRoomForm(FlaskForm):
    room_number = StringField('Room No', validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired()])
    room_type = SelectField('Room Type', choices=[
        ('', '-- Please select --'),
        ('Lecture', 'Lecture'),
        ('Networking', 'Networking'),
        ('Comp Laboratory', 'Comp Laboratory'),
        ('Engineering Laboratory', 'Engineering Laboratory')
    ], validators=[DataRequired()])
    floor_level = SelectField('Floor Level', choices=[
        (0, '-- Please select --'),
        (1, '1st Floor'),
        (2, '2nd Floor'),
        (3, '3rd Floor'),
        (4, '4th Floor')
    ], validators=[DataRequired()])
    submit = SubmitField('Update Room')
    
@bp.route('/edit-room/<int:room_id>', methods=['GET', 'POST'])
def edit_room(room_id):
    logger.debug(f"Received request for room_id: {room_id}")
    logger.debug(f"Request method: {request.method}")

    # Ownership check
    current_user_role = session.get('user_role')
    cur = g.mysql.connection.cursor()
    try:
        cur.execute("SELECT room_id, room_no FROM classrooms WHERE room_id = %s", (room_id,))
        room_data = cur.fetchone()

        if not room_data:
            flash('Room not found.', 'error')
            return redirect(url_for('my_blueprint.room'))

        if current_user_role != 'registrar':
            flash('You do not have permission to edit this room.', 'error')
            return redirect(url_for('my_blueprint.room'))

        # If we reach here, the room can be edited
        session['current_room_id'] = room_id

        # Fetch the room details
        cur.execute("SELECT room_id, room_no, capacity, type, floor_level FROM classrooms WHERE room_id = %s", (room_id,))
        room_data = cur.fetchone()
        if not room_data:
            flash('Room not found.', 'error')
            return redirect(url_for('my_blueprint.room'))
        logger.debug(f"Fetched room data: {room_data}")

        # Prepare the form
        form = EditRoomForm()

        if form.validate_on_submit():
            try:
                # Update room information
                cur.execute("UPDATE classrooms SET room_no = %s, capacity = %s, type = %s, floor_level = %s WHERE room_id = %s",
                            (form.room_number.data, form.capacity.data, form.room_type.data, form.floor_level.data, room_id))
                g.mysql.connection.commit()
                logger.debug(f"Affected rows: {cur.rowcount}")
                if cur.rowcount == 0:
                    logger.warning(f"No rows affected for room_id: {room_id}")
                    flash('No changes were made to the room information.', 'warning')
                else:
                    flash('Room information updated successfully!', 'success')
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                flash('Failed to update room.', 'danger')
            finally:
                cur.close()

            return redirect(url_for('my_blueprint.room'))
        else:
            # If form doesn't validate, populate form with room data and render the template
            form.room_number.data = room_data[1]
            form.capacity.data = room_data[2]
            form.room_type.data = room_data[3]
            form.floor_level.data = str(room_data[4])  # Convert int to str for SelectField

            # Check for validation errors
            if form.room_number.errors:
                flash(' '.join(form.room_number.errors), 'error')
            if form.capacity.errors:
                flash(' '.join(form.capacity.errors), 'error')
            if form.room_type.errors:
                flash(' '.join(form.room_type.errors), 'error')
            if form.floor_level.errors:
                flash(' '.join(form.floor_level.errors), 'error')

            return render_template('registrar/edit_room.html', form=form, room_id=room_id, current_endpoint=request.endpoint)

    except Exception as e:
        logger.error(f"An error occurred during ownership check: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
    finally:
        cur.close()

    return redirect(url_for('my_blueprint.room'))

@bp.route('/delete-room/<string:room_id>', methods=['DELETE'])
def delete_room(room_id):
    try:
        cur = g.mysql.connection.cursor()
        
        # Check if the room exists
        cur.execute("SELECT * FROM classrooms WHERE room_id = %s", (room_id,))
        room = cur.fetchone()
        if not room:
            return jsonify({'success': False, 'message': 'Room not found.'}), 404

        # Delete the room
        cur.execute("DELETE FROM classrooms WHERE room_id = %s", (room_id,))
        logger.debug(f"Deleted {cur.rowcount} entries from classrooms table")

        g.mysql.connection.commit()
        logger.debug("Changes committed to the database")

        return jsonify({'success': True, 'message': 'Room deleted successfully'}), 200

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cur.close()


@bp.route('/registrar/courses')
def registrar_courses():
    if session.get('isVerified') == False:
        abort(403)
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'registrar':
        abort(403)

    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    department_filter = request.args.get('department', '', type=str)

    cur = g.mysql.connection.cursor()

    # Fetch available departments
    cur.execute("SELECT DISTINCT department FROM room_courses")
    departments = cur.fetchall()

    if department_filter:
        query = """
            SELECT course_code, block, department, start_time, end_time, day 
            FROM room_courses 
            WHERE department = %s 
            ORDER BY course_code ASC 
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (department_filter, per_page, offset))
        courses = cur.fetchall()

        count_query = "SELECT COUNT(*) FROM room_courses WHERE department = %s"
        cur.execute(count_query, (department_filter,))
    else:
        query = """
            SELECT course_code, block, department, start_time, end_time, day 
            FROM room_courses 
            ORDER BY course_code ASC 
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (per_page, offset))
        courses = cur.fetchall()

        count_query = "SELECT COUNT(*) FROM room_courses"
        cur.execute(count_query)

    total_courses_result = cur.fetchone()
    total_courses = total_courses_result[0] if total_courses_result else 0
    cur.close()

    total_pages = (total_courses + per_page - 1) // per_page

    # Convert decimal times to HH:MM format
    courses = [
        (
            course[0],  # course_code
            course[1],  # block
            course[2],  # department
            convert_decimal_to_time(course[3]),  # start_time
            convert_decimal_to_time(course[4]),  # end_time
            course[5]   # day
        )
        for course in courses
    ]

    return render_template('registrar/registrar_courses.html', current_endpoint=request.endpoint, 
                           courses=courses, page=page, total_pages=total_pages, 
                           departments=departments, 
                           department_filter=department_filter)

def convert_decimal_to_time(decimal_time):
    try:
        hours = int(decimal_time)
        minutes = int((decimal_time - hours) * 60)
        return f"{hours:02}:{minutes:02}"
    except (TypeError, ValueError):
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/import-csv', methods=['POST'])
def import_csv():
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Ensure the upload directory exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        file.save(filepath)
        process_csv(filepath)
        flash('File successfully uploaded and processed', 'success')
        return redirect(url_for('my_blueprint.registrar_courses'))
    else:
        flash('Allowed file types are csv', 'danger')
        return redirect(request.url)

def process_csv(filepath):
    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            course_code = row['Course Code']
            capacity = row['Capacity']
            course_type = row['Type']
            block = row['Course Block']
            department = row['Department']
            start_time = convert_time_to_decimal(row['Start Time'])
            end_time = convert_time_to_decimal(row['End Time'])
            day = row['Day']
            # Insert into room_courses table
            cur = g.mysql.connection.cursor()
            query = """
            INSERT INTO room_courses (course_code, capacity, type, block, department, start_time, end_time, day)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(query, (course_code, capacity, course_type, block, department, start_time, end_time, day))
            g.mysql.connection.commit()
            cur.close()
    os.remove(filepath)

def convert_time_to_decimal(time_str):
    try:
        # Parse time in HH:MM format
        time_obj = datetime.strptime(time_str, '%H:%M')
        # Convert to decimal hours
        decimal_time = time_obj.hour + time_obj.minute / 60.0
        return decimal_time
    except ValueError:
        # If parsing fails, return None or handle the error as needed
        return None
    
@bp.route('/apply_schedule', methods=['POST'])
def apply_schedule():
    try:
        # Fetch data from the allocations table
        cur = g.mysql.connection.cursor()
        cur.execute("""
            SELECT course_id, room_id
            FROM allocations
        """)
        allocations = cur.fetchall()

        # Insert the fetched data into the final_allocations table
        for course_id, room_id in allocations:
            cur.execute("""
                INSERT INTO final_allocations (course_id, room_id)
                VALUES (%s, %s)
            """, (course_id, room_id))
        
        g.mysql.connection.commit()
        return redirect(url_for('my_blueprint.create_room_schedule'))
    except Exception as e:
        g.mysql.connection.rollback()
        return jsonify(success=False, error=str(e))


@bp.route('/registrar/create-schedule')
def create_room_schedule():
    if session.get('isVerified') == False:
        abort(403)
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'registrar':
        abort(403)
    
    floor_level = request.args.get('floor_level', 1, type=int)
    
    cur = g.mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Fetch classrooms for the selected floor level
    cur.execute("SELECT * FROM classrooms WHERE floor_level = %s", (floor_level,))
    classrooms = cur.fetchall()
    
    # Fetch allocations and join with room_courses to get course details
    classroom_ids = [classroom['room_id'] for classroom in classrooms]
    if classroom_ids:
        format_strings = ','.join(['%s'] * len(classroom_ids))
        query = f"""
            SELECT fa.*, rc.course_code, rc.block, rc.department, rc.start_time, rc.end_time, rc.day
            FROM final_allocations fa
            JOIN room_courses rc ON fa.course_id = rc.course_id
            WHERE fa.room_id IN ({format_strings})
        """
        cur.execute(query, tuple(classroom_ids))
        allocations = cur.fetchall()
    else:
        allocations = []
    
    # Fetch the list of departments
    cur.execute("SELECT DISTINCT department FROM room_courses")
    departments = cur.fetchall()
    
    cur.close()
    
    # Group allocations by room_id
    room_allocations = {}
    for allocation in allocations:
        room_id = allocation['room_id']
        if room_id not in room_allocations:
            room_allocations[room_id] = []
        room_allocations[room_id].append(allocation)
    
    # Convert decimal times to HH:MM format
    for room_id, room_allocation in room_allocations.items():
        for allocation in room_allocation:
            allocation['start_time'] = decimal_to_time(allocation['start_time'])
            allocation['end_time'] = decimal_to_time(allocation['end_time'])
    
    return render_template('registrar/registrar_schedule.html',
                           current_endpoint=request.endpoint,
                           classrooms=classrooms,
                           room_allocations=room_allocations,
                           floor_level=floor_level,
                           departments=departments)

# ========================================================CREATE SCHEDULE======================================================

def generate_faculty_timetable(cursor, current_user_id):
    faculty_timetable = {}
    
    # Fetch faculty names for the current user's sections
    cursor.execute("""
        SELECT faculty_id, first_name, last_name 
        FROM faculties 
        WHERE faculty_id IN (
            SELECT faculty_id 
            FROM courses 
            WHERE course_id IN (
                SELECT course_id 
                FROM section_courses 
                WHERE section_id IN (
                    SELECT section_id 
                    FROM sections 
                    WHERE user_id = %s
                )
            )
        )
    """, (current_user_id,))
    faculty_data = cursor.fetchall()
    faculty_names = {faculty_id: f"{first_name} {last_name}" for faculty_id, first_name, last_name in faculty_data}
    
    # Fetch all course assignments from the created_schedules table
    cursor.execute("""
        SELECT user_id, section_id, course_id, day, start_hour, duration, course_code, course_block 
        FROM created_schedules
    """)
    course_assignments = cursor.fetchall()
    
    # Iterate through the course assignments
    for user_id, section_id, course_id, day, start_hour, duration, course_code, course_block in course_assignments:
        # Fetch faculty ID for this course
        cursor.execute("SELECT faculty_id FROM courses WHERE course_id = %s", (course_id,))
        result = cursor.fetchone()
        faculty_id = result[0] if result else None
        
        if faculty_id and faculty_id in faculty_names:
            faculty_name = faculty_names[faculty_id]
            
            if faculty_name not in faculty_timetable:
                faculty_timetable[faculty_name] = {'courses': {}, 'unavailable': {}}
            
            course_key = f"{course_code}/{course_block}"
            if course_key not in faculty_timetable[faculty_name]['courses']:
                faculty_timetable[faculty_name]['courses'][course_key] = {}
            faculty_timetable[faculty_name]['courses'][course_key][day] = {
                'start_hour': f"{int(start_hour)}:{int((start_hour % 1) * 60):02d}",
                'end_hour': f"{int(start_hour + duration)}:{int(((start_hour + duration) % 1) * 60):02d}"
            }
    
    return faculty_timetable

@bp.route('/department-head/create', methods=['GET', 'POST'])
def create():
    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)

    cur = g.mysql.connection.cursor()

    if request.method == 'POST':
        try:
            # Start a transaction
            g.mysql.connection.begin()

            # Remove existing data from the created_schedules table for the current user
            cur.execute("DELETE FROM created_schedules WHERE user_id = %s", (session['user_id'],))
            
            # Fetch the current user's data from the user_solutions table
            cur.execute("""
                SELECT user_id, section_id, course_id, day, start_hour, duration, course_code, course_block
                FROM user_solutions
                WHERE user_id = %s
            """, (session['user_id'],))
            user_solutions = cur.fetchall()

            # Insert the fetched data into the created_schedules table
            for user_id, section_id, course_id, day, start_hour, duration, course_code, course_block in user_solutions:
                cur.execute("""
                    INSERT INTO created_schedules (user_id, section_id, course_id, day, start_hour, duration, course_code, course_block)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (user_id, section_id, course_id, day, start_hour, duration, course_code, course_block))
            
            # Commit the transaction
            g.mysql.connection.commit()

            return redirect(url_for('my_blueprint.create'))
        except Exception as e:
            # Rollback the transaction in case of error
            g.mysql.connection.rollback()
            # Log the error or handle it as needed
            print(f"Error: {e}")
            flash("An error occurred while applying the generated schedule. Please try again.", "danger")

    # Fetch the saved schedule from the created_schedules table
    cur.execute("""
        SELECT user_id, section_id, course_id, day, start_hour, duration, course_code, course_block
        FROM created_schedules
        WHERE user_id = %s
    """, (session['user_id'],))
    saved_schedules = cur.fetchall()
    
    # Fetch all sections owned by the current user
    cur.execute("SELECT section_id, section_name FROM sections WHERE user_id = %s", (session['user_id'],))
    sections = cur.fetchall()
    
    # Create a dictionary mapping section_ids to section_names
    section_names = {row[0]: row[1] for row in sections}

    display_schedule = {}
    for user_id, section_id, course_id, day, start_hour, duration, course_code, course_block in saved_schedules:
        section_name = section_names.get(section_id, f"Section {section_id}")
        if section_name not in display_schedule:
            display_schedule[section_name] = {'courses': {}, 'unavailable': {}}
            
        if course_id == -1:  # Unavailable time
            if day not in display_schedule[section_name]['unavailable']:
                display_schedule[section_name]['unavailable'][day] = []
            display_schedule[section_name]['unavailable'][day].append({
                    'start_hour': f"{int(start_hour)}:{int((start_hour % 1) * 60):02d}",
                    'end_hour': f"{int(start_hour + duration)}:{int(((start_hour + duration) % 1) * 60):02d}"
                })
        else:  # Regular course
            course_key = f"{course_code}/{course_block}"
            if course_key not in display_schedule[section_name]['courses']:
                display_schedule[section_name]['courses'][course_key] = {}
            display_schedule[section_name]['courses'][course_key][day] = {
                    'start_hour': f"{int(start_hour)}:{int((start_hour % 1) * 60):02d}",
                    'end_hour': f"{int(start_hour + duration)}:{int(((start_hour + duration) % 1) * 60):02d}"
                }

    faculty_timetable = generate_faculty_timetable(cur, session['user_id'])
    
    # Render the template with the fetched schedule
    return render_template('dep_head/create_schedule.html',
                           schedule=display_schedule,
                           faculty_timetable=faculty_timetable,
                           sections=sections,
                           current_endpoint=request.endpoint)

class EditScheduleForm(FlaskForm):
    day = SelectField('Day', choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday')
    ], validators=[DataRequired()])
    start_hour = TimeField('Start Hour', validators=[DataRequired()])
    duration = FloatField('Duration', validators=[DataRequired()])
    submit = SubmitField('Update Schedule')

@bp.route('/edit-schedule/<string:course_code>/<string:course_block>', methods=['GET', 'POST'])
def edit_schedule(course_code, course_block):
    logger.debug(f"Received request for course_code: {course_code}, course_block: {course_block}")
    logger.debug(f"Request method: {request.method}")

    # Ownership check
    current_user_role = session.get('user_role')
    logger.debug(f"Current user role: {current_user_role}")
    cur = g.mysql.connection.cursor()
    try:
        cur.execute("SELECT id FROM created_schedules WHERE course_code = %s AND course_block = %s", (course_code, course_block))
        schedule_data = cur.fetchall()
        logger.debug(f"Fetched schedule data: {schedule_data}")

        if not schedule_data:
            flash('Schedule not found.', 'error')
            return redirect(url_for('my_blueprint.schedule'))

        if current_user_role != 'dept-head':
            flash('You do not have permission to edit this schedule.', 'error')
            return redirect(url_for('my_blueprint.schedule'))

        # If we reach here, the schedule can be edited
        session['current_schedule_ids'] = [data[0] for data in schedule_data]
        logger.debug(f"Current schedule IDs: {session['current_schedule_ids']}")

        # Fetch the schedule details
        cur.execute("SELECT id, day, start_hour, duration FROM created_schedules WHERE course_code = %s AND course_block = %s", (course_code, course_block))
        schedule_details = cur.fetchall()
        logger.debug(f"Fetched schedule details: {schedule_details}")

        if not schedule_details:
            flash('Schedule not found.', 'error')
            return redirect(url_for('my_blueprint.create'))

        # Prepare the forms
        forms = []
        if request.method == 'POST':
            for schedule in schedule_details:
                form = EditScheduleForm(request.form, prefix=str(schedule[0]))
                forms.append((form, schedule[0]))

            all_valid = True
            for form, schedule_id in forms:
                if form.validate_on_submit():
                    try:
                        # Convert start_hour to decimal
                        start_hour_time = form.start_hour.data
                        start_hour_decimal = start_hour_time.hour + start_hour_time.minute / 60
                        logger.debug(f"Converted start hour to decimal: {start_hour_decimal}")

                        # Update schedule information
                        cur.execute("UPDATE created_schedules SET day = %s, start_hour = %s, duration = %s WHERE id = %s",
                                    (form.day.data, start_hour_decimal, form.duration.data, schedule_id))
                    except Exception as e:
                        logger.error(f"An error occurred during update: {e}")
                        flash('Failed to update schedule.', 'danger')
                        all_valid = False
                else:
                    all_valid = False

            if all_valid:
                g.mysql.connection.commit()
                logger.debug(f"Affected rows: {cur.rowcount}")
                flash('Schedule information updated successfully!', 'success')
            else:
                flash('Some forms contain errors. Please correct them and try again.', 'danger')

            return redirect(url_for('my_blueprint.schedule'))
        else:
            for schedule in schedule_details:
                form = EditScheduleForm(prefix=str(schedule[0]))
                form.day.data = schedule[1]
                form.start_hour.data = datetime.strptime(str(schedule[2]), '%H.%M').time()
                form.duration.data = schedule[3]
                forms.append((form, schedule[0]))

        return render_template('dep_head/edit_schedule.html', forms=forms, course_code=course_code, course_block=course_block, current_endpoint=request.endpoint)

    except Exception as e:
        logger.error(f"An error occurred during ownership check: {str(e)}")
        flash('An error occurred while processing your request.', 'error')
    finally:
        cur.close()

    return redirect(url_for('my_blueprint.create'))


@bp.route('/export-csv', methods=['GET'])
def export_csv():
    cur = g.mysql.connection.cursor()
    try:
        # Get the current user's ID from the session
        current_user_id = session.get('user_id')
        logger.debug(f"Current user ID: {current_user_id}")

        # Query to fetch the required data
        query = """
        SELECT cs.course_code, s.capacity, c.course_type, cs.course_block, u.department, 
               cs.start_hour, cs.duration, cs.day
        FROM created_schedules cs
        JOIN section_courses sc ON cs.course_id = sc.course_id
        JOIN sections s ON sc.section_id = s.section_id
        JOIN courses c ON cs.course_id = c.course_id
        JOIN users u ON cs.user_id = u.user_id
        WHERE cs.user_id = %s
        """
        cur.execute(query, (current_user_id,))
        rows = cur.fetchall()
        logger.debug(f"Query returned {len(rows)} rows")

        if not rows:
            flash('No data available for export.', 'warning')
            return redirect(url_for('my_blueprint.create'))

        # Create a CSV file in memory
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Course Code', 'Capacity', 'Type', 'Course Block', 'Department', 'Start Time', 'End Time', 'Day'])

        # Use a set to track unique courses
        unique_courses = set()

        for row in rows:
            course_code, capacity, course_type, course_block, department, start_hour, duration, day = row
            start_time = float(start_hour)
            end_time = start_time + float(duration)
            start_time_str = f"{int(start_time):02d}:{int((start_time % 1) * 60):02d}"
            end_time_str = f"{int(end_time):02d}:{int((end_time % 1) * 60):02d}"

            # Create a unique key for each course
            course_key = (course_code, course_block, start_time_str, day)

            if course_key not in unique_courses:
                unique_courses.add(course_key)
                writer.writerow([course_code, capacity, course_type, course_block, department, start_time_str, end_time_str, day])

        output.seek(0)
        return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=schedule.csv"})
    except Exception as e:
        logger.error(f"An error occurred while exporting CSV: {e}")
        flash('Failed to export CSV.', 'danger')
        return redirect(url_for('my_blueprint.create'))
    finally:
        cur.close()

@bp.route('/gened-export-csv', methods=['GET'])
def gened_export_csv():
    cur = g.mysql.connection.cursor()
    try:
        # Get the current user's ID from the session
        current_user_id = session.get('user_id')
        logger.debug(f"Current user ID: {current_user_id}")

        # Query to fetch the required data
        query = """
        SELECT cgs.course_code, gc.capacity, gc.type, cgs.course_block, u.department, 
               cgs.start_hour, cgs.duration, cgs.day
        FROM created_gened_schedules cgs
        JOIN gened_courses gc ON cgs.course_id = gc.course_id
        JOIN users u ON cgs.user_id = u.user_id
        WHERE cgs.user_id = %s
        """
        cur.execute(query, (current_user_id,))
        rows = cur.fetchall()
        logger.debug(f"Query returned {len(rows)} rows")

        if not rows:
            flash('No data available for export.', 'warning')
            return redirect(url_for('my_blueprint.gened_create'))

        # Create a CSV file in memory
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Course Code', 'Capacity', 'Type', 'Course Block', 'Department', 'Start Time', 'End Time', 'Day'])

        # Use a set to track unique courses
        unique_courses = set()

        for row in rows:
            course_code, capacity, course_type, course_block, department, start_hour, duration, day = row
            start_time = float(start_hour)
            end_time = start_time + float(duration)
            start_time_str = f"{int(start_time):02d}:{int((start_time % 1) * 60):02d}"
            end_time_str = f"{int(end_time):02d}:{int((end_time % 1) * 60):02d}"

            # Create a unique key for each course
            course_key = (course_code, course_block, start_time_str, day)

            if course_key not in unique_courses:
                unique_courses.add(course_key)
                writer.writerow([course_code, capacity, course_type, course_block, department, start_time_str, end_time_str, day])

        output.seek(0)
        return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=schedule.csv"})
    except Exception as e:
        logger.error(f"An error occurred while exporting CSV: {e}")
        flash('Failed to export CSV.', 'danger')
        return redirect(url_for('my_blueprint.gened_create'))
    finally:
        cur.close()


class EditAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField("New Password")
    confirmPassword = PasswordField("Confirm Password", validators=[EqualTo('password')])
    submit = SubmitField('Update')


@bp.route('/edit-account', methods=['GET', 'POST'])
def edit_account():
    # Get the current user's ID from the session
    current_user_id = session.get('user_id')
    current_app.logger.debug(f"Current user ID from session: {current_user_id}")
    
    if not current_user_id:
        flash('You must be logged in to edit your account.', 'account_error')
        return redirect(url_for('my_blueprint.admin'))

    cur = g.mysql.connection.cursor()
    try:
        # Fetch the user details
        cur.execute("SELECT username, email FROM users WHERE user_id = %s", (current_user_id,))
        user_data = cur.fetchone()
        if not user_data:
            flash('User not found.', 'account_error')
            return redirect(url_for('my_blueprint.admin'))
        current_app.logger.debug(f"Fetched user data: {user_data}")

        # Prepare the form
        form = EditAccountForm()

        if form.validate_on_submit():
            try:
                # Update user information
                cur.execute("UPDATE users SET username = %s, email = %s WHERE user_id = %s",
                            (form.username.data, form.email.data, current_user_id))
                g.mysql.connection.commit()
                current_app.logger.debug(f"Affected rows: {cur.rowcount}")
                if cur.rowcount == 0:
                    current_app.logger.warning(f"No rows affected for user_id: {current_user_id}")
                    flash('No changes were made to the user information.', 'account_warning')
                else:
                    flash('User information updated successfully!', 'account_success')

                # Update password only if provided
                if form.password.data:
                    hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())
                    cur.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_password, current_user_id))
                    g.mysql.connection.commit()
                    current_app.logger.debug(f"Password updated for user_id: {current_user_id}")
                    flash('Password updated successfully!', 'account_success')
            except Exception as e:
                current_app.logger.error(f"An error occurred: {e}")
                flash('Failed to update user.', 'account_danger')
            finally:
                cur.close()

            return redirect(url_for('my_blueprint.edit_account'))
        else:
            # If form doesn't validate, populate form with user data and render the template
            form.username.data = user_data[0]
            form.email.data = user_data[1]

            # Check for validation errors
            if form.password.errors:
                flash(' '.join(form.password.errors), 'account_error')
            if form.confirmPassword.errors:
                flash(' '.join(form.confirmPassword.errors), 'account_error')
            
            # Check for email validation error specifically
            if form.email.errors:
                flash(form.email.errors[0], 'account_error')

            return render_template('edit_user_account.html', form=form, current_endpoint=request.endpoint)

    except Exception as e:
        current_app.logger.error(f"An error occurred during ownership check: {str(e)}")
        flash('An error occurred while processing your request.', 'account_error')
    finally:
        cur.close()

    return redirect(url_for('my_blueprint.edit_account'))



@bp.route('/export-schedule', methods=['GET'])
def export_schedule():
    department_id = request.args.get('department')
    
    # Fetch the data from the final_allocations table based on the selected department
    cur = g.mysql.connection.cursor()
    cur.execute("""
        SELECT rc.course_code, rc.block, rc.start_time, rc.end_time, rc.day, cl.room_no, rc.department
        FROM final_allocations fa
        JOIN room_courses rc ON fa.course_id = rc.course_id
        JOIN classrooms cl ON fa.room_id = cl.room_id
        WHERE rc.department = %s
    """, (department_id,))
    allocations = cur.fetchall()
    cur.close()

    # Create the CSV response
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Course Code', 'Block', 'Start Time', 'End Time', 'Day', 'Room No', 'Department'])
    for allocation in allocations:
        cw.writerow(allocation)
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=schedule.csv"
    output.headers["Content-type"] = "text/csv"
    return output