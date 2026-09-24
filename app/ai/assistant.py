import os

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def ask_ai(question, student_context=None):

    if student_context:
        context_text = f"""
Student information:
- College: {student_context.get("college", "Not provided")}
- Course: {student_context.get("course", "Not provided")}
- Branch: {student_context.get("branch", "Not provided")}
- Semester: {student_context.get("semester", "Not provided")}
"""
    else:
        context_text = ""

    prompt = f"""
You are StudyGenie, an AI academic assistant for college students.

Your job is to help students understand academic concepts,
programming topics, assignments, exam preparation, and study planning.

{context_text}

Student's question:
{question}

Instructions:
- Give a clear and accurate answer.
- Explain difficult concepts in simple language.
- Use examples when useful.
- For programming questions, provide simple examples when appropriate.
- If the student asks for a study plan, create a practical plan.
- Keep the response focused on the student's question.
- Do not pretend to know information that was not provided.
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

    return response.choices[0].message.content