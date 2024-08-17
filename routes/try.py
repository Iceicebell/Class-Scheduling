import random
import mysql.connector
from geneticAlgorithm import Solution, run_genetic_algorithm
from flask import current_app
import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'thesis_project'
}


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
            print(f"Assigning course {course_id} to section {section_id} on {day} starting at {start_hour} for {max_units} hours")
            solution.add_course_assignment(section_id, course_id, day, start_hour, max_units)

    return solution



def main():
    # Generate an initial solution
    solution = generate_initial_solution()
    
    # Display the generated schedule
    print("Generated Schedule:")
    solution.display()
    
    # Calculate and display the fitness score
    # fitness_score = solution.calculate_fitness()
    # print(f"Fitness Score: {fitness_score}")

if __name__ == "__main__":
    main()