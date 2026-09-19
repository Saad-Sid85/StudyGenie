import os

from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def ask_about_notes(question, note_content):

    prompt = f"""
You are StudyGenie, an AI academic assistant.

The student has provided study notes below.

Your task is to answer the student's question
using the provided notes as the primary source.

STUDY NOTES:
--------------------
{note_content}
--------------------

STUDENT QUESTION:
{question}

Instructions:

- Answer using the provided study notes.
- Explain concepts clearly and simply.
- Preserve important terminology from the notes.
- Use examples from the notes when useful.
- If the answer cannot be found or reasonably derived
  from the notes, clearly say that the information
  is not available in the uploaded notes.
- Do not pretend that information exists in the notes
  when it does not.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )

    return response.output_text