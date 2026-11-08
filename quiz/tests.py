from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Choice, Exam, Question


def build_question_payload(exam_id, correct_count=1):
    choices = [{"text": f"Option {i}", "is_correct": i < correct_count} for i in range(4)]
    return {"exam": exam_id, "text": "Sample question?", "points": 1, "choices": choices}


class QuizApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("tester", password="pass12345")
        self.exam = Exam.objects.create(title="Exam A")
        self.other_exam = Exam.objects.create(title="Exam B")
        question = Question.objects.create(exam=self.exam, text="Existing question about Python")
        Choice.objects.create(question=question, text="Yes", is_correct=True)
        Choice.objects.create(question=question, text="No", is_correct=False)
        self.question = question

    def login(self):
        self.client.force_authenticate(self.user)

    # --- the five operations -------------------------------------------------
    def test_list_is_public_and_paginated(self):
        response = self.client.get("/api/exams/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_question_has_nested_choices_and_exam_id(self):
        response = self.client.get(f"/api/questions/{self.question.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["exam"], self.exam.id)
        self.assertEqual(len(response.data["choices"]), 2)

    def test_create_question_with_nested_choices(self):
        self.login()
        response = self.client.post("/api/questions/", build_question_payload(self.exam.id), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.get(pk=response.data["id"]).choices.count(), 4)

    def test_partial_update(self):
        self.login()
        response = self.client.patch(f"/api/questions/{self.question.id}/", {"points": 5}, format="json")
        self.assertEqual(response.status_code, 200)
        self.question.refresh_from_db()
        self.assertEqual(self.question.points, 5)

    def test_delete(self):
        self.login()
        response = self.client.delete(f"/api/exams/{self.other_exam.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Exam.objects.filter(pk=self.other_exam.id).exists())

    # --- the three provoked errors ------------------------------------------
    def test_missing_required_field_returns_400(self):
        self.login()
        response = self.client.post("/api/exams/", {"description": "no title"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.data)

    def test_wrong_type_returns_400(self):
        self.login()
        payload = build_question_payload(self.exam.id)
        payload["points"] = "many"
        response = self.client.post("/api/questions/", payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("points", response.data)

    def test_zero_correct_choices_returns_400(self):
        self.login()
        response = self.client.post("/api/questions/", build_question_payload(self.exam.id, 0), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("choices", response.data)

    def test_two_correct_choices_returns_400(self):
        self.login()
        response = self.client.post("/api/questions/", build_question_payload(self.exam.id, 2), format="json")
        self.assertEqual(response.status_code, 400)

    # --- permissions and 404 ------------------------------------------------
    def test_write_without_login_is_rejected(self):
        response = self.client.post("/api/exams/", {"title": "x"}, format="json")
        self.assertIn(response.status_code, (401, 403))

    def test_missing_resource_returns_404(self):
        self.assertEqual(self.client.get("/api/exams/9999/").status_code, 404)

    # --- filtering, search, pagination --------------------------------------
    def test_filter_questions_by_exam(self):
        Question.objects.create(exam=self.other_exam, text="Other exam question")
        response = self.client.get(f"/api/questions/?exam={self.exam.id}")
        self.assertEqual(response.data["count"], 1)

    def test_search_by_question_text(self):
        Question.objects.create(exam=self.other_exam, text="Something about Django")
        response = self.client.get("/api/questions/?search=django")
        self.assertEqual(response.data["count"], 1)

    def test_pagination_second_page(self):
        for i in range(7):
            Question.objects.create(exam=self.exam, text=f"Bulk question {i}")
        first = self.client.get("/api/questions/")
        second = self.client.get("/api/questions/?page=2")
        self.assertEqual(len(first.data["results"]), 5)
        self.assertEqual(len(second.data["results"]), 3)
        self.assertIsNotNone(first.data["next"])
