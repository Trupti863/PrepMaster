
import json
from groq import Groq
from flask import current_app


def generate_mcq_questions(subject, topic, difficulty, number):

    # Get the Groq API key from config.py
    api_key = current_app.config.get("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Groq API key is missing.")

    # Connect to Groq
    client = Groq(api_key=api_key)

    # Prompt for generating MCQ questions
    prompt = f"""
    Generate exactly {number} multiple-choice questions.

    Subject: {subject}
    Topic: {topic}
    Difficulty: {difficulty}

    Requirements:
    1. Generate exactly {number} questions.
    2. Each question must have four options.
    3. Option keys must be A, B, C, and D.
    4. Only one option must be correct.
    5. Include the correct answer key.
    6. Include a short explanation.
    7. Questions must be accurate and educational.

    Return the response in this JSON format:

    {{
        "questions": [
            {{
                "question": "Question text",
                "options": {{
                    "A": "Option one",
                    "B": "Option two",
                    "C": "Option three",
                    "D": "Option four"
                }},
                "correct_answer": "A",
                "explanation": "Explanation of the answer"
            }}
        ]
    }}

    Return only valid JSON.
    """

    # Send request to Groq API
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.7
    )

    # Convert JSON response into Python dictionary
    result = json.loads(
        response.choices[0].message.content
    )

    # Return generated questions
    return result.get("questions", [])
