"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

const STEPS = [
  "generate_script",
  "generate_images",
  "generate_audio",
  "assemble_video",
];

export default function RunPage() {
  const params = useParams();
  const runId = useMemo(() => params?.run_id?.toString?.() ?? "", [params]);
  const [run, setRun] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!runId) return;

    let cancelled = false;
    const fetchRun = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/runs/${runId}`);
        if (!res.ok) {
          const txt = await res.text();
          throw new Error(txt || `Failed: ${res.status}`);
        }
        const data = await res.json();
        if (!cancelled) setRun(data);
      } catch (e) {
        if (!cancelled) setError(e.message || "Fetch error");
      }
    };

    // Initial fetch, then poll
    fetchRun();
    const id = setInterval(fetchRun, 2000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [runId]);

  const renderStep = (name) => {
    const status = run?.steps?.[name] || "PENDING";
    const color =
      status === "COMPLETED" ? "#10b981" : 
      status === "IN_PROGRESS" ? "#f59e0b" : 
      status === "FAILED" ? "#ef4444" :
      "#6b7280";
    
    // Display friendly names
    const displayNames = {
      "generate_script": "Generate Script",
      "generate_images": "Generate Images", 
      "generate_audio": "Generate Audio",
      "assemble_video": "Assemble Video"
    };
    
    return (
      <div key={name} style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span
          style={{
            display: "inline-block",
            minWidth: 100,
            padding: "4px 12px",
            borderRadius: 999,
            background: color,
            color: "white",
            fontSize: 12,
            fontWeight: "500",
          }}
        >
          {status}
        </span>
        <span>{displayNames[name] || name}</span>
      </div>
    );
  };

  return (
    <div style={{ maxWidth: 640, margin: "2rem auto", padding: 16 }}>
      <h1>Run: {runId}</h1>
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      <div style={{ marginTop: 16, display: "grid", gap: 8 }}>
        {STEPS.map((s) => renderStep(s))}
      </div>

      <div style={{ marginTop: 24 }}>
        <strong>Status:</strong> {run?.status || "PENDING"}
      </div>

      {run?.artifacts?.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3>Generated Files:</h3>
          <div style={{ marginTop: 16, display: "grid", gap: 8 }}>
            {run.artifacts.map((artifact, index) => {
              const fileName = artifact.split('/').pop();
              const isImage = fileName.match(/\.(jpg|jpeg|png|gif)$/i);
              const isAudio = fileName.match(/\.(mp3|wav|m4a)$/i);
              const isVideo = fileName.match(/\.(mp4|avi|mov)$/i);
              
              return (
                <div key={index} style={{ 
                  padding: 12, 
                  border: "1px solid #e5e7eb", 
                  borderRadius: 8,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center"
                }}>
                  <div>
                    <div style={{ fontWeight: "500" }}>{fileName}</div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>{artifact}</div>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    {isImage && (
                      <button
                        onClick={() => window.open(`http://127.0.0.1:8000/artifacts/${artifact}`, '_blank')}
                        style={{ 
                          padding: "4px 8px", 
                          backgroundColor: "#3b82f6", 
                          color: "white", 
                          border: "none", 
                          borderRadius: 4,
                          cursor: "pointer"
                        }}
                      >
                        View Image
                      </button>
                    )}
                    {isAudio && (
                      <button
                        onClick={() => window.open(`http://127.0.0.1:8000/artifacts/${artifact}`, '_blank')}
                        style={{ 
                          padding: "4px 8px", 
                          backgroundColor: "#10b981", 
                          color: "white", 
                          border: "none", 
                          borderRadius: 4,
                          cursor: "pointer"
                        }}
                      >
                        Play Audio
                      </button>
                    )}
                    {isVideo && (
                      <button
                        onClick={() => window.open(`http://127.0.0.1:8000/artifacts/${artifact}`, '_blank')}
                        style={{ 
                          padding: "4px 8px", 
                          backgroundColor: "#dc2626", 
                          color: "white", 
                          border: "none", 
                          borderRadius: 4,
                          cursor: "pointer"
                        }}
                      >
                        Watch Video
                      </button>
                    )}
                    <a 
                      href={`http://127.0.0.1:8000/artifacts/${artifact}`}
                      download={fileName}
                      style={{
                        padding: "4px 8px", 
                        backgroundColor: "#6b7280", 
                        color: "white", 
                        textDecoration: "none",
                        borderRadius: 4,
                        fontSize: 12
                      }}
                    >
                      Download
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      
      {run?.orkes_status && (
        <div style={{ marginTop: 16 }}>
          <strong>Orkes Status:</strong> {run.orkes_status}
        </div>
      )}
      
      {run?.workflow_id && (
        <div style={{ marginTop: 8 }}>
          <strong>Workflow ID:</strong> 
          <code style={{ marginLeft: 8, padding: "2px 6px", backgroundColor: "#f3f4f6", borderRadius: 4 }}>
            {run.workflow_id}
          </code>
        </div>
      )}
    </div>
  );
}

