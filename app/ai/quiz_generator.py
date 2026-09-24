import os
import json

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


def generate_quiz(topic, number_of_questions):

    prompt = f"""
You are an academic quiz generator for college students.

Create exactly {number_of_questions} multiple-choice questions
about the topic: {topic}

Each question must have:
- A clear question
- Four options
- One correct answer

Return ONLY valid JSON.

Use exactly this format:

{{
    "questions": [
        {{
            "question": "Question text",
            "option_a": "Option A",
            "option_b": "Option B",
            "option_c": "Option C",
            "option_d": "Option D",
            "correct_answer": "A"
        }}
    ]
}}

Do not add markdown.
Do not add explanations outside the JSON.
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