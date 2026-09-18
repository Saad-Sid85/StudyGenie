import os
import json

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
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

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )

    result = response.output_text

    return json.loads(result)