"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { apiGet } from "../../lib/api";

type Project = {
  id: number;
  name: string;
  description: string;
  documents_count: number;
  questions_count: number;
  runs_count: number;
  created_at: string;
};

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  const [project, setProject] = useState<Project | null>(null);

  async function fetchProject() {
    const data = await apiGet<Project>(`/projects/${projectId}/`);
    setProject(data);
  }

  useEffect(() => {
    if (projectId) {
      fetchProject();
    }
  }, [projectId]);

  if (!project) {
    return <main className="p-8">Loading...</main>;
  }

  const steps = [
    {
      title: "1. Upload documents",
      description: "Upload PDFs, DOCX, or TXT files.",
      href: `/projects/${projectId}/upload`,
      action: "Open upload",
    },
    {
      title: "2. Generate questions",
      description: "Use NVIDIA Llama to generate questions from the documents.",
      href: `/projects/${projectId}/questions`,
      action: "Generate questions",
    },
    {
      title: "3. Generate answers",
      description: "Run multiple LLMs on the selected question.",
      href: `/projects/${projectId}/answers`,
      action: "Generate answers",
    },
    {
      title: "4. Judge and rank",
      description: "Evaluate answers and export the benchmark results.",
      href: `/projects/${projectId}/ranking`,
      action: "View ranking",
    },
  ];

  return (
    <main className="max-w-6xl mx-auto p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{project.name}</h1>
        <p className="text-white mt-2">
          {project.description || "No description"}
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mb-8">
        <div className="border rounded bg-white p-4">
          <div className="text-2xl font-bold text-black">
            {project.documents_count}
          </div>
          <div className="text-black">Documents</div>
        </div>

        <div className="border rounded bg-white p-4">
          <div className="text-2xl font-bold text-black">
            {project.questions_count}
          </div>
          <div className="text-black">Generated questions</div>
        </div>

        <div className="border rounded bg-white p-4">
          <div className="text-2xl font-bold text-black">
            {project.runs_count}
          </div>
          <div className="text-black">Benchmark runs</div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {steps.map((step) => (
          <Link
            key={step.href}
            href={step.href}
            className="border rounded bg-white p-6 hover:shadow transition"
          >
            <h2 className="font-bold text-xl mb-2 text-black">{step.title}</h2>
            <p className="text-black mb-4">{step.description}</p>
            <span className="font-semibold underline text-black">
              {step.action}
            </span>
          </Link>
        ))}
      </div>
    </main>
  );
}
