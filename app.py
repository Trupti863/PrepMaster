
from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session
)

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from config import Config
from models import db, User, QuizResult
from groq_service import generate_mcq_questions


# ---------------- APPLICATION CONFIGURATION ----------------

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"


# ---------------- LOAD USER ----------------

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(User, int(user_id))


# ---------------- CREATE DATABASE TABLES ----------------

with app.app_context():

    db.create_all()


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():

    return render_template("home.html")


# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username", "").strip()

        email = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")

        if not username or not email or not password:

            flash("Please fill all fields.", "danger")

            return redirect(url_for("signup"))

        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "danger"
            )

            return redirect(url_for("signup"))

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:

            flash("Email already registered.", "danger")

            return redirect(url_for("signup"))

        new_user = User(
            username=username,
            email=email
        )

        new_user.set_password(password)

        db.session.add(new_user)

        db.session.commit()

        flash("Account created successfully!", "success")

        return redirect(url_for("login"))

    return render_template("accounts/signup.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            login_user(user)

            flash("Login successful!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("accounts/login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():

    return render_template("dashboard/index.html")


# ---------------- GENERATE QUIZ ----------------

@app.route("/generate", methods=["GET", "POST"])
@login_required
def generate_quiz():

    allowed_subjects = [
        "Aptitude",
        "Logical Reasoning",
        "English",
        "Coding"
    ]

    allowed_difficulties = [
        "Easy",
        "Medium",
        "Hard"
    ]

    # GET REQUEST: RECEIVE SUBJECT FROM DASHBOARD

    if request.method == "GET":

        subject = request.args.get("subject", "").strip()

        if subject not in allowed_subjects:

            flash("Please select a valid subject.", "danger")

            return redirect(url_for("dashboard"))

        return render_template(
            "quiz/generate.html",
            subject=subject
        )

    # POST REQUEST: RECEIVE QUIZ DETAILS

    subject = request.form.get("subject", "").strip()

    topic = request.form.get("topic", "").strip()

    difficulty = request.form.get("difficulty", "").strip()

    number = request.form.get("number", "5")

    # VALIDATE SUBJECT

    if subject not in allowed_subjects:

        flash("Please select a valid subject.", "danger")

        return redirect(url_for("dashboard"))

    # VALIDATE DIFFICULTY

    if difficulty not in allowed_difficulties:

        flash("Please select a valid difficulty.", "danger")

        return redirect(
            url_for("generate_quiz", subject=subject)
        )

    # VALIDATE TOPIC

    if not topic or len(topic) > 100:

        flash("Please enter a valid topic.", "danger")

        return redirect(
            url_for("generate_quiz", subject=subject)
        )

    # VALIDATE NUMBER OF QUESTIONS

    try:

        number = int(number)

    except (ValueError, TypeError):

        number = 0

    if number < 1 or number > 10:

        flash(
            "Please select between 1 and 10 questions.",
            "danger"
        )

        return redirect(
            url_for("generate_quiz", subject=subject)
        )

    # GENERATE QUESTIONS USING GROQ AI

    try:

        questions = generate_mcq_questions(
            subject,
            topic,
            difficulty,
            number
        )

        if len(questions) != number:

            raise ValueError(
                "AI did not generate the requested number of questions."
            )

        # VALIDATE GENERATED QUESTIONS

        for question in questions:

            if not isinstance(question, dict):

                raise ValueError("Invalid question format.")

            required_fields = [
                "question",
                "options",
                "correct_answer",
                "explanation"
            ]

            for field in required_fields:

                if field not in question:

                    raise ValueError(
                        f"Missing question field: {field}"
                    )

            if not isinstance(question["options"], dict):

                raise ValueError("Invalid options format.")

            if set(question["options"].keys()) != {
                "A", "B", "C", "D"
            }:

                raise ValueError(
                    "Each question must have four options."
                )

            if question["correct_answer"] not in [
                "A", "B", "C", "D"
            ]:

                raise ValueError("Invalid correct answer.")

        # STORE QUIZ DATA IN SESSION

        session["quiz_questions"] = questions

        session["quiz_subject"] = subject

        session["quiz_topic"] = topic

        session["quiz_difficulty"] = difficulty

        # DISPLAY GENERATED QUESTIONS

        return render_template(
            "quiz/questions.html",
            questions=questions,
            subject=subject,
            topic=topic,
            difficulty=difficulty
        )

    except Exception:

        app.logger.exception("Quiz generation failed")

        flash(
            "Unable to generate quiz. Please try again.",
            "danger"
        )

        return redirect(
            url_for("generate_quiz", subject=subject)
        )


# ---------------- SUBMIT QUIZ ----------------

@app.route("/submit-quiz", methods=["POST"])
@login_required
def submit_quiz():

    questions = session.get("quiz_questions")

    if not questions:

        flash("Please generate a quiz first.", "danger")

        return redirect(url_for("generate_quiz"))

    subject = session.get("quiz_subject", "")

    if not subject:

        flash(
            "Invalid quiz session. Please generate a new quiz.",
            "danger"
        )

        return redirect(url_for("generate_quiz"))

    results = []

    score = 0

    for index, question in enumerate(questions, start=1):

        selected_answer = request.form.get(f"answer_{index}")

        correct_answer = question["correct_answer"]

        is_correct = selected_answer == correct_answer

        if is_correct:

            score += 1

        results.append({

            "question": question["question"],

            "options": question["options"],

            "selected": selected_answer,

            "correct": correct_answer,

            "explanation": question["explanation"],

            "is_correct": is_correct

        })

    total = len(questions)

    topic = session.get("quiz_topic", "")

    difficulty = session.get("quiz_difficulty", "")

    # SAVE QUIZ RESULT IN DATABASE

    quiz_result = QuizResult(

        user_id=current_user.id,

        subject=subject,

        score=score,

        total_questions=total

    )

    try:

        db.session.add(quiz_result)

        db.session.commit()

    except Exception:

        db.session.rollback()

        app.logger.exception("Unable to save quiz result")

        flash(
            "Your quiz result could not be saved. Please try again.",
            "danger"
        )

        return redirect(url_for("dashboard"))

    # CLEAR PREVIOUS QUIZ SESSION

    session.pop("quiz_questions", None)

    session.pop("quiz_subject", None)

    session.pop("quiz_topic", None)

    session.pop("quiz_difficulty", None)

    return render_template(

        "quiz/result.html",

        results=results,

        score=score,

        total=total,

        subject=subject,

        topic=topic,

        difficulty=difficulty

    )


# ---------------- USER PERFORMANCE REPORT ----------------

@app.route("/reports")
@login_required
def reports():

    # GET ONLY THE LOGGED-IN USER'S QUIZ ATTEMPTS

    quiz_history = QuizResult.query.filter_by(
        user_id=current_user.id
    ).order_by(
        QuizResult.id.desc()
    ).all()

    # CALCULATE PERFORMANCE STATISTICS

    total_quizzes = len(quiz_history)

    total_questions = sum(
        result.total_questions for result in quiz_history
    )

    total_correct = sum(
        result.score for result in quiz_history
    )

    total_possible = total_questions

    if total_possible > 0:

        average_percentage = round(
            (total_correct / total_possible) * 100, 2
        )

    else:

        average_percentage = 0

    # CALCULATE HIGHEST PERCENTAGE

    if quiz_history:

        highest_percentage = max(
            (
                result.score / result.total_questions * 100
                if result.total_questions > 0 else 0
            )
            for result in quiz_history
        )

        best_score = max(
            result.score for result in quiz_history
        )

    else:

        highest_percentage = 0

        best_score = 0

    return render_template(

        "dashboard/reports.html",

        quiz_history=quiz_history,

        total_quizzes=total_quizzes,

        total_questions=total_questions,

        total_correct=total_correct,

        average_percentage=average_percentage,

        highest_percentage=round(highest_percentage, 2),

        best_score=best_score

    )


# ---------------- QUIZ HISTORY ----------------

@app.route("/quiz-history")
@login_required
def quiz_history():

    # FETCH ONLY THE CURRENT USER'S PREVIOUS ATTEMPTS

    history = QuizResult.query.filter_by(
        user_id=current_user.id
    ).order_by(
        QuizResult.id.desc()
    ).all()

    return render_template(

        "dashboard/quiz_history.html",

        quiz_history=history

    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out successfully.", "success")

    return redirect(url_for("home"))


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":

    app.run(debug=True)
