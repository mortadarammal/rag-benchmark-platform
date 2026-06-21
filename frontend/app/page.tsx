"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "./lib/api";

type Project = {
  id: number;
  name: string;
  description: string;
  documents_count: number;
  questions_count: number;
  runs_count: number;
  created_at: string;
};

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  async function fetchProjects() {
    setLoading(true);
    const data = await apiGet<Project[]>("/projects/");
    setProjects(data);
    setLoading(false);
  }

  useEffect(() => {
    fetchProjects();
  }, []);

  return (
    <main className="max-w-6xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-white mt-2">Manage the RAG benchmark projects.</p>
        </div>

        <Link
          href="/projects/new"
          className="px-4 py-2 rounded bg-black text-white"
        >
          New Project
        </Link>
      </div>

      {loading && <p>Loading projects...</p>}

      {!loading && projects.length === 0 && (
        <div className="border rounded bg-white p-8 text-center">
          <h2 className="font-semibold text-xl mb-2">No projects yet</h2>
          <p className="text-black mb-4">
            Create the first benchmark project to start uploading documents.
          </p>
          <Link
            href="/projects/new"
            className="px-4 py-2 rounded bg-black text-white"
          >
            Create Project
          </Link>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        {projects.map((project) => (
          <Link
            key={project.id}
            href={`/projects/${project.id}`}
            className="border rounded bg-white p-6 hover:shadow transition"
          >
            <h2 className="font-bold text-xl mb-2 text-black">
              {project.name}
            </h2>

            <p className="text-black mb-4">
              {project.description || "No description"}
            </p>

            <div className="grid grid-cols-3 gap-3 text-sm">
              <div className="border rounded p-3">
                <div className="font-bold text-blue-600">
                  {project.documents_count}
                </div>
                <div className="text-black">Documents</div>
              </div>

              <div className="border rounded p-3">
                <div className="font-bold text-blue-600">
                  {project.questions_count}
                </div>
                <div className="text-black">Questions</div>
              </div>

              <div className="border rounded p-3">
                <div className="font-bold text-blue-600">
                  {project.runs_count}
                </div>
                <div className="text-black">Runs</div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
