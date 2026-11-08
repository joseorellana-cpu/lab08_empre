from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from quiz.models import Choice, Exam, Question


class Command(BaseCommand):
    help = "Create a demo user and demo exams (enough questions to get more than one page)."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")
        parser.add_argument("--password", default="demo12345")

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username=options["username"])
        if created:
            user.set_password(options["password"])
            user.save()

        if Exam.objects.exists():
            self.stdout.write("Demo data already present, nothing to do.")
            return

        python_exam = Exam.objects.create(title="Python basics", description="Introductory quiz")
        django_exam = Exam.objects.create(title="Django basics", description="Models, views, URLs")

        samples = [
            (python_exam, "Which keyword defines a function in Python?", ["def", "func", "lambda only", "fn"]),
            (python_exam, "What does len([1, 2, 3]) return?", ["3", "2", "4", "Error"]),
            (python_exam, "Which type is immutable?", ["tuple", "list", "dict", "set"]),
            (django_exam, "Which command applies migrations?", ["migrate", "makemigrations", "runserver", "shell"]),
            (django_exam, "Which file holds the URL routes?", ["urls.py", "models.py", "admin.py", "apps.py"]),
            (django_exam, "Which class turns a model into JSON in DRF?", ["ModelSerializer", "ModelForm", "View", "Router"]),
            (django_exam, "Which router class creates the API root view?", ["DefaultRouter", "SimpleView", "UrlMap", "Root"]),
        ]
        for exam, text, options_list in samples:
            question = Question.objects.create(exam=exam, text=text)
            for index, option in enumerate(options_list):
                Choice.objects.create(question=question, text=option, is_correct=(index == 0))

        self.stdout.write(self.style.SUCCESS(
            f"Seeded 2 exams and {len(samples)} questions. User: {options['username']}"
        ))
