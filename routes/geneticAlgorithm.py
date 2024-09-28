import cProfile
from decimal import Decimal
import pstats
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
POPULATION_SIZE = 200
MAX_GENERATIONS = 100
MUTATION_RATE = 0.01
    
class Solution:
    faculty_cache = {}
    def __init__(self, schedule=None, shared_schedule=None):
        self.schedule = schedule if schedule else {}
        self.shared_schedule = shared_schedule if shared_schedule else {}
        self.fitness_score = None

    def add_course_assignment(self, section_id, course_id, day, start_hour, duration, course_code, course_block, cursor):
        if section_id not in self.schedule:
            self.schedule[section_id] = []
        
        duration_decimal = Decimal(duration)
        hours_per_week = self.get_course_hours_per_week(cursor, course_id)

        if start_hour + duration_decimal > 13 and start_hour < 12:
            start_hour = 13
        elif start_hour + duration_decimal > 20:
            start_hour = 20 - duration_decimal  

        start_hour = max(7, start_hour)
        
        max_duration = min(12 - start_hour, duration_decimal) if start_hour < 12 else duration_decimal 
        if start_hour >= 12:
            max_duration = min(20 - start_hour, duration_decimal)  

        if hours_per_week >= 2:
            if day in ['Monday', 'Tuesday', 'Thursday']:
                days = [day, self.get_pair_day(day)]
            else:
                days = [day, self.get_pair_day(day)]
            split_duration_decimal = hours_per_week / Decimal(2)
        else:
            days = [day] 
            split_duration_decimal = duration_decimal
        
        for d in days:
            max_duration = min(12 - start_hour, split_duration_decimal) if start_hour < 12 else split_duration_decimal
            if start_hour >= 12:
                max_duration = min(20 - start_hour, split_duration_decimal)

            if self.is_slot_available(section_id, d, start_hour, max_duration):
                self.schedule[section_id].append((course_id, d, start_hour, max_duration, course_code, course_block))
            else:
                # print(f"Slot not available for course {course_id} on {d} at {start_hour}")
                pass

        self.fitness_score = None


    def fetch_unavailable_times(self, cursor, section_id):
        """Fetches unavailable times for a section and adds them to the schedule as if they were courses."""
        query = "SELECT day_of_week, start_time, end_time, course_code, block FROM unavailable_times WHERE section_id = %s"
        cursor.execute(query, (section_id,))
        unavailable_periods = cursor.fetchall()
        for day, start_time, end_time, course_code, block in unavailable_periods:

            day = self.convert_day_format(day)

            pseudo_course_id = -1

            duration = end_time - start_time

            self.add_course_assignment(section_id, pseudo_course_id, day, start_time, duration, course_code, block, cursor)

    def convert_day_format(self, day_of_week):
        """Converts the day format from the database to the format used in your schedule."""

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
            for start_hour in range(7, 20): 
                if self.is_slot_available(section_id, day, start_hour, duration):
                    available_slots.append((day, start_hour))
        return available_slots

    def is_slot_available(self, section_id, day, start_hour, duration):
        end_hour = start_hour + duration

        if start_hour < 13 and end_hour > 12:
            return False

        for course_id, course_day, course_start, course_duration, _, _ in self.schedule.get(section_id, []):
            course_end = course_start + course_duration
            if day == course_day and (
                (start_hour < course_end and end_hour > course_start) or
                (course_start < end_hour and course_end > start_hour)
            ):
                return False
        return True
    
    def get_schedule_by_course_code_and_block(self, course_code, course_block):

        return self.shared_schedule.get((course_code, course_block), (None, None))

    def add_shared_schedule(self, course_code, course_block, assignments):
        key = (course_code, course_block)
        if key not in self.shared_schedule:
            self.shared_schedule[key] = []


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
        if course_id in self.faculty_cache:
            return self.faculty_cache[course_id]
        
        query = "SELECT faculty_id FROM courses WHERE course_id = %s"
        cursor.execute(query, (course_id,))
        result = cursor.fetchone()
        faculty_id = result[0] if result else None
        self.faculty_cache[course_id] = faculty_id
        return faculty_id

    def check_unit_match(self, cursor):
        unit_match_score = 0
        for section_assignments in self.schedule.values():
            for course_id, _, _, duration, _, _ in section_assignments:
                expected_hours = self.get_course_hours_per_week(cursor, course_id)
                scheduled_hours = sum(dur for _, _, _, dur, _, _ in section_assignments if dur == duration)
                unit_match_score -= abs(expected_hours - scheduled_hours)
        return unit_match_score



    def get_course_hours_per_week(self, cursor, course_id):
        query = "SELECT hours_per_week FROM courses WHERE course_id = %s"
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


        for section_id, assignments in self.schedule.items():
            for i, (course_id1, day1, start_hour1, duration1, course_code1, course_block1) in enumerate(assignments):
                for j in range(i + 1, len(assignments)):
                    course_id2, day2, start_hour2, duration2, course_code2, course_block2 = assignments[j]
                    if day1 == day2: 
                        end_time1 = start_hour1 + duration1
                        end_time2 = start_hour2 + duration2
                        if start_hour1 < start_hour2 < end_time1 or start_hour1 < end_time2 < end_time1: 
                            conflicts_penalty += 4000 
                        
                        faculty_id1 = self.get_faculty_id(cursor, course_id1)
                        faculty_id2 = self.get_faculty_id(cursor, course_id2)
                        

                        if faculty_id1 == faculty_id2 and (course_code1 != course_code2 or course_block1 != course_block2):
                            conflicts_penalty += 3000 


        for section_id, assignments in self.schedule.items():
            for course_id, day, start_hour, duration, course_code, course_block in assignments:
                if 12 <= start_hour < 13 and start_hour + duration > 13: 
                    conflicts_penalty += 100


        course_code_block_groups = {}
        for section_id, assignments in self.schedule.items():
            for course_id, day, start_hour, duration, course_code, course_block in assignments:
                key = (course_code, course_block)
                if key not in course_code_block_groups:
                    course_code_block_groups[key] = []
                course_code_block_groups[key].append((course_id, day, start_hour, duration))
                if len(course_code_block_groups[key]) > 1: 
                    integrity_reward += 1000 


        for section_id, assignments in self.schedule.items():
            morning_slots_filled = sum(5 for _, day, start_hour, _, _, _ in assignments if start_hour < 12)
            afternoon_slots_filled = sum(5 for _, day, start_hour, _, _, _ in assignments if start_hour >= 13)
            efficiency_reward += min(morning_slots_filled, afternoon_slots_filled) 


        self.fitness_score = integrity_reward + efficiency_reward - conflicts_penalty - utilization_penalty
        # print("Fitness Score: ",self.fitness_score)
        return self.fitness_score


    
    def __lt__(self, other):
            """Less than comparison method."""
            if not isinstance(other, type(self)):

                return NotImplemented

            return self.fitness_score < other.fitness_score if other.fitness_score is not None else False


    def __eq__(self, other):
        """Equality comparison method."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.fitness_score == other.fitness_score if other.fitness_score is not None else False
    
    def find_available_slot(self, section_id, duration):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        start_hours = list(range(7, 20))  # 7 AM to 7 PM
        

        random.shuffle(days)
        random.shuffle(start_hours)
        
        for day in days:
            for start_hour in start_hours:
                end_hour = start_hour + duration
                

                if start_hour < 12 and end_hour > 13:
                    continue
                

                if end_hour > 20:
                    continue
                

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
        

        return None


    def display(self):

        for section_id, assignments in self.schedule.items():
            print(f"\nSchedule for Section {section_id}:")
            for course_id, day, start_hour, duration, course_code, course_block in assignments: 
                print(f"Course ID: {course_id}, Day: {day}, Start Hour: {start_hour}, Duration: {duration}, Course Code: {course_code}, Block: {course_block}")

            

            schedule_by_day = {'Monday': [], 'Tuesday': [], 'Wednesday': [], 'Thursday': [], 'Friday': [], 'Saturday': []}
            for course_id, day, start_hour, duration, _, _ in assignments:  
                schedule_by_day[day].append((course_id, f"{start_hour}-{start_hour + duration}"))
            

            max_courses_per_day = max(len(courses) for courses in schedule_by_day.values())
            

            print("-" * 80)
            print("Course ID", end='\t')
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday']:
                print(f"{day:<15}", end='\t')
            print("\n" + "-" * 80)
            

            for i in range(max_courses_per_day):
                row = [""] * 6 
                for j, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday','Saturday']):
                    if i < len(schedule_by_day[day]):
                        course_id, time_slot = schedule_by_day[day][i]
                        row[j] = f"{course_id:<10}{time_slot:<15}"
                    else:
                        row[j] = " " * 1 
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

    child_schedule = {}
    child_shared_schedule = {}


    for course_id in set(parent1.schedule.keys()).union(parent2.schedule.keys()):

        if course_id in parent1.schedule:
            child_schedule[course_id] = parent1.schedule[course_id].copy()
        elif course_id in parent2.schedule:
            child_schedule[course_id] = parent2.schedule[course_id].copy()


    for course_id in set(parent1.shared_schedule.keys()).union(parent2.shared_schedule.keys()):
        if course_id in parent1.shared_schedule:
            child_shared_schedule[course_id] = parent1.shared_schedule[course_id]
        elif course_id in parent2.shared_schedule:
            child_shared_schedule[course_id] = parent2.shared_schedule[course_id]


    for course_id, blocks_list in child_schedule.items():
        corrected_blocks = []
        for block in blocks_list:  
            day, start_hour, end_hour, *rest = block 
            if end_hour > 20:
                end_hour = 20 
            corrected_blocks.append((day, start_hour, end_hour, *rest))
        child_schedule[course_id] = corrected_blocks


    child_solution = Solution(schedule=child_schedule, shared_schedule=child_shared_schedule)
    return child_solution

    

def mutate(self, cursor):
    section_id = random.choice(list(self.schedule.keys()))
    if not self.schedule[section_id]:
        #print(f"Section {section_id} has no courses assigned. Skipping mutation.")
        return 
    
    course_index = random.randrange(len(self.schedule[section_id]))
    course_info = self.schedule[section_id][course_index]
    # print(f"Course info before unpacking: {course_info}")
    course_id, day, start_hour, duration, course_code, course_block = course_info 
    new_slot = self.find_available_slot(section_id, duration)
    if new_slot:
        self.remove_course_assignment(section_id, course_id)
        self.add_course_assignment(section_id, course_id, new_slot[0], new_slot[1], duration, course_code, course_block, cursor)
    try:
        new_day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        

        morning_period = range(7, 12)
        afternoon_period = range(13, 20)
        combined_periods = list(morning_period) + list(afternoon_period)
        new_start_hour = random.choice(combined_periods)
        

        if new_start_hour + duration > 13 and new_start_hour < 12:
            new_start_hour = 13  
        max_duration = duration  
        if new_start_hour + duration > 20:
            max_duration = 20 - new_start_hour 


        self.shared_schedule[(course_code, course_block)] = (new_day, new_start_hour, max_duration)
        

    except Exception as e:
        print(f"An error occurred during mutation: {e}")
        return  


def generate_initial_solution():
    solution = Solution(shared_schedule={})
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    try:
        # print("Starting generate_initial_solution()")
        
        # Fetch sections owned by the current user
        # print("Executing SQL query...")
        cursor.execute("""
            SELECT s.section_id, c.course_id, c.hours_per_week, c.course_code, c.course_block
            FROM sections s
            JOIN section_courses sc ON s.section_id = sc.section_id
            JOIN courses c ON sc.course_id = c.course_id
            WHERE s.user_id = %s;
        """, (session.get('user_id'),))
        
        print("Fetching results...")
        sections_data = cursor.fetchall()
        
        # print(f"sections_data length: {len(sections_data)}")
        # print(f"First row of sections_data: {sections_data[0]}")
        # print(f"Number of columns in first row: {len(sections_data[0])}")

        # print("Processing unavailable times...")
        for section_id, _, _, _, _ in sections_data:
            try:
                solution.fetch_unavailable_times(cursor, section_id)
            except Exception as e:
                print(f"Error fetching unavailable times for section {section_id}: {str(e)}")

        # print("Grouping courses...")
        grouped_courses = {}
        for section_id, course_id, hours_per_week, course_code, course_block in sections_data:
            key = (course_code, course_block)
            if key not in grouped_courses:
                grouped_courses[key] = []
            grouped_courses[key].append((section_id, course_id, hours_per_week))

        # print(f"Number of grouped courses: {len(grouped_courses)}")
        
        # Rest of the function remains the same...
        # print("Generating initial solution...")
        for (course_code, course_block), courses in grouped_courses.items():
            # print(f"Processing course group: {course_code}/{course_block}")
            day_options = ['Monday', 'Tuesday', 'Thursday']
            day = random.choice(day_options)
            second_day = solution.get_pair_day(day)
            
            morning_period = range(7, 12)
            afternoon_period = range(13, 20)
            combined_periods = list(morning_period) + list(afternoon_period)
            start_hour = random.choice(combined_periods)
            
            # print(f"Day: {day}, Second Day: {second_day}, Start Hour: {start_hour}")
            
            for section_id, course_id, hours_per_week in courses:
                # print(f"Processing course: {course_id} ({course_code}/{course_block})")
                
                try:
                    # print(f"Course details: Section ID: {section_id}, Course ID: {course_id}, Hours per week: {hours_per_week}")
                    
                    hours_per_week_decimal = Decimal(hours_per_week)
                    # print(f"Hours per week decimal: {hours_per_week_decimal}")
                    
                    if hours_per_week_decimal > Decimal(2):
                        split_duration_decimal = hours_per_week_decimal / Decimal(2)
                        # print(f"Split duration: {split_duration_decimal}")
                        
                        solution.add_course_assignment(section_id, course_id, day, start_hour, split_duration_decimal, course_code, course_block, cursor)
                        # print(f"Added first part of split course")
                        
                        solution.add_course_assignment(section_id, course_id, second_day, start_hour, split_duration_decimal, course_code, course_block, cursor)
                        # print(f"Added second part of split course")
                    else:
                        solution.add_course_assignment(section_id, course_id, day, start_hour, hours_per_week_decimal, course_code, course_block, cursor)
                        # print(f"Added non-split course")
                    
                except Exception as e:
                    print(f"Error processing course {course_id}: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            # print(f"Finished processing course group: {course_code}/{course_block}")

        # logging.info("Initial solution generated.")
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
        population = [initial_solution] + [generate_initial_solution() for _ in range(POPULATION_SIZE - 1)]  
        

        for solution in population:
            solution.calculate_fitness(cursor)
        
        for _ in range(MAX_GENERATIONS):
            new_population = []
            elite_count = POPULATION_SIZE // 10
            new_population.extend(population[:elite_count])

            while len(new_population) < POPULATION_SIZE:

                parent1, parent2 = select_parents(population)
                

                child = crossover(parent1, parent2)  
                

                if random.random() < MUTATION_RATE:
                    mutate(child, cursor)  
                new_population.append(child)
            

            population = new_population
            

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


def get_best_solution():
    initial_solution = generate_initial_solution()
    return run_genetic_algorithm(initial_solution)

class GenerateForm(FlaskForm):
    submit = SubmitField('Generate Schedule')
def generate_faculty_timetable(cursor, current_user_id):
    faculty_timetable = {}
    

    cursor.execute("SELECT faculty_id, first_name, last_name FROM faculties WHERE faculty_id IN (SELECT faculty_id FROM courses WHERE course_id IN (SELECT course_id FROM section_courses WHERE section_id IN (SELECT section_id FROM sections WHERE user_id = %s)))", (current_user_id,))
    faculty_data = cursor.fetchall()
    faculty_names = {faculty_id: f"{first_name} {last_name}" for faculty_id, first_name, last_name in faculty_data}
    

    cursor.execute("SELECT user_id, section_id, course_id, day, start_hour, duration, course_code, course_block FROM user_solutions")
    course_assignments = cursor.fetchall()
    

    for user_id, section_id, course_id, day, start_hour, duration, course_code, course_block in course_assignments:

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

    cursor.execute("""
        SELECT user_id, section_id, course_id, day, start_hour, duration, course_code, course_block
        FROM user_solutions
        WHERE user_id = %s
    """, (session['user_id'],))

    saved_solutions = cursor.fetchall()
    

    cursor.execute("SELECT section_id, section_name FROM sections WHERE user_id = %s", (session['user_id'],))
    sections = cursor.fetchall()
    

    section_names = {row[0]: row[1] for row in sections}

    display_schedule = {}
    for user_id, section_id, course_id, day, start_hour, duration, course_code, course_block in saved_solutions:
        section_name = section_names.get(section_id, f"Section {section_id}")
        if section_name not in display_schedule:
            display_schedule[section_name] = {'courses': {}}
            
        course_key = f"{course_code}/{course_block}"
        if course_key not in display_schedule[section_name]['courses']:
            display_schedule[section_name]['courses'][course_key] = {}
        if day not in display_schedule[section_name]['courses'][course_key]:
            display_schedule[section_name]['courses'][course_key][day] = []
        
        display_schedule[section_name]['courses'][course_key][day].append({
            'start_hour': f"{int(start_hour)}:{int((start_hour % 1) * 60):02d}",
            'end_hour': f"{int(start_hour + duration)}:{int(((start_hour + duration) % 1) * 60):02d}"
        })

        
    form =  GenerateForm()
    faculty_timetable = None 
    if request.method == 'POST':
        if form.validate_on_submit():
            global POPULATION_SIZE, MAX_GENERATIONS


            profiler = cProfile.Profile()
            profiler.enable()
            best_solution = get_best_solution()
            profiler.disable()
            stats = pstats.Stats(profiler).sort_stats('cumtime')
            stats.print_stats(10)  

            

            best_solution = get_best_solution()


            cursor.execute("DELETE FROM user_solutions WHERE user_id = %s", (session['user_id'],))

            query = """
                INSERT INTO user_solutions 
                (id, user_id, section_id, course_id, day, start_hour, duration, course_code, course_block)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = []
            for section_id, courses in best_solution.schedule.items():
                for course_id, day, start_hour, duration, course_code, course_block in courses:
                    values.append((
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

            cursor.executemany(query, values)

            db.commit()

        faculty_timetable = generate_faculty_timetable(cursor, session.get('user_id'))
            


        return render_template('dep_head/generate.html',
                               form=form,
                               schedule=display_schedule,
                               faculty_timetable=faculty_timetable,
                               sections=sections,
                               current_endpoint=request.endpoint)

    faculty_timetable = generate_faculty_timetable(cursor, session['user_id'])

    return render_template('dep_head/generate.html',
                           form=form,
                           schedule=display_schedule,
                           faculty_timetable=faculty_timetable,
                           sections=sections,
                           current_endpoint=request.endpoint)