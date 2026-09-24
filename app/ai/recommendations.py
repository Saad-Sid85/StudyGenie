import os
import json

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def generate_recommendations(student, tasks, quizzes):

    student_info = {
        "college": student.get("college"),
        "course": student.get("course"),
        "branch": student.get("branch"),
        "semester": student.get("semester")
    }

    task_data = []

    for task in tasks:
        task_data.append({
            "title": task["title"],
            "description": task["description"],
            "subject": task["subject"],
            "due_date": str(task["due_date"]),
            "priority": task["priority"],
            "status": task["status"]
        })

    quiz_data = []

    for quiz in quizzes:
        quiz_data.append({
            "topic": quiz["topic"],
            "score": quiz["score"],
            "total_questions": quiz["total_questions"],
            "created_at": str(quiz["created_at"])
        })

    prompt = f"""
You are StudyGenie, an AI study planning assistant.

Analyze the student's academic information, tasks and quiz performance.

Student information:
{json.dumps(student_info, indent=2)}

Student tasks:
{json.dumps(task_data, indent=2)}

Student quiz history:
{json.dumps(quiz_data, indent=2)}

Create practical and personalized study recommendations.

Consider:
1. Upcoming deadlines
2. High-priority pending tasks
3. Subjects/topics where quiz performance is relatively weak
4. Topics where the student is performing well
5. What the student should study first
6. A practical study plan for the next few days

Return ONLY valid JSON using exactly this format:

{{
    "summary": "Short summary of the student's current academic situation.",
    "priorities": [
        "Priority recommendation 1",
        "Priority recommendation 2",
        "Priority recommendation 3"
    ],
    "weak_topics": [
        "Topic or subject that needs more attention"
    ],
    "strong_topics": [
        "Topic or subject where the student is doing well"
    ],
    "study_plan": [
        "Day 1: ...",
        "Day 2: ...",
        "Day 3: ..."
    ]
}}

Rules:
- Base recommendations only on the provided student data.
- Do not invent assignments, quiz scores or deadlines.
- If there is not enough quiz data, say so.
- If there are no tasks, say so.
- Keep recommendations practical for a college student.
"""

    response = client.chat.completions.create(
        model="gemini-3.6-flash",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = response.choices[0].message.content

    return json.loads(result)