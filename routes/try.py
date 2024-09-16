import random
import mysql.connector
from minorAlgorithm import Solution, generate_initial_solution, run_genetic_algorithm
from flask import current_app
import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'thesis_project'
}

def main():
    print("Starting the genetic algorithm process...")

    # Generate an initial solution
    initial_solution = generate_initial_solution()
    print("Initial solution generated.")

    # Display the initial solution
    print("\nInitial Solution Schedule:")
    initial_solution.display()

    # Run the genetic algorithm
    print("\nRunning genetic algorithm...")
    best_solution = run_genetic_algorithm(initial_solution)

    # Display the best solution
    print("\nBest Solution Schedule:")
    best_solution.display()

    # Compare initial and final fitness scores
    print(f"\nInitial Fitness Score: {initial_solution.fitness_score}")
    print(f"Final Fitness Score: {best_solution.fitness_score}")

    # Additional analysis
    print("\nDetailed Analysis:")
    print("\nDetailed Analysis:")
    for course_code, assignments in best_solution.schedule.items():
        print(f"\nSchedule for {course_code}:")
        for day, start_hour, duration, _ in assignments:
            print(f"  - Day: {day}, Start Time: {start_hour:.2f}, Duration: {duration:.2f}")
        print()

    print("Genetic Algorithm Process Complete.")

if __name__ == "__main__":
    main()