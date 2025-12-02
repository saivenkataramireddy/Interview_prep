from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe

from .models import Topic, Question, UserQuestionAttempt, TopicContent, TestScore
from .forms import SignupForm
import json
import random

# map categories -> topics
CATEGORIES_TOPICS = {
    "Frontend": ["HTML", "CSS", "JS", "React"],
    "Backend": ["Python", "Django", "Node.js"],
    "Database": ["SQL", "MongoDB"],
    "Aptitude": ["Logical", "Problem Solving", "Quantitative"],
    "HR": ["All"],
    "System Design": ["Basics", "Database Design"],
}

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'tracker/signup.html', {'form': form})


@login_required
def dashboard_view(request):
    # Total topics from static mappings
    total_topics = sum(len(topics) for topics in CATEGORIES_TOPICS.values())

    # Completed topics for this user only
    completed_count = TestScore.objects.filter(user=request.user, completed=True).count()

    pending_count = total_topics - completed_count
    progress = int((completed_count / total_topics) * 100) if total_topics > 0 else 0

    return render(request, 'tracker/dashboard.html', {
        "total": total_topics,
        "done": completed_count,
        "pending": pending_count,
        "progress": progress,
    })



@login_required
def add_topic(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category', '')
        if name:
            Topic.objects.create(
                user=request.user,
                name=name,
                category=category,
                status='pending'
            )
    return redirect('dashboard')


@login_required
def toggle_status(request, id):
    topic = get_object_or_404(Topic, id=id, user=request.user)
    topic.status = 'pending' if topic.status == 'done' else 'done'
    topic.save()
    return redirect('dashboard')


@login_required
def delete_topic(request, id):
    topic = get_object_or_404(Topic, id=id, user=request.user)
    topic.delete()
    return redirect('dashboard')

#

@login_required
def practice_view(request):
    categories = list(CATEGORIES_TOPICS.keys())
    topics_by_category = CATEGORIES_TOPICS

    selected_category = request.session.get("selected_category")
    selected_topic = request.session.get("selected_topic")
    question_ids = request.session.get("question_ids", [])
    current_index = request.session.get("current_index", 0)
    score = request.session.get("score", 0)

    # Validate session questions (DB updated → remove stale IDs)
    if question_ids:
        valid_qs = Question.objects.filter(id__in=question_ids).count()
        if valid_qs != len(question_ids):
            for key in ["selected_category", "selected_topic", "question_ids", "current_index", "score"]:
                request.session.pop(key, None)
            question_ids = []
            selected_category = None
            selected_topic = None

    if request.method == "POST":
        mode = request.POST.get("mode")

        # Step 1 → Start Test
        if mode == "start_test":
            for key in ["selected_category", "selected_topic", "question_ids", "current_index", "score"]:
                request.session.pop(key, None)

            selected_category = request.POST.get("category")
            selected_topic = request.POST.get("topic")

            questions = list(Question.objects.filter(
                category=selected_category,
                topic=selected_topic
            ).order_by("?")[:10])

            if not questions:
                return render(request, "tracker/practice.html", {
                    "categories": categories,
                    "topics_by_category": json.dumps(topics_by_category),
                    "error": "⚠ No questions available for this topic!"
                })

            request.session["selected_category"] = selected_category
            request.session["selected_topic"] = selected_topic
            request.session["question_ids"] = [q.id for q in questions]
            request.session["current_index"] = 0
            request.session["score"] = 0

            return redirect("practice")

        # Step 2 → Next Question
        elif mode == "next_question":
            qid = question_ids[current_index]
            user_answer = request.POST.get("answer", "").strip()
            q = Question.objects.get(id=qid)

            if user_answer.upper() == q.correct_answer.upper():
                request.session["score"] = score + 1

            request.session["current_index"] = current_index + 1
            return redirect("practice")

        # Step 3 → Submit Test
        elif mode == "submit_test":
            total = len(question_ids)
            percentage = (score / total) * 100 if total > 0 else 0

            # Validation rule → Need 90% to pass
            test_completed = True if percentage >= 90 else False

            TestScore.objects.update_or_create(
                user=request.user,
                topic=selected_topic,
                defaults={"score": percentage, "completed": test_completed}
            )

            # Clear session
            for key in ["selected_category", "selected_topic", "question_ids", "current_index", "score"]:
                request.session.pop(key, None)

            message = (
                "🎉 Congratulations! You passed successfully!"
                if test_completed else
                "⚠ You scored below 90%. Prepare well and retake the test."
            )

            # Result Page Render
            return render(request, "tracker/test_result.html", {
                "topic": selected_topic,
                "score": round(percentage, 2),
                "passed": test_completed,
                "message": message,
            })

    # Display Question
    if question_ids and current_index < len(question_ids):
        q = Question.objects.get(id=question_ids[current_index])
        options = {
            "A": q.option_a,
            "B": q.option_b,
            "C": q.option_c,
            "D": q.option_d,
        }
    else:
        q = None
        options = None

    return render(request, "tracker/practice.html", {
        "categories": categories,
        "topics_by_category": json.dumps(topics_by_category),
        "selected_category": selected_category,
        "selected_topic": selected_topic,
        "question": q,
        "index": current_index + 1 if q else 0,
        "total": len(question_ids),
        "options": options,
        "score": score,
    })



@login_required
def learn_topic_view(request, topic):
    content = TopicContent.objects.filter(topic=topic).first()
    questions_count = Question.objects.filter(topic=topic).count()

    return render(request, "tracker/learn_topic.html", {
        "topic": topic,
        "content": content,
        "questions_count": questions_count
    })

@login_required
def take_test_view(request, topic):
    # Load the same question set using session
    if 'test_questions' not in request.session:
        questions = list(Question.objects.filter(topic=topic).order_by('?')[:10])
        request.session['test_questions'] = [q.id for q in questions]
        request.session['current_index'] = 0
        request.session['score'] = 0
    else:
        questions = [Question.objects.get(id=qid) for qid in request.session['test_questions']]

    current_index = request.session['current_index']
    total = len(questions)

    # Submit logic
    if request.method == "POST":
        user_answer = request.POST.get("answer", "")

        current_question = questions[current_index]
        if user_answer.upper() == current_question.correct_answer.upper():
            request.session['score'] += 1

        current_index += 1
        request.session['current_index'] = current_index

        if current_index >= total:
            score = request.session['score']
            percentage = (score / total) * 100

            # Save to DB
            TestScore.objects.update_or_create(
                user=request.user,
                topic=topic,
                defaults={"score": percentage, "completed": True}
            )

            # Clear session test data
            del request.session['test_questions']
            del request.session['current_index']
            del request.session['score']

            return render(request, "tracker/test_submitted.html", {
                "topic": topic,
                "score": percentage,
                "message": "Test Submitted Successfully! 🎯"
            })

    return render(request, "tracker/test_page.html", {
        "topic": topic,
        "question": questions[current_index],
        "index": current_index + 1,
        "total": total
    })

@login_required
def progress_analytics_view(request):
    topics_data = CATEGORIES_TOPICS
    analytics = []
    total_completed = 0
    total_pending = 0

    weak_topic = None
    lowest_percent = 101  # start higher than 100

    for category, topics in topics_data.items():
        completed = TestScore.objects.filter(
            user=request.user,
            topic__in=topics,
            completed=True
        ).count()

        total_topics = len(topics)
        pending = total_topics - completed

        total_completed += completed
        total_pending += pending

        percent = round((completed / total_topics) * 100, 1) if total_topics > 0 else 0

        analytics.append({
            "category": category,
            "completed": completed,
            "pending": pending,
            "total": total_topics,
            "percent": percent
        })

        # Track weakest category
        if percent < lowest_percent:
            lowest_percent = percent
            weak_topic = category

    return render(request, "tracker/progress_analytics.html", {
        "analytics": analytics,
        "total_completed": total_completed,
        "total_pending": total_pending,
        "weak_topic": weak_topic,
    })
