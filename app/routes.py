from flask import Blueprint, render_template, request, redirect, url_for, session
import bcrypt
import mysql.connector

from app.ai.quiz_generator import generate_quiz
from app.database import get_db_connection


main = Blueprint("main", __name__)


# ============================================================
# HOME
# ============================================================

@main.route("/")
def home():
    return render_template("index.html")


# ============================================================
# REGISTER
# ============================================================

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

        # Hash password
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


# ============================================================
# LOGIN
# ============================================================

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


# ============================================================
# DASHBOARD
# ============================================================

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


# ============================================================
# TASKS
# ============================================================

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


# ============================================================
# ADD TASK
# ============================================================

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


# ============================================================
# COMPLETE TASK
# ============================================================

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
        (
            task_id,
            session["user_id"]
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("main.tasks"))


# ============================================================
# DELETE TASK
# ============================================================

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
        (
            task_id,
            session["user_id"]
        )
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("main.tasks"))


# ============================================================
# QUIZ PAGE
# ============================================================

@main.route("/quiz")
def quiz():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    return render_template("quiz.html")


# ============================================================
# GENERATE QUIZ
# ============================================================

@main.route("/quiz/generate", methods=["POST"])
def generate_quiz_route():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    topic = request.form.get("topic", "").strip()

    try:
        num_questions = int(request.form.get("num_questions", 5))
    except ValueError:
        num_questions = 5

    # Basic validation
    if not topic:
        return "Please enter a quiz topic."

    if num_questions < 1:
        num_questions = 1

    if num_questions > 20:
        num_questions = 20

    try:

        # Ask AI to generate the quiz
        quiz_data = generate_quiz(
            topic,
            num_questions
        )

        questions = quiz_data["questions"]

        if not questions:
            return "AI did not generate any questions."

        # ----------------------------------------------------
        # Save quiz in database
        # ----------------------------------------------------

        connection = get_db_connection()
        cursor = connection.cursor()

        quiz_query = """
            INSERT INTO quizzes
            (user_id, topic, total_questions)
            VALUES (%s, %s, %s)
        """

        cursor.execute(
            quiz_query,
            (
                session["user_id"],
                topic,
                len(questions)
            )
        )

        quiz_id = cursor.lastrowid

        # ----------------------------------------------------
        # Save questions
        # ----------------------------------------------------

        question_query = """
            INSERT INTO quiz_questions
            (
                quiz_id,
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_answer
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        for question in questions:

            cursor.execute(
                question_query,
                (
                    quiz_id,
                    question["question"],
                    question["option_a"],
                    question["option_b"],
                    question["option_c"],
                    question["option_d"],
                    question["correct_answer"]
                )
            )

        connection.commit()

        cursor.close()
        connection.close()

        # ----------------------------------------------------
        # Get questions again with database IDs
        # ----------------------------------------------------

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM quiz_questions
            WHERE quiz_id = %s
            ORDER BY id ASC
            """,
            (quiz_id,)
        )

        saved_questions = cursor.fetchall()

        cursor.close()
        connection.close()

        # Save current quiz ID in session as a backup
        session["current_quiz_id"] = quiz_id

        # Show quiz questions
        return render_template(
            "quiz_result.html",
            topic=topic,
            quiz_id=quiz_id,
            questions=saved_questions
        )

    except Exception as e:

        return f"AI Quiz Generation Error: {str(e)}"


# ============================================================
# SUBMIT QUIZ
# ============================================================

@main.route("/quiz/submit", methods=["POST"])
def submit_quiz():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    # Get quiz ID from the form
    quiz_id = request.form.get("quiz_id")

    # Backup: use session quiz ID if form does not contain it
    if not quiz_id:
        quiz_id = session.get("current_quiz_id")

    if not quiz_id:
        return "Quiz ID is missing. Please generate a new quiz and try again."

    # Make sure quiz ID is an integer
    try:
        quiz_id = int(quiz_id)
    except ValueError:
        return "Invalid Quiz ID."

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # ----------------------------------------------------
        # Make sure this quiz belongs to the logged-in user
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM quizzes
            WHERE id = %s AND user_id = %s
            """,
            (
                quiz_id,
                session["user_id"]
            )
        )

        quiz = cursor.fetchone()

        if not quiz:
            return "Quiz not found."

        # ----------------------------------------------------
        # Get questions
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM quiz_questions
            WHERE quiz_id = %s
            ORDER BY id ASC
            """,
            (quiz_id,)
        )

        questions = cursor.fetchall()

        if not questions:
            return "No questions found for this quiz."

        # ----------------------------------------------------
        # Calculate score
        # ----------------------------------------------------

        score = 0

        for question in questions:

            field_name = f"question_{question['id']}"

            selected_answer = request.form.get(field_name)

            # Check answer
            if selected_answer == question["correct_answer"]:
                score += 1

            # Save student's answer
            cursor.execute(
                """
                INSERT INTO quiz_answers
                (quiz_id, question_id, selected_answer)
                VALUES (%s, %s, %s)
                """,
                (
                    quiz_id,
                    question["id"],
                    selected_answer
                )
            )

        # ----------------------------------------------------
        # Save final score
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE quizzes
            SET score = %s
            WHERE id = %s AND user_id = %s
            """,
            (
                score,
                quiz_id,
                session["user_id"]
            )
        )

        connection.commit()

        # Quiz has been completed
        session.pop("current_quiz_id", None)

        # ----------------------------------------------------
        # Show result
        # ----------------------------------------------------

        return render_template(
            "quiz_score.html",
            topic=quiz["topic"],
            score=score,
            total=len(questions)
        )

    except Exception as e:

        connection.rollback()

        return f"Quiz Submission Error: {str(e)}"

    finally:

        cursor.close()
        connection.close()


# ============================================================
# LOGOUT
# ============================================================

@main.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("main.login"))