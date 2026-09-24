import os
import json

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def generate_automation_alerts(student, tasks, quizzes):

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
You are StudyGenie's smart automation engine.

Your job is to analyze a college student's tasks and quiz
performance and generate useful academic alerts.

Student information:
{json.dumps(student_info, indent=2)}

Pending tasks:
{json.dumps(task_data, indent=2)}

Quiz history:
{json.dumps(quiz_data, indent=2)}

Generate practical alerts for the student.

Consider:

1. Tasks with approaching deadlines
2. High-priority pending tasks
3. Multiple pending tasks
4. Weak quiz performance
5. Topics that need revision
6. Good quiz performance
7. General study recommendations

Return ONLY valid JSON.

Use exactly this format:

{{
    "alerts": [
        {{
            "type": "deadline",
            "level": "high",
            "title": "Deadline Alert",
            "message": "Your DBMS assignment is due soon."
        }},
        {{
            "type": "performance",
            "level": "medium",
            "title": "Performance Alert",
            "message": "You should revise Data Structures."
        }}
    ]
}}

Rules:

- Base alerts only on the provided data.
- Never invent tasks or quiz scores.
- Do not create an alert if there is no supporting data.
- Keep messages short and useful.
- Use these levels only:
  high
  medium
  low

- Use these types when appropriate:
  deadline
  priority
  performance
  progress
  study

- If there is not enough data for a particular alert,
  simply do not create that alert.
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