from decimal import Decimal
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


bp = Blueprint('RoomAlgorithm', __name__)


class Chromosome:
    def __init__(self, length):
        self.genes = [0] * length  # 0 represents empty room, 1 represents assigned room

    def mutate(self):
        index = random.randint(0, len(self.genes) - 1)
        self.genes[index] = 1 - self.genes[index]

    def fitness(self, rooms, courses, schedules):
        fitness = 0
        for i, gene in enumerate(self.genes):
            if gene == 1:
                room_id = i // (len(courses) + len(schedules))  # Room ID calculation
                course_id = (i % (len(courses) + len(schedules))) // len(schedules)
                schedule_id = i % len(schedules)
                
                # Check capacity constraint
                if not check_capacity(rooms[room_id], courses[course_id]):
                    fitness -= 10
                
                # Check section assignment
                if len(courses[course_id]['sections']) > 1 and not check_section_assignment(courses[course_id], schedules[schedule_id]):
                    fitness -= 5
                
                # Check overlap
                if not check_no_overlap(schedules[schedule_id]):
                    fitness -= 8
                
                # Assign department to floor
                if not check_department_floor_assignment(courses[course_id], rooms[room_id]):
                    fitness -= 3
        
        return fitness
class Chromosome:
    def __init__(self, length):
        self.genes = [0] * length  # 0 represents empty room, 1 represents assigned room

    def mutate(self):
        index = random.randint(0, len(self.genes) - 1)
        self.genes[index] = 1 - self.genes[index]

    def fitness(self, rooms, courses, schedules):
        fitness = 0
        for i, gene in enumerate(self.genes):
            if gene == 1:
                room_id = i // (len(courses) + len(schedules))  # Room ID calculation
                course_id = (i % (len(courses) + len(schedules))) // len(schedules)
                schedule_id = i % len(schedules)
                
                # Check capacity constraint
                if not check_capacity(rooms[room_id], courses[course_id]):
                    fitness -= 10
                
                # Check section assignment
                if len(courses[course_id]['sections']) > 1 and not check_section_assignment(courses[course_id], schedules[schedule_id]):
                    fitness -= 5
                
                # Check overlap
                if not check_no_overlap(schedules[schedule_id]):
                    fitness -= 8
                
                # Assign department to floor
                if not check_department_floor_assignment(courses[course_id], rooms[room_id]):
                    fitness -= 3
        
        return fitness

def initialize_population(pop_size, length):
    population = []
    for _ in range(pop_size):
        chromosome = Chromosome(length)
        chromosome.mutate()
        population.append(chromosome)
    return population

def genetic_algorithm(rooms, courses, schedules, pop_size=100, generations=100):
    population = initialize_population(pop_size, len(rooms) * (len(courses) + len(schedules)))
    
    for generation in range(generations):
        population.sort(key=lambda x: x.fitness(rooms, courses, schedules), reverse=True)
        
        # Selection
        selected = population[:int(pop_size * 0.2)]
        
        # Crossover
        offspring = []
        while len(offspring) < pop_size - len(selected):
            parent1, parent2 = random.sample(selected, 2)
            child = Chromosome(len(parent1.genes))
            for i in range(len(child.genes)):
                if random.random() > 0.5:
                    child.genes[i] = parent1.genes[i]
                else:
                    child.genes[i] = parent2.genes[i]
            offspring.append(child)
        
        # Mutation
        for child in offspring:
            child.mutate()
        
        # Replace least fit individuals
        population = selected + offspring
        
        print(f"Generation {generation+1}, Best fitness: {population[0].fitness(rooms, courses, schedules)}")
    
    return population[0]

def check_capacity(room, course):
    # Implement logic to check if room has enough capacity
    pass

def check_section_assignment(course, schedule):
    # Implement logic to check if sections are assigned to the same room
    pass

def check_no_overlap(schedule):
    # Implement logic to check for overlapping times
    pass

def check_department_floor_assignment(course, room):
    # Implement logic to assign department to floor based on room allocation
    pass

