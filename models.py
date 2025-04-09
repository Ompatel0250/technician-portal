# This file would normally define SQLAlchemy models,
# but since we're using direct psycopg2 connections to an existing database,
# we don't need to define models in this implementation.
# 
# The existing tables in the PostgreSQL database are:
#
# CREATE TABLE appointments (
#     id SERIAL PRIMARY KEY,
#     intent TEXT,
#     name TEXT,
#     problem_description TEXT,
#     location TEXT,
#     contact TEXT,
#     time_slot TEXT,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );
#
# CREATE TABLE technicians (
#     id SERIAL PRIMARY KEY,
#     name TEXT NOT NULL,
#     expertise TEXT NOT NULL,
#     location TEXT NOT NULL,
#     contact TEXT NOT NULL,
#     email TEXT NOT NULL,
#     password TEXT NOT NULL
# );
