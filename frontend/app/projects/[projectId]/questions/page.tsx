"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiGet, apiPost } from "../../../lib/api";

type GeneratedQuestion = {
  id: number;
  project: number;
  question: string;
  source_chunk_ids: string[];
  source_document_ids: number[];
  status: string;
  selected: boolean;
  created_at: string;
};

export default function QuestionsPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  const [questions, setQuestions] = useState<GeneratedQuestion[]>([]);
  const [numberOfQuestions, setNumberOfQuestions] = useState(10);

  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [selectingId, setSelectingId] = useState<number | null>(null);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function fetchQuestions() {
    try {
      setLoading(true);
      setError("");

      const data = await apiGet<GeneratedQuestion[]>(
        `/benchmarks/projects/${projectId}/questions/`,
      );

      setQuestions(data);
    } catch (err) {
      console.error(err);
      setError("Could not load questions. Make sure Django is running.");
    } finally {
      setLoading(false);
    }
  }

  async function generateQuestions() {
    try {
      setGenerating(true);
      setMessage("");
      setError("");

      await apiPost("/benchmarks/questions/generate/", {
        project_id: Number(projectId),
        number_of_questions: numberOfQuestions,
      });

      setMessage(
        "Question generation started. Wait a few seconds, then refresh.",
      );

      setTimeout(fetchQuestions, 5000);
    } catch (err) {
      console.error(err);
      setError("Could not start question generation.");
    } finally {
      setGenerating(false);
    }
  }

  async function selectQuestion(questionId: number) {
    try {
      setSelectingId(questionId);
      setMessage("");
      setError("");

      await apiPost(`/benchmarks/questions/${questionId}/select/`);

      setMessage("Question selected successfully.");
      await fetchQuestions();
    } catch (err) {
      console.error(err);
      setError("Could not select question.");
    } finally {
      setSelectingId(null);
    }
  }

  useEffect(() => {
    if (projectId) {
      fetchQuestions();
    }
  }, [projectId]);

  const selectedQuestion = questions.find((q) => q.selected);

  return (
    <main className="max-w-5xl mx-auto p-8">
      <div className="mb-8">
        <Link
          href={`/projects/${projectId}`}
          className="text-sm underline text-white"
        >
          ← Back to project
        </Link>

        <h1 className="text-3xl font-bold mt-4">Questions</h1>
      </div>

      <div className="border rounded bg-white p-6 mb-8">
        <h2 className="font-semibold text-xl mb-4 text-black">
          Generate questions
        </h2>

        <div className="flex flex-col sm:flex-row gap-4 sm:items-end">
          <div>
            <label className="block font-medium mb-2 text-black">
              Number of questions
            </label>

            <input
              type="number"
              min={1}
              max={30}
              value={numberOfQuestions}
              onChange={(e) => setNumberOfQuestions(Number(e.target.value))}
              className="border rounded px-3 py-2 w-40 text-blue-500"
            />
          </div>

          <button
            onClick={generateQuestions}
            disabled={generating}
            className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
          >
            {generating ? "Starting..." : "Generate Questions"}
          </button>

          <button
            onClick={fetchQuestions}
            disabled={loading}
            className="px-4 py-2 rounded border text-black"
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {message && <p className="mt-4 text-green-700 text-sm">{message}</p>}

        {error && <p className="mt-4 text-red-700 text-sm">{error}</p>}
      </div>

      {selectedQuestion && (
        <div className="border rounded bg-green-50 border-green-600 p-4 mb-8">
          <h2 className="font-semibold mb-2 text-green-800">
            Selected question
          </h2>

          <p className="text-black">{selectedQuestion.question}</p>

          <Link
            href={`/projects/${projectId}/answers`}
            className="inline-block mt-4 px-4 py-2 rounded bg-green-700 text-white"
          >
            Continue to answer generation
          </Link>
        </div>
      )}

      <div className="border rounded bg-white">
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="font-semibold text-black">Generated questions</h2>
          <span className="text-sm text-black">
            {questions.length} question(s)
          </span>
        </div>

        {loading ? (
          <div className="p-6 text-black">Loading questions...</div>
        ) : questions.length === 0 ? (
          <div className="p-6 text-black">
            No questions generated yet. Click “Generate Questions”.
          </div>
        ) : (
          <div className="divide-y">
            {questions.map((question) => (
              <div
                key={question.id}
                className={`p-5 text-black ${
                  question.selected ? "bg-green-50" : "bg-white"
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  <div>
                    <p className="font-medium">{question.question}</p>

                    <div className="text-sm text-gray-800 mt-2">
                      ID: {question.id} · Status: {question.status}
                    </div>
                  </div>

                  <div className="shrink-0">
                    {question.selected ? (
                      <span className="px-3 py-1 rounded bg-green-700 text-white text-sm">
                        Selected
                      </span>
                    ) : (
                      <button
                        onClick={() => selectQuestion(question.id)}
                        disabled={selectingId === question.id}
                        className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
                      >
                        {selectingId === question.id
                          ? "Selecting..."
                          : "Select"}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
