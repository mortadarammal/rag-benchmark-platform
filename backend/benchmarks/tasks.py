# backend/benchmarks/tasks.py

from celery import shared_task
from django.utils import timezone
from rag.config import RAG_CONFIG
from benchmarks.models import (
    GeneratedQuestion,
    BenchmarkRun,
    ModelAnswer,
    EvaluationResult,
)
from benchmarks.question_generation import generate_questions_for_project
from benchmarks.answer_generation import (
    generate_answer_with_model,
    get_default_generator_models,
)

from benchmarks.judge_evaluation import evaluate_answer_with_judge 
#from benchmarks.ragas_evaluation_runner import evaluate_answer_with_ragas
#from benchmarks.ragas_nvidia import get_ragas_judge_llm, get_ragas_embeddings

@shared_task
def generate_questions_task(
    project_id: int,
    number_of_questions: int = 10,
):
    """
    
    Generates questions for one project and stores them in PostgreSQL.
    """

    questions, source_chunks = generate_questions_for_project(
        project_id=project_id,
        number_of_questions=number_of_questions,
    )

    source_chunk_ids = [
        chunk.get("chunk_id")
        for chunk in source_chunks
        if chunk.get("chunk_id")
    ]

    source_document_ids = list(
        {
            chunk.get("document_id")
            for chunk in source_chunks
            if chunk.get("document_id")
        }
    )

    created_questions = []

    for question in questions:
        obj = GeneratedQuestion.objects.create(
            project_id=project_id,
            question=question,
            source_chunk_ids=source_chunk_ids,
            source_document_ids=source_document_ids,
        )

        created_questions.append(
            {
                "id": obj.id,
                "question": obj.question,
            }
        )

    return {
        "project_id": project_id,
        "questions_created": len(created_questions),
        "questions": created_questions,
    }


@shared_task
def generate_answers_for_selected_question_task(
    question_id: int,
    selected_model_keys: list[str] | None = None,
):
    """
    

    Takes the question selected by the user and asks multiple LLMs to answer it.
    """

    question_obj = GeneratedQuestion.objects.get(id=question_id)
    project = question_obj.project

    all_models = get_default_generator_models()

    if selected_model_keys:
        models_to_run = {
            key: value
            for key, value in all_models.items()
            if key in selected_model_keys
        }
    else:
        models_to_run = all_models

    if not models_to_run:
        raise ValueError("No valid generator models selected.")

    benchmark_run = BenchmarkRun.objects.create(
        project=project,
        question=question_obj,
        status="running",
    )

    try:
        created_answers = []

        for model_key, model_name in models_to_run.items():
            answer_obj = ModelAnswer.objects.create(
                benchmark_run=benchmark_run,
                model_key=model_key,
                model_name=model_name,
                question=question_obj.question,
                status="running",
            )

            try:
                result = generate_answer_with_model(
                    question=question_obj.question,
                    project_id=project.id,
                    model_key=model_key,
                    model_name=model_name,
                )

                answer_obj.answer = result["generated_answer"]
                answer_obj.retrieved_contexts = result["retrieved_contexts"]
                answer_obj.full_context = result["full_context"]
                answer_obj.latency_ms = result["latency_ms"]
                answer_obj.status = (
                    "failed"
                    if result["generated_answer"].startswith("[ERROR]")
                    else "completed"
                )
                answer_obj.completed_at = timezone.now()

                if answer_obj.status == "failed":
                    answer_obj.error_message = result["generated_answer"]

                answer_obj.save(
                    update_fields=[
                        "answer",
                        "retrieved_contexts",
                        "full_context",
                        "latency_ms",
                        "status",
                        "error_message",
                        "completed_at",
                    ]
                )

            except Exception as e:
                answer_obj.status = "failed"
                answer_obj.error_message = str(e)
                answer_obj.completed_at = timezone.now()
                answer_obj.save(
                    update_fields=[
                        "status",
                        "error_message",
                        "completed_at",
                    ]
                )

            created_answers.append(
                {
                    "id": answer_obj.id,
                    "model_key": answer_obj.model_key,
                    "status": answer_obj.status,
                }
            )

        benchmark_run.status = "completed"
        benchmark_run.completed_at = timezone.now()
        benchmark_run.save(update_fields=["status", "completed_at"])

        return {
            "benchmark_run_id": benchmark_run.id,
            "question_id": question_obj.id,
            "answers": created_answers,
        }

    except Exception as e:
        benchmark_run.status = "failed"
        benchmark_run.error_message = str(e)
        benchmark_run.completed_at = timezone.now()
        benchmark_run.save(
            update_fields=[
                "status",
                "error_message",
                "completed_at",
            ]
        )

        raise



@shared_task
def evaluate_benchmark_run_task(benchmark_run_id: int):
    """
    Evaluates every completed ModelAnswer in one BenchmarkRun.
    Saves EvaluationResult rows.
    """
    
    benchmark_run = BenchmarkRun.objects.get(id=benchmark_run_id)

    answers = ModelAnswer.objects.filter(
        benchmark_run=benchmark_run,
        status="completed",
    ).order_by("id")

    if not answers.exists():
        raise ValueError("No completed answers found for this benchmark run.")

    evaluated = []

    for answer_obj in answers:
        # result = evaluate_answer_with_judge(
        #     question=answer_obj.question,
        #     answer=answer_obj.answer,
        #     retrieved_contexts=answer_obj.retrieved_contexts,
        # )
        try:
            result = evaluate_answer_with_judge(
                question=answer_obj.question,
                answer=answer_obj.answer,
                retrieved_contexts=answer_obj.retrieved_contexts,
            )
    #         result = evaluate_answer_with_ragas(
    #               question=answer_obj.question,
    #               answer=answer_obj.answer,
    #               retrieved_contexts=answer_obj.retrieved_contexts,
    # )
 

        except Exception as e:
            result = {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0,
                "context_sufficiency": 0.0,
                "context_recall": 0.0,
                "final_score": 0.0,
                "faithfulness_reasoning": f"Evaluation failed: {str(e)}",
                "answer_relevancy_reasoning": f"Evaluation failed: {str(e)}",
                "context_precision_reasoning": f"Evaluation failed: {str(e)}",
                "context_sufficiency_reasoning": f"Evaluation failed: {str(e)}",
                "context_recall_reasoning": f"Evaluation failed: {str(e)}",
                "raw_judge_output": {"error": str(e)},
            }

        evaluation, _ = EvaluationResult.objects.update_or_create(
            answer=answer_obj,
            defaults={
                "judge_model": RAG_CONFIG["judge_model"],
                "faithfulness": result["faithfulness"],
                "answer_relevancy": result["answer_relevancy"],
                "context_precision": result["context_precision"],
                #"context_recall": result["context_recall"],
                "context_sufficiency": result["context_sufficiency"],
                "final_score": result["final_score"],
                "faithfulness_reasoning": result["faithfulness_reasoning"],
                "answer_relevancy_reasoning": result["answer_relevancy_reasoning"],
                "context_precision_reasoning": result["context_precision_reasoning"],
                #"context_recall_reasoning": result["context_recall_reasoning"],
                "context_sufficiency_reasoning": result["context_sufficiency_reasoning"],
                "raw_judge_output": result["raw_judge_output"],
            },
        )

        evaluated.append(
            {
                "answer_id": answer_obj.id,
                "model_key": answer_obj.model_key,
                "faithfulness": evaluation.faithfulness,
                "answer_relevancy": evaluation.answer_relevancy,
                "context_precision": evaluation.context_precision,
                "context_sufficiency": evaluation.context_sufficiency,
                "final_score": evaluation.final_score,
            }
        )

    return {
        "benchmark_run_id": benchmark_run.id,
        "evaluated_answers": evaluated,
    }