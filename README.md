# Employee Management API

This is a simple Employee Management API built using Python, FastAPI, and PostgreSQL. The main purpose of this project is to manage employee records through API endpoints.

The API allows users to add new employees, view employee details, update existing records, and delete employees from the database.

## Technologies Used
- Python
- FastAPI
- PostgreSQL
- Psycopg
- Postman

## Features
- Add a new employee
- Get all employees
- Get employee details by ID
- Update employee information
- Delete an employee
- Handle duplicate email entries

## Installation and Setup

1. Clone the repository:

   `git clone https://github.com/siddhantgulati/employee-management-api.git`

2. Go to the project directory:

   `cd employee-management-api`

3. Create a virtual environment:

   `python3 -m venv venv`

4. Activate the virtual environment:

   `source venv/bin/activate`

5. Install the required packages:

   `pip install -r requirements.txt`

6. Run the FastAPI server:

   `uvicorn main:app --reload`

## API Documentation

Once the server is running, open the following URL in your browser:

`http://127.0.0.1:8000/docs`

You can test all the available API endpoints using the Swagger UI.

## Database

PostgreSQL is used to store employee records. Make sure PostgreSQL is running and the database connection is configured before starting the application.
