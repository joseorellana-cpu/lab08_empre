from rest_framework import filters, viewsets

from .models import Choice, Exam, Question
from .serializers import ExamSerializer, QuestionSerializer, StandaloneChoiceSerializer


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description"]


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["text"]  # ?search=<text of the question>

    def get_queryset(self):
        queryset = Question.objects.select_related("exam").prefetch_related("choices")
        exam_id = self.request.query_params.get("exam")  # ?exam=<exam id>
        if exam_id is not None:
            queryset = queryset.filter(exam_id=exam_id)
        return queryset


class ChoiceViewSet(viewsets.ModelViewSet):
    serializer_class = StandaloneChoiceSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["text"]

    def get_queryset(self):
        queryset = Choice.objects.all()
        question_id = self.request.query_params.get("question")
        if question_id is not None:
            queryset = queryset.filter(question_id=question_id)
        return queryset
