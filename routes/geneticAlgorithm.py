from decimal import Decimal
import random
from typing import Optional
from flask import Blueprint, current_app, flash, has_app_context, jsonify, redirect, render_template, render_template_string, request, abort, session, url_for
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
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta, time




db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'thesis_project'
}


bp = Blueprint('algorithm', __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
POPULATION_SIZE = 5
MAX_GENERATIONS = 5
MUTATION_RATE = 0.1
    
class Solution:
    def __init__(self, schedule=None, shared_schedule=None):
        self.schedule = schedule if schedule else {}
        self.shared_schedule = shared_schedule if shared_schedule else {}
        self.fitness_score = None

    def add_course_assignment(self, section_id, course_id, day, start_hour, duration, course_code, course_block, cursor):
        if section_id not in self.schedule:
            self.schedule[section_id] = []
        
        # Convert duration to Decimal for precise calculations
        duration_decimal = Decimal(duration)
        # print(f"Original duration_decimal for course {course_id}: {duration_decimal}")  # Debugging line
        
        # Fetch the actual units from the database to decide on splitting
        units = self.get_course_units(cursor, course_id)
        # print(f"Units for course {course_id}: {units}")  # Debugging line
        
        # Adjust max_duration to respect the lunch break without unnecessarily reducing course duration
        if start_hour + duration_decimal > 13 and start_hour < 12:
            start_hour = 13  # Move the course to start after lunch if it would otherwise span it
        elif start_hour + duration_decimal > 20:
            start_hour = 20 - duration_decimal  # Adjust start_hour to ensure the course ends exactly at 20:00 if it would extend beyond

        # Ensure no course starts before 7:00 as a lower bound (assuming 7:00 is the earliest start time)
        start_hour = max(7, start_hour)

        # Ensure the course does not start too late to fit its entire duration before 12:00 or 20:00
        max_duration = min(12 - start_hour, duration_decimal) if start_hour < 12 else duration_decimal  # Ensure the course ends before 12:00 if it starts before
        if start_hour >= 12:
            max_duration = min(20 - start_hour, duration_decimal)  # Ensure the course ends before 20:00 if it starts after 12:00

        # Check if the course has 2 or more units and needs to be split into two meetings
        if units >= 2:
            # Determine the days to split the course based on the initial day
            if day in ['Monday', 'Tuesday', 'Thursday']:
                days = [day, self.get_pair_day(day)]
            else:
                # If the day is not one of the starting days, choose a pair that fits within the week
                days = [day, self.get_pair_day(day)]
            split_duration_decimal = units / Decimal(2)  # Use Decimal for precise division
            # print(f"Split duration_decimal for course {course_id}: {split_duration_decimal}")  # Debugging line
        else:
            days = [day]  # Course with less than 2 units, schedule on any day without splitting
            split_duration_decimal = duration_decimal
            # print(f"Duration_decimal for course {course_id} (not split): {split_duration_decimal}")  # Debugging line
        
        for d in days:
            # Adjust max_duration for each part if necessary
            max_duration = min(12 - start_hour, split_duration_decimal) if start_hour < 12 else split_duration_decimal
            if start_hour >= 12:
                max_duration = min(20 - start_hour, split_duration_decimal)
            # print(f"Final max_duration for course {course_id} on day {d}: {max_duration}")

            # Check for duplicates before adding
            existing_assignments = [(cid, day, sh) for cid, day, sh, _, _, _ in self.schedule[section_id]]
            if (course_id, d, start_hour) not in existing_assignments:
                self.schedule[section_id].append((course_id, d, start_hour, max_duration, course_code, course_block))
                # print(f"Added course {course_id} on {d} at {start_hour} with max_duration {max_duration}")
            else:
                pass
                # print(f"Skipping duplicate course {course_id} on {d} at {start_hour}")

        self.fitness_score = None


    def fetch_unavailable_times(self, cursor, section_id):
        """Fetches unavailable times for a section and adds them to the schedule as if they were courses."""
        query = "SELECT day_of_week, start_time, end_time FROM unavailable_times WHERE section_id = %s"
        cursor.execute(query, (section_id,))
        unavailable_periods = cursor.fetchall()
        for day, start_time, end_time in unavailable_periods:
            # Convert day_of_week to a format matching your schedule's day format if necessary
            day = self.convert_day_format(day)  # Implement this method based on your day format
            # Assuming unavailable times are treated as courses with a special course_id, e.g., negative IDs
            pseudo_course_id = -1  # Use a unique identifier for unavailable times
            # You might need to adjust the duration calculation based on your existing logic
            duration = end_time - start_time
            # Add unavailable times to the schedule
            self.add_course_assignment(section_id, pseudo_course_id, day, start_time, duration, "Unavailable", "None", cursor)

    def convert_day_format(self, day_of_week):
        """Converts the day format from the database to the format used in your schedule."""
        # Implement conversion logic here if necessary
        return day_of_week

    def get_pair_day(self, day):
        """Returns the paired day for splitting courses."""
        day_pairs = {
            'Monday': 'Wednesday',
            'Tuesday': 'Friday',
            'Thursday': 'Saturday'
        }
        paired_day = day_pairs.get(day, day)
        # print(f"Pair day for {day} is {paired_day}")
        return day_pairs.get(day, day)

    def get_available_slots(self, section_id, duration):
        available_slots = []
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for day in days:
            for start_hour in range(7, 20):  # Assuming 7 AM to 8 PM
                if self.is_slot_available(section_id, day, start_hour, duration):
                    available_slots.append((day, start_hour))
        return available_slots

    def is_slot_available(self, section_id, day, start_hour, duration):
        end_hour = start_hour + duration
        # Check for lunch break conflict
        if start_hour < 13 and end_hour > 12:
            return False
        # Check for overlap with existing courses and unavailable times
        for course_id, course_day, course_start, course_duration, _, _ in self.schedule.get(section_id, []):
            course_end = course_start + course_duration
            if day == course_day and (
                (start_hour < course_end and end_hour > course_start) or
                (course_start < end_hour and course_end > start_hour)
            ):
                return False
        return True
    
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
        """
        Calculate the fitness score of the current schedule based on several criteria:
        - Penalty for overlapping courses (including unavailable times and faculty conflicts)
        - Penalty for disregarding lunch breaks
        - Reward for maintaining course-code-block integrity
        - Reward for efficient time utilization
        """
        # print("Calculating Fitness...")
        fitness_score = 0
        conflicts_penalty = 0
        integrity_reward = 0
        efficiency_reward = 0
        utilization_penalty = 0

        # Penalty for overlapping courses and unavailable times
        for section_id, assignments in self.schedule.items():
            for i, (course_id1, day1, start_hour1, duration1, course_code1, course_block1) in enumerate(assignments):
                for j in range(i + 1, len(assignments)):
                    course_id2, day2, start_hour2, duration2, course_code2, course_block2 = assignments[j]
                    if day1 == day2:  # Check only within the same day
                        end_time1 = start_hour1 + duration1
                        end_time2 = start_hour2 + duration2
                        if start_hour1 < start_hour2 < end_time1 or start_hour1 < end_time2 < end_time1:  # Overlap check
                            conflicts_penalty += 200  # Simple penalty, adjust based on severity
                        faculty_id1 = self.get_faculty_id(cursor, course_id1)
                        faculty_id2 = self.get_faculty_id(cursor, course_id2)
                        if faculty_id1 == faculty_id2:  # Faculty conflict
                            conflicts_penalty += 200  # Adjust penalty as needed

        # Penalty for disregarding lunch breaks
        for section_id, assignments in self.schedule.items():
            for course_id, day, start_hour, duration, course_code, course_block in assignments:
                if 12 <= start_hour < 13 and start_hour + duration > 13:  # Course spans over lunch break
                    conflicts_penalty += 100  # Adjust based on how much it spans over

        # Reward for maintaining course-code-block integrity
        course_code_block_groups = {}
        for section_id, assignments in self.schedule.items():
            for course_id, day, start_hour, duration, course_code, course_block in assignments:
                key = (course_code, course_block)
                if key not in course_code_block_groups:
                    course_code_block_groups[key] = []
                course_code_block_groups[key].append((course_id, day, start_hour, duration))
                if len(course_code_block_groups[key]) > 1:  # More than one instance of the same course-code-block grouping
                    integrity_reward += 100  # Reward for keeping them together

        # Reward for efficient utilization (simple example: reward for filling morning and afternoon slots)
        for section_id, assignments in self.schedule.items():
            morning_slots_filled = sum(10 for _, day, start_hour, _, _, _ in assignments if start_hour < 12)
            afternoon_slots_filled = sum(10 for _, day, start_hour, _, _, _ in assignments if start_hour >= 13)
            efficiency_reward += min(morning_slots_filled, afternoon_slots_filled)  # Encourage balance

        # Calculate total fitness score
        self.fitness_score = integrity_reward + efficiency_reward - conflicts_penalty - utilization_penalty
        # print("Fitness Score: ",self.fitness_score)
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
    
    def find_available_slot(self, section_id, duration):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        start_hours = list(range(7, 20))  # 7 AM to 7 PM
        
        # Shuffle days and start hours to introduce randomness
        random.shuffle(days)
        random.shuffle(start_hours)
        
        for day in days:
            for start_hour in start_hours:
                end_hour = start_hour + duration
                
                # Check if the slot crosses the lunch break (12 PM to 1 PM)
                if start_hour < 12 and end_hour > 13:
                    continue
                
                # Check if the slot extends beyond 8 PM
                if end_hour > 20:
                    continue
                
                # Check for conflicts with existing assignments
                conflict = False
                for course_id, existing_day, existing_start, existing_duration, _, _ in self.schedule.get(section_id, []):
                    existing_end = existing_start + existing_duration
                    if day == existing_day and (
                        (start_hour < existing_end and end_hour > existing_start) or
                        (existing_start < end_hour and existing_end > start_hour)
                    ):
                        conflict = True
                        break
                
                if not conflict:
                    return (day, start_hour)
        
        # If no available slot is found
        return None


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

def get_course_details(cursor, course_id):
    query = "SELECT course_code, course_block FROM courses WHERE course_id = %s"
    cursor.execute(query, (course_id,))
    result = cursor.fetchone()
    if result:
        course_code, course_block = result
        return course_code, course_block
    else:
        raise ValueError(f"Course details not found for course_id: {course_id}")
    

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

    

def mutate(self, cursor):
    section_id = random.choice(list(self.schedule.keys()))
    if not self.schedule[section_id]:
        #print(f"Section {section_id} has no courses assigned. Skipping mutation.")
        return  # Skip mutation for this iteration
    
    course_index = random.randrange(len(self.schedule[section_id]))
    course_info = self.schedule[section_id][course_index]
    # print(f"Course info before unpacking: {course_info}")
    course_id, day, start_hour, duration, course_code, course_block = course_info  # Assuming duration is unpacked correctly
    
    new_slot = self.find_available_slot(section_id, duration)
    if new_slot:
        self.remove_course_assignment(section_id, course_id)
        self.add_course_assignment(section_id, course_id, new_slot[0], new_slot[1], duration, course_code, course_block, cursor)
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
    solution = Solution(shared_schedule={})
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    try:
        # Fetch sections owned by the current user
        cursor.execute("""
            SELECT s.section_id, c.course_id, c.units, c.course_code, c.course_block
            FROM sections s
            JOIN section_courses sc ON s.section_id = sc.section_id
            JOIN courses c ON sc.course_id = c.course_id
            WHERE s.user_id = %s;
        """, (session.get('user_id'),))
        sections_data = cursor.fetchall()

        # Fetch unavailable times for each section to mark them in the schedule
        for section_id, _, _, _, _ in sections_data:
            solution.fetch_unavailable_times(cursor, section_id)

        grouped_courses = {}
        for section_id, course_id, units, course_code, course_block in sections_data:
            key = (course_code, course_block)
            if key not in grouped_courses:
                grouped_courses[key] = []
            grouped_courses[key].append((section_id, course_id, units))

        for (course_code, course_block), courses in grouped_courses.items():
            day_options = ['Monday', 'Tuesday', 'Thursday']  # Consider expanding day options based on scheduling constraints
            day = random.choice(day_options)
            second_day = solution.get_pair_day(day)
            morning_period = range(7, 12)
            afternoon_period = range(13, 20)
            combined_periods = list(morning_period) + list(afternoon_period)
            start_hour = random.choice(combined_periods)

            for section_id, course_id, units in courses:
                units_decimal = Decimal(units)
                # logging.debug(f"Processing course {course_id} with units {units_decimal}")
                if units_decimal > Decimal(2):
                    split_duration_decimal = units_decimal / Decimal(2)
                    # logging.debug(f"Split duration_decimal for course {course_id}: {split_duration_decimal}")
                    solution.add_course_assignment(section_id, course_id, day, start_hour, split_duration_decimal, course_code, course_block, cursor)
                    solution.add_course_assignment(section_id, course_id, second_day, start_hour, split_duration_decimal, course_code, course_block, cursor)
                else:
                    solution.add_course_assignment(section_id, course_id, day, start_hour, units_decimal, course_code, course_block, cursor)

        logging.info("Initial solution generated.")
    finally:
        cursor.close()
        db.close()
    return solution



def select_parents(population, tournament_size=3):
    def tournament(population, size):
        tournament_group = random.sample(population, size)
        return max(tournament_group, key=lambda x: x.fitness_score)

    return tournament(population, tournament_size), tournament(population, tournament_size)

def run_genetic_algorithm(initial_solution):
    db = mysql.connector.connect(**db_config)
    try:
        cursor = db.cursor()
        population = [initial_solution] + [generate_initial_solution() for _ in range(POPULATION_SIZE - 1)]  # Adjusted for POPULATION_SIZE
        
        # Initial fitness calculation for the population
        for solution in population:
            solution.calculate_fitness(cursor)
        
        for _ in range(MAX_GENERATIONS):
            new_population = []
            elite_count = POPULATION_SIZE // 10
            new_population.extend(population[:elite_count])

            while len(new_population) < POPULATION_SIZE:
                # Parent selection
                parent1, parent2 = select_parents(population)
                
                # Crossover to generate offspring
                child = crossover(parent1, parent2)  # Ensure crossover is defined to accept cursor and perform necessary DB operations
                
                # Mutation with a chance defined by MUTATION_RATE
                if random.random() < MUTATION_RATE:
                    mutate(child, cursor)  # Ensure mutate is defined to accept a solution and cursor for DB operations
                new_population.append(child)
            
            # Replace the old population with the new one, ensuring we maintain the same population size
            population = new_population
            
            # Optionally, recalculate fitness for clarity and correctness
            for solution in new_population:
                solution.calculate_fitness(cursor)
            
            # Sort the population by fitness score to identify the best solutions
            population.sort(key=lambda x: x.fitness_score, reverse=True)
            population = population[:POPULATION_SIZE]  # Trim to original size, keeping only the best solutions
        
        # Identify the best solution based on fitness score
        best_solution = max(population, key=lambda x: x.fitness_score)
    finally:
        cursor.close()
        db.close()
    print("Selected best solution's schedule:", best_solution.schedule)
    return best_solution


def get_best_solution():
    initial_solution = generate_initial_solution()
    return run_genetic_algorithm(initial_solution)

class GenerateForm(FlaskForm):
    population_size = IntegerField('Population Size', default=50)
    max_generations = IntegerField('Max Generations', default=100)
    submit = SubmitField('Generate Schedule')
def generate_faculty_timetable(cursor, current_user_id):
    faculty_timetable = {}
    
    # Fetch faculty names for the current user's sections
    cursor.execute("SELECT faculty_id, first_name, last_name FROM faculty WHERE faculty_id IN (SELECT faculty_id FROM courses WHERE course_id IN (SELECT course_id FROM section_courses WHERE section_id IN (SELECT section_id FROM sections WHERE user_id = %s)))", (current_user_id,))
    faculty_data = cursor.fetchall()
    faculty_names = {faculty_id: f"{first_name} {last_name}" for faculty_id, first_name, last_name in faculty_data}
    
    # Fetch all course assignments from the database
    cursor.execute("SELECT user_id, section_id, course_id, day, start_hour, duration, course_code, course_block FROM user_solutions")
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

@bp.route('/department-head/generate', methods=['GET', 'POST'])
def generate():
    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'dept-head':
        abort(403)

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    # Fetch the saved schedule from the database
    cursor.execute("""
        SELECT user_id, section_id, course_id, day, start_hour, duration, course_code, course_block
        FROM user_solutions
        WHERE user_id = %s
    """, (session['user_id'],))

    saved_solutions = cursor.fetchall()
    
    # Fetch all sections owned by the current user
    cursor.execute("SELECT section_id, section_name FROM sections WHERE user_id = %s", (session['user_id'],))
    sections = cursor.fetchall()
    
    # Create a dictionary mapping section_ids to section_names
    section_names = {row[0]: row[1] for row in sections}

    display_schedule = {}
    for user_id, section_id, course_id, day, start_hour, duration, course_code, course_block in saved_solutions:
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
    form =  GenerateForm()
    faculty_timetable = None 
    if request.method == 'POST':
        if form.validate_on_submit():
            global POPULATION_SIZE, MAX_GENERATIONS
            POPULATION_SIZE = form.population_size.data
            MAX_GENERATIONS = form.max_generations.data

            # Run the genetic algorithm and get the best solution
            best_solution = get_best_solution()

            # Clear existing solutions for this user
            cursor.execute("DELETE FROM user_solutions WHERE user_id = %s", (session['user_id'],))

            # Save the best solution to the database
            for section_id, courses in best_solution.schedule.items():
                for course_id, day, start_hour, duration, course_code, course_block in courses:
                    query = """
                        INSERT INTO user_solutions 
                        (id, user_id, section_id, course_id, day, start_hour, duration, course_code, course_block)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(query, (
                        None,
                        session['user_id'],
                        section_id,
                        course_id,
                        day,
                        float(start_hour),
                        float(duration),
                        course_code,
                        course_block
                    ))

            # Commit the changes
            db.commit()

        faculty_timetable = generate_faculty_timetable(cursor, session.get('user_id'))
            

        # Render the template with the fetched schedule
        return render_template('dep_head/generate.html',
                               form=form,
                               schedule=display_schedule,
                               faculty_timetable=faculty_timetable,
                               sections=sections,
                               current_endpoint=request.endpoint)

    faculty_timetable = generate_faculty_timetable(cursor, session['user_id'])
    # If it's a GET request or form validation failed, just render the template without a schedule
    return render_template('dep_head/generate.html',
                           form=form,
                           schedule=display_schedule,
                           faculty_timetable=faculty_timetable,
                           sections=sections,
                           current_endpoint=request.endpoint)
