from decimal import Decimal
import random
from typing import Optional
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, abort, session, url_for
from functools import wraps
from flask import g
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import HiddenField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
import logging
from flask import current_app
import random
import mysql.connector
import random
from datetime import datetime, timedelta

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'thesis_project'
}

bp = Blueprint('RoomAlgorithm', __name__)

# Connect to the database
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Fetch classrooms from the database
def fetch_classrooms():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM classrooms")
    classrooms = cursor.fetchall()
    cursor.close()
    conn.close()
    return classrooms

# Fetch room courses from the database excluding those already in final_allocations
def fetch_room_courses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM room_courses 
        WHERE course_id NOT IN (SELECT course_id FROM final_allocations)
    """)
    room_courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return room_courses

# Fetch existing allocations from final_allocations
def fetch_existing_allocations():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT fa.*, rc.course_code, rc.block, rc.department, rc.start_time, rc.end_time, rc.day, rc.type, rc.capacity, c.floor_level
        FROM final_allocations fa
        JOIN room_courses rc ON fa.course_id = rc.course_id
        JOIN classrooms c ON fa.room_id = c.room_id
    """)
    existing_allocations = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Convert to list of tuples (course, room)
    formatted_allocations = []
    for allocation in existing_allocations:
        course = {
            'course_id': allocation['course_id'],
            'course_code': allocation['course_code'],
            'block': allocation['block'],
            'department': allocation['department'],
            'start_time': allocation['start_time'],
            'end_time': allocation['end_time'],
            'day': allocation['day'],
            'type': allocation['type'],
            'capacity': allocation['capacity']
        }
        room = {
            'room_id': allocation['room_id'],
            'floor_level': allocation['floor_level'],
            'capacity': allocation['capacity'],
            'type': allocation['type']
        }
        formatted_allocations.append((course, room))
    
    return formatted_allocations

# Genetic Algorithm Parameters
mutation_rate = 0.01

def initialize_population(classrooms, room_courses, population_size, existing_allocations):
    population = []
    for _ in range(population_size):
        schedule = existing_allocations.copy()
        course_groups = {}
        for course in room_courses:
            key = (course['course_code'], course['block'])
            if key not in course_groups:
                course_groups[key] = []
            course_groups[key].append(course)
        
        for group in course_groups.values():
            # Prioritize room assignment based on department and floor preferences
            preferred_rooms = []
            for course in group:
                if course['department'] in ['CSIT', 'Engineering']:
                    preferred_rooms.extend([room for room in classrooms if room['floor_level'] == 4])
                elif course['department'] == 'GENED':
                    preferred_rooms.extend([room for room in classrooms if room['floor_level'] in [1, 2]])
                elif course['department'] == 'SEAS':
                    preferred_rooms.extend([room for room in classrooms if room['floor_level'] in [1, 2]])
                elif course['department'] == 'SBMA':
                    preferred_rooms.extend([room for room in classrooms if room['floor_level'] == 3])
                else:
                    preferred_rooms.extend(classrooms)
            
            # Filter rooms by capacity and type
            valid_rooms = [room for room in preferred_rooms if room['capacity'] >= course['capacity'] and room['type'] == course['type']]
            
            if not valid_rooms:
                valid_rooms = [room for room in classrooms if room['capacity'] >= course['capacity'] and room['type'] == course['type']]
            
            room = random.choice(valid_rooms) if valid_rooms else random.choice(classrooms)
            
            for course in group:
                schedule.append((course, room))
        population.append(schedule)
    return population

def decimal_to_time(decimal_time):
    hours = int(decimal_time)
    minutes = int((decimal_time - hours) * 60)
    return f"{hours:02}:{minutes:02}"

def time_conflict(course1, course2):
    start1 = decimal_to_time(course1['start_time'])
    end1 = decimal_to_time(course1['end_time'])
    start2 = decimal_to_time(course2['start_time'])
    end2 = decimal_to_time(course2['end_time'])
    return not (end1 <= start2 or end2 <= start1)

def fitness(schedule):
    score = 0
    course_room_map = {}

    for i, (course, room) in enumerate(schedule):
        # Check if the course type matches the room type and capacity
        if course['type'] == room['type'] and course['capacity'] <= room['capacity']:
            score += 10
        else:
            score -= 10  # Penalize if the room type or capacity does not match
        
        # Check if the course department matches the preferred floor level
        if course['department'] == 'CSIT' and room['floor_level'] == 4:
            score += 1
        elif course['department'] == 'ENGINEERING' and room['floor_level'] == 4:
            score += 1
        elif course['department'] == 'GENED' and room['floor_level'] in [1, 2]:
            score += 1
        elif course['department'] == 'SEAS' and room['floor_level'] in [1, 2]:
            score += 1
        elif course['department'] == 'SBMA' and room['floor_level'] == 3:
            score += 1
        else:
            score -= 1  # Penalize if the room is not on the preferred floor
        
        # Check for time conflicts
        for j in range(i):
            if schedule[j][1]['room_id'] == room['room_id'] and time_conflict(schedule[j][0], course):
                score -= 10
        
        # Ensure courses with the same code and block use the same room
        key = (course['course_code'], course['block'])
        if key in course_room_map:
            if course_room_map[key] != room['room_id']:
                score -= 10  # Penalize if the room is different
        else:
            course_room_map[key] = room['room_id']

    return score

def tournament_selection(population, tournament_size=3):
    selected = []
    for _ in range(len(population)):
        tournament = random.sample(population, tournament_size)
        winner = max(tournament, key=lambda x: fitness(x))
        selected.append(winner)
    return selected

def crossover(parent1, parent2):
    crossover_point = random.randint(0, len(parent1) - 1)
    child1 = parent1[:crossover_point] + parent2[crossover_point:]
    child2 = parent2[:crossover_point] + parent1[crossover_point:]
    
    # Ensure courses with the same code and block use the same room
    course_room_map = {}
    for i, (course, room) in enumerate(child1):
        key = (course['course_code'], course['block'])
        if key not in course_room_map:
            course_room_map[key] = room
        else:
            child1[i] = (course, course_room_map[key])
    
    course_room_map = {}
    for i, (course, room) in enumerate(child2):
        key = (course['course_code'], course['block'])
        if key not in course_room_map:
            course_room_map[key] = room
        else:
            child2[i] = (course, course_room_map[key])
    
    return child1, child2

def mutate(schedule, classrooms):
    if random.random() < mutation_rate:
        course_index = random.randint(0, len(schedule) - 1)
        new_room = random.choice(classrooms)
        key = (schedule[course_index][0]['course_code'], schedule[course_index][0]['block'])
        for i, (course, room) in enumerate(schedule):
            if (course['course_code'], course['block']) == key:
                schedule[i] = (course, new_room)
    return schedule

# Example usage
def selection(population):
    return tournament_selection(population)

def genetic_algorithm(classrooms, room_courses, population_size, generations, existing_allocations):
    population = initialize_population(classrooms, room_courses, population_size, existing_allocations)
    for _ in range(generations):
        selected = tournament_selection(population)
        next_generation = []
        while len(next_generation) < population_size:
            parent1, parent2 = random.sample(selected, 2)
            child1, child2 = crossover(parent1, parent2)
            next_generation.append(mutate(child1, classrooms))
            next_generation.append(mutate(child2, classrooms))
        population = next_generation
    best_schedule = max(population, key=lambda x: fitness(x))
    
    # Identify conflicts
    conflicts = []
    for i, (course1, room1) in enumerate(best_schedule):
        for j, (course2, room2) in enumerate(best_schedule):
            if i != j and room1['room_id'] == room2['room_id'] and time_conflict(course1, course2):
                conflicts.append((course1, course2, room1))
    
    return best_schedule, conflicts

def save_schedule_to_db(schedule):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert new allocations
        for course, room in schedule:
            cursor.execute(
                "INSERT INTO allocations (course_id, room_id) VALUES (%s, %s)",
                (course['course_id'], room['room_id'])
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Failed to save schedule to database: {e}")
    finally:
        cursor.close()
        conn.close()

class GenerateForm(FlaskForm):
    population_size = IntegerField('Population Size', default=100)
    max_generations = IntegerField('Max Generations', default=1000)
    submit = SubmitField('Generate Schedule')

@bp.route('/generate-schedule', methods=['GET', 'POST'])
def room_schedule():
    form = GenerateForm()
    floor_level = request.args.get('floor_level', 1, type=int)
    
    if form.validate_on_submit():
        population_size = form.population_size.data
        generations = form.max_generations.data
        
        # Fetch data from the database
        classrooms = fetch_classrooms()
        room_courses = fetch_room_courses()
        existing_allocations = fetch_existing_allocations()
        
        # Run the genetic algorithm
        best_schedule, conflicts = genetic_algorithm(classrooms, room_courses, population_size, generations, existing_allocations)
        
        # Delete all existing data from the allocations table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM allocations")
        conn.commit()
        
        # Save the schedule to the database
        save_schedule_to_db(best_schedule)
        
        cursor.close()
        conn.close()
        
        flash('Algorithm completed successfully. The page will reload to display the changes.')
        return redirect(url_for('RoomAlgorithm.room_schedule', floor_level=floor_level))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch classrooms for the selected floor level
    cursor.execute("SELECT * FROM classrooms WHERE floor_level = %s", (floor_level,))
    classrooms = cursor.fetchall()
    
    # Fetch allocations and join with room_courses to get course details
    classroom_ids = [classroom['room_id'] for classroom in classrooms]
    if classroom_ids:
        format_strings = ','.join(['%s'] * len(classroom_ids))
        query = f"""
            SELECT a.*, rc.course_code, rc.block, rc.department, rc.start_time, rc.end_time, rc.day
            FROM allocations a
            JOIN room_courses rc ON a.course_id = rc.course_id
            WHERE a.room_id IN ({format_strings})
        """
        cursor.execute(query, tuple(classroom_ids))
        allocations = cursor.fetchall()
    else:
        allocations = []
    
    cursor.close()
    conn.close()
    
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
    
    return render_template('registrar/registrar_generate.html', form=form, 
                           room_allocations=room_allocations, 
                           classrooms=classrooms, floor_level=floor_level,
                           current_endpoint=request.endpoint)