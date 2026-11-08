from django.db import transaction
from rest_framework import serializers

from .models import Choice, Exam, Question


class ChoiceSerializer(serializers.ModelSerializer):
    """Choice. The parent question is set by the view/serializer, not by the client
    when the choice travels nested inside a question."""

    class Meta:
        model = Choice
        fields = ["id", "question", "text", "is_correct"]
        read_only_fields = ["id", "question"]


class StandaloneChoiceSerializer(ChoiceSerializer):
    """Used by /api/choices/: here the question IS referenced by its id."""

    class Meta(ChoiceSerializer.Meta):
        read_only_fields = ["id"]


class NestedChoiceSerializer(serializers.ModelSerializer):
    """Choice as it appears inside a question (no 'question' field, it is implied)."""

    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct"]
        read_only_fields = ["id"]


class QuestionSerializer(serializers.ModelSerializer):
    # Relationship decision:
    #   - choices travel NESTED inside the question (they make no sense alone);
    #   - the exam is referenced by its primary key (exam is an independent resource).
    choices = NestedChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ["id", "exam", "text", "points", "choices"]
        read_only_fields = ["id"]

    def validate_choices(self, value):
        """Custom rule: a question must have exactly one correct choice."""
        correct = sum(1 for choice in value if choice.get("is_correct"))
        if correct != 1:
            raise serializers.ValidationError(
                f"La pregunta debe tener exactamente una opcion correcta (recibidas: {correct})."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        choices_data = validated_data.pop("choices")
        question = Question.objects.create(**validated_data)
        Choice.objects.bulk_create(Choice(question=question, **c) for c in choices_data)
        return question

    @transaction.atomic
    def update(self, instance, validated_data):
        choices_data = validated_data.pop("choices", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if choices_data is not None:
            # Replace the whole set of choices so the "exactly one correct" rule keeps holding.
            instance.choices.all().delete()
            Choice.objects.bulk_create(Choice(question=instance, **c) for c in choices_data)
        return instance


class ExamSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(source="questions.count", read_only=True)

    class Meta:
        model = Exam
        fields = ["id", "title", "description", "created_at", "question_count"]
        read_only_fields = ["id", "created_at", "question_count"]
