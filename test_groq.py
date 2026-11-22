
from app import app
from groq_service import generate_mcq_questions

with app.app_context():

    try:
        print("Connecting to Groq AI...")

        result = generate_mcq_questions(
            subject="Aptitude",
            topic="Percentages",
            difficulty="Easy",
            number=2
        )

        print("\nGroq API Connected Successfully!")
        print("\nGenerated Questions:\n")

        for i, question in enumerate(result["questions"], 1):
            print(f"Question {i}: {question['question']}")

            for option, value in question["options"].items():
                print(f"{option}. {value}")

            print("Correct Answer:", question["correct_answer"])
            print("Explanation:", question["explanation"])
            print("-" * 50)

    except Exception as e:
        print("Groq API Error:", str(e))
