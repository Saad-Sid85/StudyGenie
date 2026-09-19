from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session
)

import os
import bcrypt
import mysql.connector

from pypdf import PdfReader

from app.ai.quiz_generator import generate_quiz
from app.ai.assistant import ask_ai
from app.ai.recommendations import generate_recommendations
from app.ai.notes_ai import ask_about_notes
from app.ai.pdf_extractor import extract_text_from_pdf
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

    try:

        # ----------------------------------------------------
        # Student profile
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT name, email, college, course, branch, semester
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        # ----------------------------------------------------
        # Pending task count
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM tasks
            WHERE user_id = %s
              AND status = 'Pending'
            """,
            (session["user_id"],)
        )

        pending_tasks = cursor.fetchone()["count"]

        # ----------------------------------------------------
        # Upcoming tasks
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                title,
                subject,
                due_date,
                priority,
                status
            FROM tasks
            WHERE user_id = %s
              AND status = 'Pending'
            ORDER BY due_date ASC
            LIMIT 5
            """,
            (session["user_id"],)
        )

        upcoming_tasks = cursor.fetchall()

        # ----------------------------------------------------
        # Upcoming deadline count
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM tasks
            WHERE user_id = %s
              AND status = 'Pending'
              AND due_date >= CURDATE()
              AND due_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
            """,
            (session["user_id"],)
        )

        upcoming_deadlines = cursor.fetchone()["count"]

        # ----------------------------------------------------
        # Total quizzes taken
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM quizzes
            WHERE user_id = %s
              AND score IS NOT NULL
            """,
            (session["user_id"],)
        )

        quizzes_taken = cursor.fetchone()["count"]

        # ----------------------------------------------------
        # Average quiz score
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(
                    ROUND(
                        AVG(
                            CASE
                                WHEN total_questions > 0
                                THEN (score / total_questions) * 100
                            END
                        ),
                        1
                    ),
                    0
                ) AS average_score
            FROM quizzes
            WHERE user_id = %s
              AND score IS NOT NULL
            """,
            (session["user_id"],)
        )

        average_score = cursor.fetchone()["average_score"]

        # ----------------------------------------------------
        # Recent quiz performance
        # ----------------------------------------------------
        cursor.execute(
            """
            SELECT
                id,
                topic,
                score,
                total_questions,
                created_at
            FROM quizzes
            WHERE user_id = %s
              AND score IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (session["user_id"],)
        )

        recent_quizzes = cursor.fetchall()
        
        # ----------------------------------------------------
        # Generate AI recommendation preview
        # ----------------------------------------------------

        try:

            recommendation_data = generate_recommendations(
                user,
                upcoming_tasks,
                recent_quizzes
            )

            recommendation_preview = recommendation_data.get(
                "summary",
                "Keep working consistently and stay on top of your upcoming tasks."
            )

            recommendation_priorities = recommendation_data.get(
                "priorities",
                []
            )

        except Exception:

            recommendation_preview = (
                "Complete your pending tasks and review your recent quiz performance."
            )

            recommendation_priorities = []


        # ----------------------------------------------------
        # Generate Smart Automation Alerts
        # ----------------------------------------------------

        try:

            from app.ai.automation import generate_automation_alerts

            automation_data = generate_automation_alerts(
                user,
                upcoming_tasks,
                recent_quizzes
            )

            dashboard_alerts = automation_data.get(
                "alerts",
                []
            )

        except Exception:

            dashboard_alerts = []

        return render_template(
            "dashboard.html",
            user=user,
            pending_tasks=pending_tasks,
            upcoming_tasks=upcoming_tasks,
            upcoming_deadlines=upcoming_deadlines,
            quizzes_taken=quizzes_taken,
            average_score=average_score,
            recent_quizzes=recent_quizzes,
            recommendation_preview=recommendation_preview,
            recommendation_priorities=recommendation_priorities,
            dashboard_alerts=dashboard_alerts
        )

    finally:
        cursor.close()
        connection.close()


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
# DELETE QUIZ
# ============================================================

@main.route("/quiz/delete/<int:quiz_id>")
def delete_quiz(quiz_id):

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM quizzes
            WHERE id = %s
              AND user_id = %s
            """,
            (
                quiz_id,
                session["user_id"]
            )
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("main.dashboard"))


# ============================================================
# LOGOUT
# ============================================================

@main.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("main.login"))

# ============================================================
# AI ASSISTANT
# ============================================================

@main.route("/assistant", methods=["GET", "POST"])
def assistant():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    answer = None
    question = ""

    # --------------------------------------------------------
    # Ask AI
    # --------------------------------------------------------

    if request.method == "POST":

        question = request.form.get("question", "").strip()

        if not question:
            return render_template(
                "assistant.html",
                answer=None,
                question="",
                error="Please enter a question."
            )

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT college, course, branch, semester
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        student = cursor.fetchone()

        cursor.close()
        connection.close()

        try:

            answer = ask_ai(
                question,
                student
            )

        except Exception as e:

            return render_template(
                "assistant.html",
                answer=None,
                question=question,
                error=f"AI Assistant Error: {str(e)}"
            )

    return render_template(
        "assistant.html",
        answer=answer,
        question=question,
        error=None
    )

# ============================================================
# AI STUDY RECOMMENDATIONS
# ============================================================

@main.route("/recommendations")
def recommendations():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # ----------------------------------------------------
        # Get student information
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT college, course, branch, semester
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        student = cursor.fetchone()

        if not student:
            return "Student information not found."

        # ----------------------------------------------------
        # Get pending tasks
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                title,
                description,
                subject,
                due_date,
                priority,
                status
            FROM tasks
            WHERE user_id = %s
              AND status = 'Pending'
            ORDER BY due_date ASC
            """,
            (session["user_id"],)
        )

        tasks = cursor.fetchall()

        # ----------------------------------------------------
        # Get quiz history
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                topic,
                score,
                total_questions,
                created_at
            FROM quizzes
            WHERE user_id = %s
              AND score IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (session["user_id"],)
        )

        quizzes = cursor.fetchall()

    finally:

        cursor.close()
        connection.close()

    # --------------------------------------------------------
    # Generate AI recommendations
    # --------------------------------------------------------

    try:

        recommendations_data = generate_recommendations(
            student,
            tasks,
            quizzes
        )

        return render_template(
            "recommendations.html",
            recommendations=recommendations_data
        )

    except Exception as e:

        return f"AI Recommendation Error: {str(e)}"

    # ============================================================
# STUDY NOTES
# ============================================================

@main.route("/notes")
def notes():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                id,
                title,
                filename,
                created_at
            FROM notes
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        )

        notes_list = cursor.fetchall()

    finally:

        cursor.close()
        connection.close()

    return render_template(
        "notes.html",
        notes=notes_list
    )


@main.route("/notes/upload", methods=["GET", "POST"])
def upload_note():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        pdf_file = request.files.get("pdf_file")

        if not title:
            return render_template(
                "upload_note.html",
                error="Please enter a note title."
            )

        if not pdf_file or pdf_file.filename == "":
            return render_template(
                "upload_note.html",
                error="Please select a PDF file."
            )

        if not pdf_file.filename.lower().endswith(".pdf"):
            return render_template(
                "upload_note.html",
                error="Only PDF files are supported."
            )

        try:
            extracted_text = extract_text_from_pdf(pdf_file)

            if not extracted_text:
                return render_template(
                    "upload_note.html",
                    error="Could not extract text from this PDF, even with OCR."
                )

            connection = get_db_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO notes
                (
                    user_id,
                    title,
                    filename,
                    content
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    session["user_id"],
                    title,
                    pdf_file.filename,
                    extracted_text
                )
            )

            connection.commit()

            cursor.close()
            connection.close()

            return redirect(url_for("main.notes"))

        except Exception as e:

            return render_template(
                "upload_note.html",
                error=f"PDF Upload Error: {str(e)}"
            )

    return render_template(
        "upload_note.html",
        error=None
    )


@main.route("/notes/<int:note_id>")
def view_note(note_id):

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                id,
                title,
                filename,
                content,
                created_at
            FROM notes
            WHERE id = %s
              AND user_id = %s
            """,
            (
                note_id,
                session["user_id"]
            )
        )

        note = cursor.fetchone()

    finally:

        cursor.close()
        connection.close()

    if not note:
        return "Note not found."

    return render_template(
        "view_note.html",
        note=note,
        answer=None,
        question=""
    )


# ============================================================
# DELETE STUDY NOTE
# ============================================================

@main.route("/notes/delete/<int:note_id>")
def delete_note(note_id):

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM notes
            WHERE id = %s
              AND user_id = %s
            """,
            (
                note_id,
                session["user_id"]
            )
        )

        connection.commit()

    finally:

        cursor.close()
        connection.close()

    return redirect(url_for("main.notes"))

@main.route(
    "/notes/<int:note_id>/ask",
    methods=["POST"]
)
def ask_note_question(note_id):

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    question = request.form.get(
        "question",
        ""
    ).strip()

    if not question:
        return "Please enter a question."

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                id,
                title,
                filename,
                content,
                created_at
            FROM notes
            WHERE id = %s
              AND user_id = %s
            """,
            (
                note_id,
                session["user_id"]
            )
        )

        note = cursor.fetchone()

    finally:

        cursor.close()
        connection.close()

    if not note:
        return "Note not found."

    try:

        answer = ask_about_notes(
            question,
            note["content"]
        )

    except Exception as e:

        return render_template(
            "view_note.html",
            note=note,
            answer=None,
            question=question,
            error=f"AI Notes Error: {str(e)}"
        )

    return render_template(
        "view_note.html",
        note=note,
        answer=answer,
        question=question,
        error=None
    )
    
    # ============================================================
# SMART AUTOMATION & ALERTS
# ============================================================

@main.route("/automation")
def automation():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # ----------------------------------------------------
        # Get student information
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                college,
                course,
                branch,
                semester
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        student = cursor.fetchone()

        if not student:
            return "Student information not found."

        # ----------------------------------------------------
        # Get pending tasks
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                title,
                description,
                subject,
                due_date,
                priority,
                status
            FROM tasks
            WHERE user_id = %s
              AND status = 'Pending'
            ORDER BY due_date ASC
            """,
            (session["user_id"],)
        )

        tasks = cursor.fetchall()

        # ----------------------------------------------------
        # Get quiz history
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                topic,
                score,
                total_questions,
                created_at
            FROM quizzes
            WHERE user_id = %s
              AND score IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (session["user_id"],)
        )

        quizzes = cursor.fetchall()

    finally:

        cursor.close()
        connection.close()

    # --------------------------------------------------------
    # Generate smart alerts using AI
    # --------------------------------------------------------

    try:

        from app.ai.automation import generate_automation_alerts

        automation_data = generate_automation_alerts(
            student,
            tasks,
            quizzes
        )

        alerts = automation_data.get(
            "alerts",
            []
        )

    except Exception as e:

        return f"Automation Error: {str(e)}"

    return render_template(
        "automation.html",
        alerts=alerts
    )
    
    
    # ============================================================
# STUDENT PROGRESS ANALYTICS
# ============================================================

@main.route("/progress")
def progress():

    if "user_id" not in session:
        return redirect(url_for("main.login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        # ----------------------------------------------------
        # Task statistics
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS total_tasks
            FROM tasks
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        total_tasks = cursor.fetchone()["total_tasks"]

        cursor.execute(
            """
            SELECT COUNT(*) AS completed_tasks
            FROM tasks
            WHERE user_id = %s
              AND status = 'Completed'
            """,
            (session["user_id"],)
        )

        completed_tasks = cursor.fetchone()["completed_tasks"]

        cursor.execute(
            """
            SELECT COUNT(*) AS pending_tasks
            FROM tasks
            WHERE user_id = %s
              AND status = 'Pending'
            """,
            (session["user_id"],)
        )

        pending_tasks = cursor.fetchone()["pending_tasks"]


        # ----------------------------------------------------
        # Quiz statistics
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*) AS quizzes_taken
            FROM quizzes
            WHERE user_id = %s
              AND score IS NOT NULL
            """,
            (session["user_id"],)
        )

        quizzes_taken = cursor.fetchone()["quizzes_taken"]


        cursor.execute(
            """
            SELECT
                COALESCE(
                    ROUND(
                        AVG(
                            CASE
                                WHEN total_questions > 0
                                THEN (score / total_questions) * 100
                            END
                        ),
                        1
                    ),
                    0
                ) AS average_score
            FROM quizzes
            WHERE user_id = %s
              AND score IS NOT NULL
            """,
            (session["user_id"],)
        )

        average_score = cursor.fetchone()["average_score"]


        # ----------------------------------------------------
        # Topic-wise quiz performance
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                topic,
                COUNT(*) AS attempts,
                ROUND(
                    AVG(
                        CASE
                            WHEN total_questions > 0
                            THEN (score / total_questions) * 100
                        END
                    ),
                    1
                ) AS average_score
            FROM quizzes
            WHERE user_id = %s
              AND score IS NOT NULL
            GROUP BY topic
            ORDER BY average_score DESC
            """,
            (session["user_id"],)
        )

        topic_performance = cursor.fetchall()


        # ----------------------------------------------------
        # Recent quiz performance
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                topic,
                score,
                total_questions,
                created_at
            FROM quizzes
            WHERE user_id = %s
              AND score IS NOT NULL
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (session["user_id"],)
        )

        recent_quizzes = cursor.fetchall()

    finally:

        cursor.close()
        connection.close()


    return render_template(
        "progress.html",
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        quizzes_taken=quizzes_taken,
        average_score=average_score,
        topic_performance=topic_performance,
        recent_quizzes=recent_quizzes
    )