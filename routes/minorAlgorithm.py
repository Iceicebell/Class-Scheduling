import cProfile
from copy import deepcopy
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

bp = Blueprint('minorAlgorithm', __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
POPULATION_SIZE = 5
MAX_GENERATIONS = 5
MUTATION_RATE = 0.1


class Solution:
    faculty_cache = {}
    def __init__(self, schedule=None, shared_schedule=None):
        self.schedule = schedule if schedule else {}
        self.shared_schedule = shared_schedule if shared_schedule else {}
        self.fitness_score = None

    def add_course_assignment(self, course_id, day, start_hour, duration, course_code, course_block, cursor):
        if course_id not in self.schedule:
            self.schedule[course_id] = []
        
        duration_decimal = Decimal(duration)

        if start_hour + duration_decimal > 13 and start_hour < 12:
            start_hour = 13
        elif start_hour + duration_decimal > 20:
            start_hour = 20 - duration_decimal

        start_hour = max(7, start_hour)

        max_duration = min(12 - start_hour, duration_decimal) if start_hour < 12 else duration_decimal
        if start_hour >= 12:
            max_duration = min(20 - start_hour, duration_decimal)

        existing_assignments = [tuple(a[:-1]) for a in self.schedule[course_id]]
        if (day, start_hour) not in existing_assignments:
            self.schedule[course_id].append((day, start_hour, max_duration, course_code, course_block))
        else:
            pass

        faculty_id = self.get_faculty_id(cursor, course_id)
        conflicting_courses = [cid for cid, assignments in self.schedule.items() 
                            if self.get_faculty_id(cursor, cid) == faculty_id 
                            and cid != course_id]

        for conflicting_course in conflicting_courses:
            conflicting_assignments = self.schedule[conflicting_course]
            for i, assignment in enumerate(conflicting_assignments):
                conflict_day, conflict_start, conflict_duration, _, _ = assignment
                
                if day == conflict_day and start_hour < conflict_start < start_hour + max_duration:
                    new_conflicting_start = conflict_start + max_duration
                    while new_conflicting_start in [a[1] for a in conflicting_assignments]:
                        new_conflicting_start += 2
                    
                    paired_day = self.get_pair_day(conflict_day)
                    for j, paired_assignment in enumerate(conflicting_assignments):
                        paired_day_j, _, _, _, _ = paired_assignment
                        if paired_day_j == paired_day:
                            conflicting_assignments[j] = (paired_day, new_conflicting_start, max_duration, conflicting_assignments[j][3], conflicting_assignments[j][4])
                    
                    conflicting_assignments[i] = (conflict_day, new_conflicting_start, max_duration, conflicting_assignments[i][3], conflicting_assignments[i][4])
                    # print(f"Moved conflicting course {conflicting_course} to avoid overlap")

        self.fitness_score = None

    def get_pair_day(self, day):
        day_pairs = {
            'Monday': 'Wednesday',
            'Tuesday': 'Friday',
            'Thursday': 'Saturday'
        }
        return day_pairs.get(day, day)

    def get_faculty_id(self, cursor, course_id):
        if course_id in self.faculty_cache:
            return self.faculty_cache[course_id]
        
        query = "SELECT faculty_id FROM courses WHERE course_id = %s"
        cursor.execute(query, (course_id,))
        result = cursor.fetchone()
        faculty_id = result[0] if result else None
        self.faculty_cache[course_id] = faculty_id
        return faculty_id



    def calculate_fitness(self, cursor):
        if self.fitness_score is None:
            fitness_score = Decimal(0)
            conflicts_penalty = Decimal(0)
            efficiency_reward = Decimal(0)
            consistency_reward = Decimal(0)
            lunch_break_reward = Decimal(0)
            balanced_schedule_reward = Decimal(0)
            late_course_penalty = Decimal(0)

            # Penalty for overlapping courses within the same faculty
            for course_id1, assignments1 in self.schedule.items():
                for course_id2, assignments2 in self.schedule.items():
                    if course_id1 != course_id2:
                        faculty_id1 = self.get_faculty_id(cursor, course_id1)
                        faculty_id2 = self.get_faculty_id(cursor, course_id2)
                        if faculty_id1 == faculty_id2:  # Same faculty
                            for assignment1 in assignments1:
                                day1, start_hour1, duration1, _, _ = assignment1
                                for assignment2 in assignments2:
                                    day2, start_hour2, duration2, _, _ = assignment2
                                    if day1 == day2: 
                                        end_time1 = start_hour1 + duration1
                                        end_time2 = start_hour2 + duration2
                                        if start_hour1 < start_hour2 < end_time1 or start_hour1 < end_time2 < end_time1: 
                                            conflicts_penalty += Decimal(1000)  
                                            # print(f"Conflict detected: Course {course_id1} and Course {course_id2} overlap on {day1}")

            # Reward for consistency in split courses
            for course_id, assignments in self.schedule.items():
                if len(assignments) > 1:
                    days = [assignment[0] for assignment in assignments]
                    start_hours = [assignment[1] for assignment in assignments]
                    if len(set(days)) == 2 and len(set(start_hours)) == 1:
                        consistency_reward += Decimal(200) 
                        # print(f"Consistent split course found: Course {course_id}")

            # Penalty for disregarding lunch breaks
            for course_id, assignments in self.schedule.items():
                for assignment in assignments:
                    day, start_hour, duration, course_code, _ = assignment
                    end_time = start_hour + duration
                    if 12 <= start_hour < 13 and end_time > 13:  
                        conflicts_penalty += Decimal(100) 
                        # print(f"Course {course_id} spans over lunch break on {day}")
                    elif 12 <= end_time <= 13: 
                        lunch_break_reward -= Decimal(50) 
                        # print(f"Course {course_id} scheduled during lunch break on {day}")

            # Penalty for late courses (exceeding 17:00)
            for course_id, assignments in self.schedule.items():
                for assignment in assignments:
                    day, start_hour, duration, course_code, _ = assignment
                    end_time = start_hour + duration
                    if end_time > 17:
                        late_course_penalty += Decimal(200) * (Decimal(end_time) - Decimal(17)) 
                        # print(f"Course {course_id} ends late ({end_time}) on {day}")

            # Reward for efficient utilization (filling morning and afternoon slots)
            for course_id, assignments in self.schedule.items():
                morning_slots_filled = sum(Decimal(5) for _, start_hour, _, _, _ in assignments if start_hour < 12)
                afternoon_slots_filled = sum(Decimal(5) for _, start_hour, _, _, _ in assignments if start_hour >= 13)
                efficiency_reward += min(morning_slots_filled, afternoon_slots_filled) 


            # Calculate total fitness score
            self.fitness_score = efficiency_reward + consistency_reward + lunch_break_reward + balanced_schedule_reward - conflicts_penalty - late_course_penalty
            # print("Fitness Score: ", self.fitness_score)
        return self.fitness_score

    def display(self):
        for course_code, assignments in self.schedule.items():
            print(f"\nSchedule for {course_code}:")
            for assignment in assignments:
                day, start_hour, duration, course_code, course_block = assignment
                # print(f"Day: {day}, Start Hour: {start_hour:.2f}, Duration: {duration:.2f}, Block: {course_block}")

def generate_initial_solution():
    solution = Solution(shared_schedule={})
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    try:
        print("Starting generate_initial_solution()")

        cursor.execute("""
            SELECT course_id, hours_per_week, course_code, course_block
            FROM gened_courses
        """)
        courses_data = cursor.fetchall()

        # print("Generating initial solution...")
        for course_data in courses_data:
            try:
                course_id, hours_per_week, course_code, course_block = course_data

                hours_per_week_decimal = Decimal(hours_per_week)

                if hours_per_week_decimal > Decimal(2):
                    split_duration_decimal = hours_per_week_decimal / Decimal(2)
                    

                    morning_period = range(7, 12)
                    afternoon_period = range(13, 20)
                    combined_periods = list(morning_period) + list(afternoon_period)
                    start_hour = random.choice(combined_periods)
                    
                    # Select days for the split course
                    day_options = ['Monday', 'Tuesday', 'Thursday']
                    day1 = random.choice(day_options)
                    day2 = solution.get_pair_day(day1)
                    

                    solution.add_course_assignment(course_id, day1, start_hour, split_duration_decimal, course_code, course_block, cursor)
                    solution.add_course_assignment(course_id, day2, start_hour, split_duration_decimal, course_code, course_block, cursor)
                else:
                    day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
                    start_hour = random.randint(7, 19)
                    solution.add_course_assignment(course_id, day, start_hour, hours_per_week_decimal, course_code, course_block, cursor)

            except Exception as e:
                # print(f"Error processing course {course_id}: {str(e)}")
                import traceback
                traceback.print_exc()

        # print("Initial solution generated.")
    finally:
        cursor.close()
        db.close()
    return solution

def crossover(parent1, parent2):
    child_schedule = {}
    

    for course_id in set(parent1.schedule.keys()).union(parent2.schedule.keys()):
        if course_id in parent1.schedule:
            child_schedule[course_id] = parent1.schedule[course_id].copy()
        elif course_id in parent2.schedule:
            child_schedule[course_id] = parent2.schedule[course_id].copy()


    child_solution = Solution(schedule=child_schedule)
    return child_solution


def mutate(self, cursor):
    course_id = random.choice(list(self.schedule.keys()))
    if not self.schedule[course_id]:
        # print(f"Course {course_id} has no assignments. Skipping mutation.")
        return  

    assignments = self.schedule[course_id]
    if len(assignments) > 1:
        assignment_index = random.randrange(len(assignments))
        day, start_hour, duration, course_code, course_block = assignments[assignment_index]
    else:
        day, start_hour, duration, course_code, course_block = assignments[0]

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

        self.schedule[course_id][assignment_index] = (new_day, new_start_hour, max_duration, course_code, course_block)
    except Exception as e:
        # print(f"An error occurred during mutation: {e}")
        return  


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
            population = population[:POPULATION_SIZE]  # Trim to original size, keeping only the best solutions
        
        best_solution = max(population, key=lambda x: x.fitness_score)
    finally:
        cursor.close()
        db.close()
    # print("Selected best solution's schedule:", best_solution.schedule)
    return best_solution

def get_best_solution():
    initial_solution = generate_initial_solution()
    return run_genetic_algorithm(initial_solution)



class GenerateForm(FlaskForm):
    population_size = IntegerField('Population Size', default=100)
    max_generations = IntegerField('Max Generations', default=500)
    submit = SubmitField('Generate Schedule')







@bp.route('/gen-ed/generate', methods=['GET', 'POST'])
def generate():
    if session.get('isVerified') == False:
        return redirect(url_for('my_blueprint.new_user'))
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if session.get('user_role') != 'gen-ed':
        abort(403)

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    form = GenerateForm()
    display_schedule = {}
    faculty_timetable = {}


    cursor.execute("""
        SELECT gs.course_id, gs.day, gs.start_hour, gs.duration, gc.course_code, gc.course_block, f.first_name, f.last_name
        FROM gened_solutions gs
        JOIN gened_courses gc ON gs.course_id = gc.course_id
        JOIN faculties f ON gc.faculty_id = f.faculty_id
        WHERE gs.user_id = %s
    """, (session['user_id'],))
    saved_solutions = cursor.fetchall()

    # Process the schedule data
    for course_id, day, start_hour, duration, course_code, course_block, first_name, last_name in saved_solutions:
        if course_id != -1: 
            course_key = f"{course_code}/{course_block}"
            

            if course_key not in display_schedule:
                display_schedule[course_key] = {}
            if day not in display_schedule[course_key]:
                display_schedule[course_key][day] = []
            display_schedule[course_key][day].append({
                'start_hour': f"{int(start_hour)}:{int((start_hour % 1) * 60):02d}",
                'end_hour': f"{int(start_hour + duration)}:{int(((start_hour + duration) % 1) * 60):02d}"
            })


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

    if request.method == 'POST':
        if form.validate_on_submit():
            global POPULATION_SIZE, MAX_GENERATIONS
            POPULATION_SIZE = form.population_size.data
            MAX_GENERATIONS = form.max_generations.data


            profiler = cProfile.Profile()
            profiler.enable()
            best_solution = get_best_solution()
            profiler.disable()
            stats = pstats.Stats(profiler).sort_stats('cumtime')
            stats.print_stats(10)


            cursor.execute("DELETE FROM gened_solutions WHERE user_id = %s", (session['user_id'],))


            query = """
                INSERT INTO gened_solutions 
                (id, user_id, course_id, day, start_hour, duration, course_code, course_block)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = []
            for course_id, assignments in best_solution.schedule.items():
                for assignment in assignments:
                    try:
                        day, start_hour, duration, course_code, course_block = assignment
                    except ValueError:
                        continue
                    values.append((
                        None,
                        session['user_id'],
                        course_id,
                        day,
                        float(start_hour),
                        float(duration),
                        course_code,
                        course_block
                    ))

            cursor.executemany(query, values)


            db.commit()
            flash('Algorithm completed successfully. The page will reload to display the changes.')
 
    return render_template('genEd/genEd_generate.html',
                           form=form,
                           student_schedule=display_schedule,
                           faculty_timetable=faculty_timetable,
                           current_endpoint=request.endpoint)