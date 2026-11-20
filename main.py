import psycopg
from psycopg.rows import dict_row
from psycopg.errors import UniqueViolation

from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, EmailStr, Field


# DATABASE CONNECTION

def get_connection():
    return psycopg.connect(
        host="localhost",
        dbname="employee_db",
        user="employee_user",
        password="LocalDev@12345",
        port=5432,
        row_factory=dict_row
    )


# CREATE TABLE

try:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    department VARCHAR(50),
                    salary INTEGER
                );
            """)

    print("Employee table created successfully!")

except Exception as e:
    print("Database Error:", e)


# FASTAPI APP

app = FastAPI()


# PYDANTIC MODEL / INPUT VALIDATION

class Employee(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    department: str | None = Field(default=None, max_length=50)
    salary: int | None = Field(default=None, gt=0)


# HOME API

@app.get("/")
def home():
    return {
        "message": "Employee API is running"
    }


# 1. CREATE SINGLE EMPLOYEE

@app.post("/employees")
def create_employee(employee: Employee):

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO employees (name, email, department, salary)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        employee.name,
                        employee.email,
                        employee.department,
                        employee.salary
                    )
                )

                employee_id = cursor.fetchone()["id"]

        return {
            "message": "Employee added successfully",
            "employee_id": employee_id
        }

    except UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="This email already exists. Please use another email."
        )


# 2. UPDATE EMPLOYEE BY ID

@app.put("/employees/{employee_id}")
def update_employee(employee_id: int, employee: Employee):

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE employees
                    SET name = %s,
                        email = %s,
                        department = %s,
                        salary = %s
                    WHERE id = %s
                    RETURNING id;
                    """,
                    (
                        employee.name,
                        employee.email,
                        employee.department,
                        employee.salary,
                        employee_id
                    )
                )

                updated_employee = cursor.fetchone()

                if updated_employee is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Employee not found"
                    )

        return {
            "message": "Employee updated successfully",
            "employee_id": employee_id
        }

    except UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="This email already exists. Please use another email."
        )


# 2. GET ALL EMPLOYEES

@app.get("/employees")
def get_all_employees():

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM employees ORDER BY id"
            )

            employees = cursor.fetchall()

    return employees


# 3. GET EMPLOYEES BY DEPARTMENT

@app.get("/employees/department/{department}")
def get_employees_by_department(department: str):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM employees WHERE department = %s",
                (department,)
            )

            employees = cursor.fetchall()

    if not employees:
        raise HTTPException(
            status_code=404,
            detail="No employees found in this department"
        )

    return employees


# 4. GET EMPLOYEES WHOSE NAME STARTS WITH A LETTER

@app.get("/employees/name-starts/{letter}")
def get_employees_by_name(letter: str):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM employees WHERE name ILIKE %s",
                (letter + "%",)
            )

            employees = cursor.fetchall()

    if not employees:
        raise HTTPException(
            status_code=404,
            detail="No employees found with this starting letter"
        )

    return employees


# 5. GET EMPLOYEES WITH SALARY GREATER THAN A VALUE

@app.get("/employees/salary-greater-than/{salary}")
def get_employees_by_salary(salary: int):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM employees WHERE salary > %s",
                (salary,)
            )

            employees = cursor.fetchall()

    if not employees:
        raise HTTPException(
            status_code=404,
            detail="No employees found above this salary"
        )

    return employees


# 6. GET EMPLOYEES WITHIN A SALARY RANGE

@app.get("/employees/salary-range")
def get_employees_by_salary_range(
    min_salary: int = Query(ge=0),
    max_salary: int = Query(gt=0)
):

    if min_salary > max_salary:
        raise HTTPException(
            status_code=400,
            detail="Minimum salary cannot be greater than maximum salary"
        )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM employees
                WHERE salary BETWEEN %s AND %s
                """,
                (min_salary, max_salary)
            )

            employees = cursor.fetchall()

    if not employees:
        raise HTTPException(
            status_code=404,
            detail="No employees found in this salary range"
        )

    return employees


# 7. FILTER EMPLOYEES BY DEPARTMENT AND SALARY

@app.get("/employees/filter")
def filter_employees(
    department: str | None = None,
    min_salary: int | None = Query(default=None, ge=0),
    max_salary: int | None = Query(default=None, gt=0)
):

    if (
        min_salary is not None
        and max_salary is not None
        and min_salary > max_salary
    ):
        raise HTTPException(
            status_code=400,
            detail="Minimum salary cannot be greater than maximum salary"
        )

    query = "SELECT * FROM employees WHERE 1=1"
    values = []

    if department:
        query += " AND department = %s"
        values.append(department)

    if min_salary is not None:
        query += " AND salary >= %s"
        values.append(min_salary)

    if max_salary is not None:
        query += " AND salary <= %s"
        values.append(max_salary)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(values))

            employees = cursor.fetchall()

    if not employees:
        raise HTTPException(
            status_code=404,
            detail="No matching employees found"
        )

    return employees


# 8. SEARCH EMPLOYEES BY NAME

@app.get("/employees/search")
def search_employees(keyword: str):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM employees WHERE name ILIKE %s",
                ("%" + keyword + "%",)
            )

            employees = cursor.fetchall()

    if not employees:
        raise HTTPException(
            status_code=404,
            detail="No matching employees found"
        )

    return employees


# 9. SORT EMPLOYEES

@app.get("/employees/sort")
def sort_employees(
    sort_by: str = "name",
    order: str = "asc"
):

    allowed_columns = [
        "id",
        "name",
        "department",
        "salary"
    ]

    if sort_by not in allowed_columns:
        raise HTTPException(
            status_code=400,
            detail="Invalid sorting column"
        )

    if order.lower() not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Order must be asc or desc"
        )

    query = (
        f"SELECT * FROM employees "
        f"ORDER BY {sort_by} {order.upper()}"
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)

            employees = cursor.fetchall()

    return employees


# 10. PAGINATION

@app.get("/employees/page")
def get_employees_with_pagination(
    limit: int = Query(default=10, gt=0, le=100),
    offset: int = Query(default=0, ge=0)
):

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM employees
                ORDER BY id
                LIMIT %s OFFSET %s
                """,
                (limit, offset)
            )

            employees = cursor.fetchall()

    return {
        "limit": limit,
        "offset": offset,
        "employees": employees
    }


# 11. BULK INSERT EMPLOYEES

@app.post("/employees/bulk")
def create_multiple_employees(
    employees: list[Employee] = Body(...)
):

    if not employees:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one employee"
        )

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO employees (name, email, department, salary)
                    VALUES (%s, %s, %s, %s)
                    """,
                    [
                        (
                            employee.name,
                            employee.email,
                            employee.department,
                            employee.salary
                        )
                        for employee in employees
                    ]
                )

        return {
            "message": "Employees added successfully",
            "total_inserted": len(employees)
        }

    except UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="One or more email addresses already exist. No employees were inserted."
        )


# 12. DELETE EMPLOYEE BY ID (DELETE API)

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int):

    with get_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                DELETE FROM employees
                WHERE id = %s
                RETURNING id;
                """,
                (employee_id,)
            )

            deleted_employee = cursor.fetchone()

    if deleted_employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return {
        "message": "Employee deleted successfully",
        "employee_id": employee_id
    }

# UPDATE PARTIAL DETAILS OF AN EMPLOYEE (PATCH API)