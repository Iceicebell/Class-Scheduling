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
POPULATION_SIZE = 50
MAX_GENERATIONS = 100
MUTATION_RATE = 0.5

class Solution:
    def __init__(self, schedule=None, shared_schedule=None):
        self.schedule = schedule if schedule else {}
        self.shared_schedule = shared_schedule if shared_schedule else {}
        self.fitness_score = None

    def add_course_assignment(self, section_id, course_id, day, start_hour, duration, course_code, course_block):
        if section_id not in self.schedule:
            self.schedule[section_id] = []
        # Assuming other parameters are correctly passed and used elsewhere in your method

        # Adjust max_duration to respect the lunch break without unnecessarily reducing course duration
        if start_hour < 12:
            max_duration = min(12 - start_hour, duration)  # Ensure the course ends before 12:00 if it starts before
        else:
            max_duration = duration  # For courses starting at or after 12:00, keep the original duration unless it would extend beyond 20:00
            if start_hour + duration > 20:
                max_duration = 20 - start_hour  # Adjust only if it extends beyond 20:00

        # Ensure no course spans the lunch break
        adjusted_start_hour = start_hour
        if start_hour + duration > 13 and start_hour < 12:
            adjusted_start_hour = 13  # Move the course to start after lunch if it would otherwise span it
            max_duration = min(20 - adjusted_start_hour, duration)  # Adjust duration to not exceed 20:00

        self.schedule[section_id].append((course_id, day, adjusted_start_hour, max_duration, course_code, course_block))
        self.fitness_score = None


    def get_schedule_by_course_code_and_block(self, course_code, course_block):
        # This method retrieves the existing day and start_hour for a given course_code and course_block combo
        return self.shared_schedule.get((course_code, course_block), (None, None))

    def add_shared_schedule(self, course_code, course_block, assignments):
        key = (course_code, course_block)
        if key not in self.shared_schedule:
            self.shared_schedule[key] = []

        # Instead of extending, append new assignments to preserve individuality
        self.shared_schedule[key].extend([assignment for assignment in assignments if assignment not in self.shared_schedule[key]])

    def remove_course_assignment(self, section_id, course_id):
        if section_id in self.schedule:
            self.schedule[section_id] = [
                (cid, d, sh, dur, cc, cb) for (cid, d, sh, dur, cc, cb) in self.schedule[section_id]
                if cid != course_id
            ]
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
            for course_id, _, _, duration, _, _ in section_assignments:  # Assuming the sixth element is not used
                expected_units = self.get_course_units(cursor, course_id)
                scheduled_hours = sum(dur for _, _, _, dur, _, _ in section_assignments if dur == duration)
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
            
            if not self.schedule:
                print("Warning: Empty schedule.")
                self.fitness_score = float('-inf')
                return self.fitness_score
            
            unit_match_score = self.check_unit_match(cursor)
            
            for section_id, assignments in self.schedule.items():
                for i, (course_id1, day1, start_hour1, duration1, course_code1, course_block1) in enumerate(assignments):
                    # Penalize courses that span the lunch break
                    if start_hour1 < 12 and start_hour1 + duration1 > 12:
                        conflicts += 1  # Penalize if a course starts before 12:00 and ends after 12:00, potentially spanning the lunch break
                    
                    for j in range(i+1, len(assignments)):
                        course_id2, day2, start_hour2, duration2, course_code2, course_block2 = assignments[j]
                        if day1 == day2:
                            # Check for direct time overlaps
                            if start_hour1 <= start_hour2 < start_hour1 + duration1 or start_hour2 <= start_hour1 < start_hour2 + duration2:
                                conflicts += 1
                            # Penalize if either course spans the lunch break
                            if (start_hour1 < 12 and start_hour1 + duration1 > 12) or (start_hour2 < 12 and start_hour2 + duration2 > 12):
                                conflicts += 1
                            faculty_id1 = self.get_faculty_id(cursor, course_id1)
                            faculty_id2 = self.get_faculty_id(cursor, course_id2)
                            if faculty_id1 == faculty_id2:
                                conflicts += 1
                            faculty_workload[faculty_id1] = faculty_workload.get(faculty_id1, 0) + duration1
                            faculty_workload[faculty_id2] = faculty_workload.get(faculty_id2, 0) + duration2
                            
                            # Additional check for lunch break violations within the nested loop
                            if (start_hour1 < 12 and start_hour1 + duration1 > 12) or (start_hour2 < 12 and start_hour2 + duration2 > 12):
                                conflicts += 1  # Penalize if either course spans the lunch break
                            
                max_workload = max(faculty_workload.values(), default=0)
                unit_match_score = self.check_unit_match(cursor)
                self.fitness_score = -conflicts - max_workload + unit_match_score
                print(f"Calculated fitness score: {self.fitness_score}")
                return self.fitness_score
        except Exception as e:
            print(f"Error calculating fitness: {e}")
            self.fitness_score = float('-inf')
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


    def display(self):
    # Iterate over each section in the schedule
        for section_id, assignments in self.schedule.items():
            print(f"\nSchedule for Section {section_id}:")
            for course_id, day, start_hour, duration, course_code, course_block in assignments:  # Correctly unpacking five elements
                print(f"Course ID: {course_id}, Day: {day}, Start Hour: {start_hour}, Duration: {duration}, Course Code: {course_code}, Block: {course_block}")

            
            # Organize schedule by day for the current section
            schedule_by_day = {'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': [], 'Friday': [], 'Saturday': []}
            for course_id, day, start_hour, duration, _, _ in assignments:  # Adjusted to match the five-element structure, ignoring course_code and course_block
                schedule_by_day[day].append((course_id, f"{start_hour}-{start_hour + duration}"))
            
            # Determine the maximum number of courses scheduled on any day for this section
            max_courses_per_day = max(len(courses) for courses in schedule_by_day.values())
            
            # Print header for the section's schedule with borders
            print("-" * 80)
            print("Course ID", end='\t')
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday']:
                print(f"{day:<15}", end='\t')
            print("\n" + "-" * 80)
            
            # Print rows for the current section with borders
            for i in range(max_courses_per_day):
                row = [""] * 6  # Initialize row with empty strings
                for j, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday']):
                    if i < len(schedule_by_day[day]):
                        course_id, time_slot = schedule_by_day[day][i]
                        row[j] = f"{course_id:<10}{time_slot:<15}"
                    else:
                        row[j] = " " * 1  # Adjust width as needed
                print("".join(row))
            print("-" * 80)  



# def calculate_fitness(self):
#         conflicts = 0
#         faculty_workload = {}
#         with current_app.app_context():
#             with current_app.mysql.connection.cursor() as cur:
#                 for section_assignments in self.schedule.values():
#                     for i, (course_id1, day1, start_hour1, duration1) in enumerate(section_assignments):
#                         for j in range(i+1, len(section_assignments)):
#                             course_id2, day2, start_hour2, duration2 = section_assignments[j]
#                             if day1 == day2 and (start_hour1 <= start_hour2 < start_hour1 + duration1 or start_hour2 <= start_hour1 < start_hour2 + duration2):
#                                 conflicts += 1
#                             faculty_id1 = self.get_faculty_id(cur, course_id1)
#                             faculty_id2 = self.get_faculty_id(cur, course_id2)
#                             if faculty_id1 == faculty_id2:
#                                 conflicts += 1
#                             faculty_workload[faculty_id1] = faculty_workload.get(faculty_id1, 0) + duration1
#                             faculty_workload[faculty_id2] = faculty_workload.get(faculty_id2, 0) + duration2

#                 max_workload = max(faculty_workload.values(), default=0)
#                 unit_match_score = self.check_unit_match(cur)
#                 self.fitness_score = -conflicts - max_workload + unit_match_score
#                 return self.fitness_score

           

def crossover(parent1, parent2):
    # Initialize the child's schedule and shared_schedule as empty dictionaries
    child_schedule = {}
    child_shared_schedule = {}

    # Iterate over the keys in parent1's schedule to combine schedules
    for course_id in set(parent1.schedule.keys()).union(parent2.schedule.keys()):
        # Check if the course exists in both parents; if not, use the one that does exist
        if course_id in parent1.schedule:
            child_schedule[course_id] = parent1.schedule[course_id].copy()
        elif course_id in parent2.schedule:
            child_schedule[course_id] = parent2.schedule[course_id].copy()

    # Combine shared_schedules similarly, but directly assign tuple values
    for course_id in set(parent1.shared_schedule.keys()).union(parent2.shared_schedule.keys()):
        if course_id in parent1.shared_schedule:
            child_shared_schedule[course_id] = parent1.shared_schedule[course_id]
        elif course_id in parent2.shared_schedule:
            child_shared_schedule[course_id] = parent2.shared_schedule[course_id]

    # After combining, ensure time slots do not exceed 20 hours
    for course_id, blocks_list in child_schedule.items():
        corrected_blocks = []
        for block in blocks_list:  # Assuming blocks_list is a list of tuples
            day, start_hour, end_hour, *rest = block  # Use *rest to capture remaining elements
            if end_hour > 20:
                end_hour = 20  # Simplified correction logic
            corrected_blocks.append((day, start_hour, end_hour, *rest))
        child_schedule[course_id] = corrected_blocks

    # Create a new Solution object with the combined schedule and shared_schedule
    child_solution = Solution(schedule=child_schedule, shared_schedule=child_shared_schedule)
    return child_solution


def get_course_details(cursor, course_id):
    query = "SELECT course_code, course_block FROM courses WHERE course_id = %s"
    cursor.execute(query, (course_id,))
    result = cursor.fetchone()
    if result:
        course_code, course_block = result
        return course_code, course_block
    else:
        raise ValueError(f"Course details not found for course_id: {course_id}")
    


def mutate(self, cursor):
    section_id = random.choice(list(self.schedule.keys()))
    if not self.schedule[section_id]:
        print(f"Section {section_id} has no courses assigned. Skipping mutation.")
        return  # Skip mutation for this iteration
    
    course_index = random.randrange(len(self.schedule[section_id]))
    course_info = self.schedule[section_id][course_index]
    print(f"Course info before unpacking: {course_info}")
    course_id, day, start_hour, duration, course_code, course_block = course_info  # Assuming duration is unpacked correctly
    
    try:
        new_day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        
        # Adjusting start hour selection to exclude the 12:00-13:00 period
        morning_period = range(7, 12)
        afternoon_period = range(13, 20)
        combined_periods = list(morning_period) + list(afternoon_period)
        new_start_hour = random.choice(combined_periods)
        
        # Ensure the new start hour plus duration does not exceed 20:00 and respects the lunch break
        if new_start_hour + duration > 13 and new_start_hour < 12:
            new_start_hour = 13  # Ensure start after lunch break if it would otherwise span it
        max_duration = duration  # Keep original duration unless it would extend beyond 20:00
        if new_start_hour + duration > 20:
            max_duration = 20 - new_start_hour  # Adjust only if it extends beyond 20:00

        # Update shared_schedule to reflect the mutation
        self.shared_schedule[(course_code, course_block)] = (new_day, new_start_hour, max_duration)
        
        # Apply the new schedule to all sections with the same course_code and course_block
        # Ensure the original duration is maintained unless it conflicts with the lunch break or end time
    except Exception as e:
        print(f"An error occurred during mutation: {e}")
        return  # Exit the function early due to an error




def generate_initial_solution():
    solution = Solution(shared_schedule={})  # Initialize with an empty shared_schedule
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

    # Group courses by (course_code, course_block)
    grouped_courses = {}
    for section_id, course_id, units, course_code, course_block in sections_data:
        key = (course_code, course_block)
        if key not in grouped_courses:
            grouped_courses[key] = []
        grouped_courses[key].append((section_id, course_id, units))

    # Assign the same schedule to all courses in the same group
    for (course_code, course_block), courses in grouped_courses.items():
        max_units = max(units for _, _, units in courses)
        day, start_hour = solution.get_schedule_by_course_code_and_block(course_code, course_block)
        
        if day is None and start_hour is None:
            day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
            morning_period = range(7, 12)
            afternoon_period = range(13, 20)
            combined_periods = list(morning_period) + list(afternoon_period)
            start_hour = random.choice(combined_periods)
            max_duration = min(20 - start_hour, max_units) if start_hour >= 13 else min(12 - start_hour, max_units)  # Respect lunch break
            solution.shared_schedule[(course_code, course_block)] = (day, start_hour, max_duration)
            print(f"Assigning shared schedule for {course_code} {course_block}: {day} {start_hour} {max_duration}")
        else:
            _, start_hour, max_duration = solution.shared_schedule[(course_code, course_block)]
            max_duration = min(20 - start_hour, max_units) if start_hour >= 13 else min(12 - start_hour, max_units)  # Adjust for lunch break
        
        for section_id, course_id, _ in courses:
            solution.add_course_assignment(section_id, course_id, day, start_hour, max_duration, course_code, course_block)

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
                child = crossover(parent1, parent2)  # Assuming crossover is adjusted accordingly
                
                # Mutation
                if random.random() < MUTATION_RATE:
                    mutate(child, cursor)  # Correctly pass the cursor here
                
                new_population.append(child)
            
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
