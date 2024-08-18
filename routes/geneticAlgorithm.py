import random
from typing import Optional
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, abort, session, url_for
from functools import wraps
from flask import g
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
import logging
from flask import current_app
import random
import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'thesis_project'
}


bp = Blueprint('algorithm', __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
POPULATION_SIZE = 100
MAX_GENERATIONS = 50
MUTATION_RATE = 0.01

class Solution:
    def __init__(self, schedule=None):
        self.schedule = schedule if schedule else {}
        self.fitness_score = None

    def add_course_assignment(self, section_id, course_id, day, start_hour, duration):
        if section_id not in self.schedule:
            self.schedule[section_id] = []
        self.schedule[section_id].append((course_id, day, start_hour, duration))
        self.fitness_score = None

    def add_shared_schedule(self, course_code, course_block, assignments):
        key = (course_code, course_block)
        if key not in self.shared_schedule:
            self.shared_schedule[key] = []

        # Instead of extending, append new assignments to preserve individuality
        self.shared_schedule[key].extend([assignment for assignment in assignments if assignment not in self.shared_schedule[key]])

    def remove_course_assignment(self, section_id, course_id):
        if section_id in self.schedule:
            self.schedule[section_id] = [(cid, d, sh, dur) for cid, d, sh, dur in self.schedule[section_id] if cid != course_id]
            self.fitness_score = None

    def get_schedule(self, section_id):
        return self.schedule.get(section_id, [])



    def get_faculty_id(self, cursor, course_id):
        query = "SELECT faculty_id FROM courses WHERE course_id = %s"
        cursor.execute(query, (course_id,))
        result = cursor.fetchone()
        return result[0] if result else None

    def check_unit_match(self, cursor):
        unit_match_score = 0
        for section_assignments in self.schedule.values():
            for course_id, _, _, duration in section_assignments:
                expected_units = self.get_course_units(cursor, course_id)
                scheduled_hours = sum(dur for _, _, _, dur in section_assignments if dur == duration)
                unit_match_score -= abs(expected_units - scheduled_hours)
        return unit_match_score

    def get_course_units(self, cursor, course_id):
        query = "SELECT units FROM courses WHERE course_id = %s"
        cursor.execute(query, (course_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

    def calculate_fitness(self, cursor):
        print("Calculating fitness...")
        try:
            conflicts = 0
            faculty_workload = {}
            
            # Validate the schedule before proceeding
            if not self.schedule:
                print("Warning: Empty schedule.")
                self.fitness_score = float('-inf')  # Assign a very low fitness score for empty schedules
                return self.fitness_score
            
            unit_match_score = self.check_unit_match(cursor)
            
            for section_assignments in self.schedule.values():
                for i, (course_id1, day1, start_hour1, duration1) in enumerate(section_assignments):
                    for j in range(i+1, len(section_assignments)):
                        course_id2, day2, start_hour2, duration2 = section_assignments[j]
                        if day1 == day2 and (start_hour1 <= start_hour2 < start_hour1 + duration1 or start_hour2 <= start_hour1 < start_hour2 + duration2):
                            conflicts += 1
                        faculty_id1 = self.get_faculty_id(cursor, course_id1)
                        faculty_id2 = self.get_faculty_id(cursor, course_id2)
                        if faculty_id1 == faculty_id2:
                            conflicts += 1
                        faculty_workload[faculty_id1] = faculty_workload.get(faculty_id1, 0) + duration1
                        faculty_workload[faculty_id2] = faculty_workload.get(faculty_id2, 0) + duration2

            max_workload = max(faculty_workload.values(), default=0)
            unit_match_score = self.check_unit_match(cursor)
            self.fitness_score = -conflicts - max_workload + unit_match_score
            print(f"Calculated fitness score: {self.fitness_score}")
            return self.fitness_score
        except Exception as e:
            print(f"Error calculating fitness: {e}")
            self.fitness_score = float('-inf')  # Assign a very low fitness score in case of an error
            return self.fitness_score
    
    def __lt__(self, other):
            """Less than comparison method."""
            if not isinstance(other, type(self)):
                # Not a Solution instance, so we can't compare.
                return NotImplemented
            # Ensure fitness_score is never None or handle comparisons appropriately
            return self.fitness_score < other.fitness_score if other.fitness_score is not None else False

        # Optionally, implement equality for completeness
    def __eq__(self, other):
        """Equality comparison method."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.fitness_score == other.fitness_score if other.fitness_score is not None else False

    def check_unit_match(self, cursor):
        unit_match_score = 0
        for section_assignments in self.schedule.values():
            for course_id, _, _, duration in section_assignments:
                expected_units = self.get_course_units(cursor, course_id)
                scheduled_hours = sum(dur for _, _, _, dur in section_assignments if dur == duration)
                unit_match_score -= abs(expected_units - scheduled_hours)
        return unit_match_score


    def display(self):
    # Iterate over each section in the schedule
        for section_id, assignments in self.schedule.items():
            print(f"\nSchedule for Section {section_id}:")
            
            # Organize schedule by day for the current section
            schedule_by_day = {'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': [], 'Friday': []}
            for course_id, day, start_hour, duration in assignments:
                schedule_by_day[day].append((course_id, f"{start_hour}-{start_hour + duration}"))
            
            # Determine the maximum number of courses scheduled on any day for this section
            max_courses_per_day = max(len(courses) for courses in schedule_by_day.values())
            
            # Print header for the section's schedule with borders
            print("-" * 80)
            print("Course ID", end='\t')
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                print(f"{day:<15}", end='\t')
            print("\n" + "-" * 80)
            
            # Print rows for the current section with borders
            for i in range(max_courses_per_day):
                row = [""] * 6  # Initialize row with empty strings
                for j, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']):
                    if i < len(schedule_by_day[day]):
                        course_id, time_slot = schedule_by_day[day][i]
                        row[j] = f"{course_id:<10}{time_slot:<15}"
                    else:
                        row[j] = " " * 1  # Adjust width as needed
                print("".join(row))
            print("-" * 80)  



def calculate_fitness(self):
        conflicts = 0
        faculty_workload = {}
        with current_app.app_context():
            with current_app.mysql.connection.cursor() as cur:
                for section_assignments in self.schedule.values():
                    for i, (course_id1, day1, start_hour1, duration1) in enumerate(section_assignments):
                        for j in range(i+1, len(section_assignments)):
                            course_id2, day2, start_hour2, duration2 = section_assignments[j]
                            if day1 == day2 and (start_hour1 <= start_hour2 < start_hour1 + duration1 or start_hour2 <= start_hour1 < start_hour2 + duration2):
                                conflicts += 1
                            faculty_id1 = self.get_faculty_id(cur, course_id1)
                            faculty_id2 = self.get_faculty_id(cur, course_id2)
                            if faculty_id1 == faculty_id2:
                                conflicts += 1
                            faculty_workload[faculty_id1] = faculty_workload.get(faculty_id1, 0) + duration1
                            faculty_workload[faculty_id2] = faculty_workload.get(faculty_id2, 0) + duration2

                max_workload = max(faculty_workload.values(), default=0)
                unit_match_score = self.check_unit_match(cur)
                self.fitness_score = -conflicts - max_workload + unit_match_score
                return self.fitness_score
            

def crossover(parent1, parent2):
    """Mix features of two parent schedules to create a child schedule."""
    child = Solution()
    for section_id in set(parent1.schedule).union(parent2.schedule):
        if random.random() < 0.5:
            child.schedule[section_id] = parent1.schedule.get(section_id, [])[:]
        else:
            child.schedule[section_id] = parent2.schedule.get(section_id, [])[:]
    print("Crossover performed, child schedule:", child.schedule)
    return child

def mutate(self):
    section_id = random.choice(list(self.schedule.keys()))
    
    # Check if the selected section has any courses assigned
    if not self.schedule[section_id]:
        print(f"Section {section_id} has no courses assigned. Skipping mutation.")
        return  # Skip mutation for this iteration
    
    course_index = random.randrange(len(self.schedule[section_id]))
    
    course_info = self.schedule[section_id][course_index]
    
    # Ensure the course information has the expected length
    if len(course_info) != 4:
        raise ValueError(f"Course information missing expected values: {course_info}")
    
    # Directly unpack the course information, assuming it has exactly four elements
    course_id, day, start_hour, duration = course_info  # Corrected to match the expected structure
    
    # Attempt to move the course to a different slot without causing conflicts
    while True:
        new_day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
        new_start_hour = random.randint(7, 19 - duration)
        conflict = False
        for other_section in self.schedule:
            if other_section != section_id:
                for other_course in self.schedule[other_section]:
                    if other_course[0] == course_id and other_course[1] == new_day and new_start_hour >= other_course[2] and new_start_hour + duration <= other_course[2] + other_course[3]:
                        conflict = True
                        break
                    if conflict:
                        break
        if not conflict:
            break
    self.remove_course_assignment(section_id, course_id)
    self.add_course_assignment(section_id, course_id, new_day, new_start_hour, duration)
    self.fitness_score = None
    print("Mutated solution:", self.schedule)

def generate_initial_solution():
    solution = Solution()
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("""
    SELECT sections.section_id, courses.course_id, courses.units, courses.course_code, courses.course_block
    FROM sections
    JOIN section_courses ON sections.section_id = section_courses.section_id
    JOIN courses ON section_courses.course_id = courses.course_id
    WHERE sections.department = 'SOECS';
    """)
    sections_data = cursor.fetchall()
    cursor.close()
    db.close()

    grouped_courses = {}
    for section_id, course_id, units, course_code, course_block in sections_data:
        key = (course_code, course_block)
        if key not in grouped_courses:
            grouped_courses[key] = []
        grouped_courses[key].append((section_id, course_id, units))

    for (course_code, course_block), courses in grouped_courses.items():
        max_units = max(units for _, _, units in courses)  # Determine the maximum units for the group
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
        start_hour = random.randint(7, 19)  # Adjust start_hour calculation if necessary to fit max_units
        for section_id, course_id, _ in courses:
            solution.add_course_assignment(section_id, course_id, day, start_hour, max_units)

    print("Initial solution generated:", solution.schedule)
    
    return solution

def select_parents(population):
    # Example: Random selection for simplicity. Implement a more sophisticated method based on fitness.
    parent1 = random.choice(population)
    parent2 = random.choice(population)
    return parent1, parent2

def run_genetic_algorithm(initial_solution):
    db = mysql.connector.connect(**db_config)
    try:
        cursor = db.cursor()
        population = [initial_solution] + [generate_initial_solution() for _ in range(POPULATION_SIZE - 1)]  # Adjusted for POPULATION_SIZE
        
        for solution in population:
            solution.calculate_fitness(cursor)
        
        for _ in range(MAX_GENERATIONS):
            new_population = []
            while len(new_population) < POPULATION_SIZE:
                parent1, parent2 = select_parents(population)
                
                # Crossover
                child = crossover(parent1, parent2)  # Note: crossover now returns a single child
                
                # Mutation
                if random.random() < MUTATION_RATE:
                    mutate(child)
                
                new_population.append(child)  # Append the single child to the new population
                
            # Merge and select the best or replace the population
            population = new_population
            
            # Optionally, recalculate fitness for new population
            for solution in new_population:
                solution.calculate_fitness(cursor)
            
            population.sort(key=lambda x: x.fitness_score, reverse=True)
            population = population[:POPULATION_SIZE]
        
        best_solution = max(population, key=lambda x: x.fitness_score)
    finally:
        cursor.close()
        db.close()
    print("Selected best solution's schedule:", best_solution.schedule)
    return best_solution


@bp.route('/department-head/generate')
def generate():
    if session.get('isVerified') ==False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)
    return render_template('dep_head/generate.html', current_endpoint=request.endpoint)
