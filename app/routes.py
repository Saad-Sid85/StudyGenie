from flask import Blueprint, render_template, request, redirect, url_for, session
import bcrypt
import mysql.connector

from app.database import get_db_connection


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        college = request.form["college"]
        course = request.form["course"]
        branch = request.form["branch"]
        semester = request.form["semester"]

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        )

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            query = """
                INSERT INTO users
                (name, email, password, college, course, branch, semester)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                name,
                email,
                hashed_password.decode("utf-8"),
                college,
                course,
                branch,
                semester
            )

            cursor.execute(query, values)
            connection.commit()

        except mysql.connector.IntegrityError:
            return "Email already registered."

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("main.login"))

    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT *
            FROM users
            WHERE email = %s
        """

        cursor.execute(query, (email,))
        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"].encode("utf-8")
        ):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("main.dashboard"))

        return "Invalid email or password."

    return render_template("login.html")


@main.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT name, email, college, course, branch, semester
        FROM users
        WHERE id = %s
    """

    cursor.execute(query, (session["user_id"],))
    user = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        user=user
    )


# ---------------- TASKS ----------------

@main.route("/tasks")
def tasks():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT id, title, description, subject,
               due_date, priority, status
        FROM tasks
        WHERE user_id = %s
        ORDER BY due_date ASC
    """

    cursor.execute(query, (session["user_id"],))
    task_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "tasks.html",
        tasks=task_list
    )


@main.route("/tasks/add", methods=["GET", "POST"])
def add_task():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        subject = request.form["subject"]
        due_date = request.form["due_date"]
        priority = request.form["priority"]

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO tasks
            (user_id, title, description, subject, due_date, priority)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            session["user_id"],
            title,
            description,
            subject,
            due_date,
            priority
        )

        cursor.execute(query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("main.tasks"))

    return render_template("add_task.html")


@main.route("/tasks/complete/<int:task_id>")
def complete_task(task_id):

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        UPDATE tasks
        SET status = 'Completed'
        WHERE id = %s AND user_id = %s
    """

    cursor.execute(
        query,
        (task_id, session["user_id"])
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("main.tasks"))


@main.route("/tasks/delete/<int:task_id>")
def delete_task(task_id):

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        DELETE FROM tasks
        WHERE id = %s AND user_id = %s
    """

    cursor.execute(
        query,
        (task_id, session["user_id"])
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("main.tasks"))


# ---------------- LOGOUT ----------------

@main.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("main.login"))