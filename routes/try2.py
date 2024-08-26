import random
import mysql.connector
from geneticAlgorithm2 import Solution, generate_initial_solution, run_genetic_algorithm
from flask import current_app
import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'thesis_project'
}


def main():
    # Assuming generate_initial_solution is defined here or imported correctly
    solution = Solution()
    # # Initialize solution as needed...
    
    # # Run the genetic algorithm with the initial solution
    best_solution = run_genetic_algorithm(solution)

    # # Display the best schedule
    print("About to display the best solution's schedule:", best_solution.schedule)
    best_solution.display()

    # initial_solution = generate_initial_solution()
    
    # Display the initial solution's schedule
    # print("Generated initial solution's schedule:")
    # initial_solution.display()


if __name__ == "__main__":
    main()