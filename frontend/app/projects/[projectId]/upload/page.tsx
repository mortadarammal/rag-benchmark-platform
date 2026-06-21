"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "../../../lib/api";
import Link from "next/link";
import { useParams } from "next/navigation";

type UploadedDocument = {
  id: number;
  original_name: string;
  status: string;
  error_message: string | null;
  chunks_count: number;
  created_at: string;
  processed_at: string | null;
};

export default function UploadPage() {
  const params = useParams();
  const projectId = params.projectId as string;

  const [file, setFile] = useState<File | null>(null);
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [uploading, setUploading] = useState(false);

  async function fetchDocuments() {
    const res = await fetch(`${API_BASE_URL}/documents/project/${projectId}/`);
    const data = await res.json();
    setDocuments(data);
  }

  async function uploadFile() {
    if (!file) return;

    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("project", projectId);

    await fetch(`${API_BASE_URL}/documents/upload/`, {
      method: "POST",
      body: formData,
    });

    setFile(null);
    setUploading(false);

    setTimeout(fetchDocuments, 2000);
  }

  useEffect(() => {
    fetchDocuments();

    const interval = setInterval(fetchDocuments, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <main className="max-w-5xl mx-auto p-8">
      <div className="mb-8">
        <Link
          href={`/projects/${projectId}`}
          className="text-sm underline text-white"
        >
          ← Back to project
        </Link>

        <h1 className="text-3xl font-bold mb-2">Upload documents</h1>
      </div>

      <div className="border rounded bg-white p-6 mb-8">
        <input
          type="file"
          accept=".pdf,.docx,.txt,.md"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="mb-4 text-black"
        />

        <br />

        <button
          onClick={uploadFile}
          disabled={!file || uploading}
          className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Upload"}
        </button>
      </div>

      <div className="border rounded bg-white text-black">
        <div className="p-4 border-b font-semibold text-black">Documents</div>

        {documents.length === 0 ? (
          <div className="p-6 text-black">No documents uploaded yet.</div>
        ) : (
          <table className="w-full text-sm text-black">
            <thead className="bg-gray-100 text-black">
              <tr>
                <th className="text-left p-3">File</th>
                <th className="text-left p-3">Status</th>
                <th className="text-left p-3">Chunks</th>
                <th className="text-left p-3">Error</th>
              </tr>
            </thead>

            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-t">
                  <td className="p-3 text-black">{doc.original_name}</td>
                  <td className="p-3 text-black">{doc.status}</td>
                  <td className="p-3 text-black">{doc.chunks_count}</td>
                  <td className="p-3 text-red-600">
                    {doc.error_message || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </main>
  );
}
