import React, { useCallback, useState, useEffect } from "react";
import { useDropzone } from "react-dropzone";

const ACCEPTED_TYPES = {
  "image/jpeg": [],
  "image/png": [],
  "application/pdf": [],
};

export default function FileUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [step, setStep] = useState<'select' | 'uploading' | 'done'>('select');
  const [generating, setGenerating] = useState(false);
  const [latex, setLatex] = useState<string | null>(null);
  const [genError, setGenError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Toast auto-dismiss
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3500);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const onDrop = useCallback((acceptedFiles: File[], fileRejections: any[]) => {
    if (fileRejections && fileRejections.length > 0) {
      setToast({ type: 'error', message: '❌ Dateiformat nicht unterstützt' });
      return;
    }
    const uploaded = acceptedFiles[0];
    setFile(uploaded);

    if (uploaded && uploaded.type.startsWith("image/")) {
      setPreview(URL.createObjectURL(uploaded));
    } else {
      setPreview(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
  });

  const removeFile = () => {
    setFile(null);
    setPreview(null);
  };

  const uploadFile = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      setSessionId(data.session_id);
      setStep('done');
      setToast({ type: 'success', message: '✅ Datei erfolgreich hochgeladen' });
    } catch (err: any) {
      setError(err.message || 'Upload error');
      setToast({ type: 'error', message: '❌ Upload fehlgeschlagen' });
    } finally {
      setUploading(false);
    }
  };

  const generateLatex = async () => {
    if (!sessionId) return;
    setGenerating(true);
    setGenError(null);
    setLatex(null);
    try {
      const res = await fetch('http://localhost:8000/api/generate-latex', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
      if (!res.ok) throw new Error('Fehler beim Generieren');
      const text = await res.text();
      setLatex(text);
      setToast({ type: 'success', message: '✅ Aufgabe erfolgreich generiert' });
    } catch (err: any) {
      setGenError(err.message || 'Fehler beim Generieren');
      setToast({ type: 'error', message: '❌ Fehler beim Generieren' });
    } finally {
      setGenerating(false);
    }
  };

  // Step mapping for progress UI
  const getStepIndex = () => {
    if (step === 'select') return 0;
    if (step === 'uploading') return 0;
    if (step === 'done' && !latex) return 1;
    if (step === 'done' && latex) return 2;
    return 0;
  };
  const steps = [
    'Upload',
    'Aufgaben generieren',
    'PDF herunterladen',
  ];
  const currentStep = getStepIndex();

  return (
    <div className="w-full max-w-md mx-auto">
      {/* Toast notification */}
      {toast && (
        <div
          className={`fixed top-6 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded shadow-lg text-white text-base font-medium transition-all
            ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}
        >
          {toast.message}
        </div>
      )}
      {/* Progress Steps UI */}
      <div className="flex justify-between items-center mb-8">
        {steps.map((label, idx) => (
          <div key={label} className="flex-1 flex flex-col items-center">
            <div
              className={`w-8 h-8 flex items-center justify-center rounded-full border-2 text-sm font-bold mb-1
                ${currentStep === idx ? 'bg-blue-600 text-white border-blue-600' : idx < currentStep ? 'bg-green-500 text-white border-green-500' : 'bg-gray-200 text-gray-400 border-gray-300'}`}
            >
              {idx + 1}
            </div>
            <span className={`text-xs ${currentStep === idx ? 'text-blue-700 font-semibold' : idx < currentStep ? 'text-green-700' : 'text-gray-400'}`}>{label}</span>
            {idx < steps.length - 1 && (
              <div className={`h-1 w-full ${idx < currentStep ? 'bg-green-500' : 'bg-gray-200'}`}></div>
            )}
          </div>
        ))}
      </div>
      {step === 'select' && !file ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition ${
            isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300"
          }`}
        >
          <input {...getInputProps()} />
          <p className="text-gray-500">
            Drag & drop a JPG, PNG, or PDF here, or click to select a file
          </p>
        </div>
      ) : step === 'select' && file ? (
        <div className="flex flex-col items-center space-y-4">
          {file.type.startsWith("image/") ? (
            <img
              src={preview!}
              alt="Preview"
              className="max-h-48 rounded shadow"
            />
          ) : (
            <div className="flex flex-col items-center">
              <span className="text-6xl">📄</span>
              <span className="text-gray-700">{file.name}</span>
            </div>
          )}
          <div className="flex space-x-2">
            <button
              onClick={removeFile}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
              disabled={uploading}
            >
              Remove / Replace
            </button>
            <button
              onClick={uploadFile}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              disabled={uploading}
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
          {error && <div className="text-red-600">{error}</div>}
        </div>
      ) : step === 'uploading' ? (
        <div className="text-center">Uploading...</div>
      ) : step === 'done' && sessionId ? (
        <div className="text-center space-y-4">
          <div className="text-green-600 font-semibold">Upload successful!</div>
          <div className="text-gray-700">Session ID: <span className="font-mono">{sessionId}</span></div>
          <button
            onClick={generateLatex}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 mt-4"
            disabled={generating}
          >
            {generating ? 'Wird erstellt…' : 'Generate'}
          </button>
          {generating && <div className="mt-2 text-gray-500">Wird erstellt…</div>}
          {genError && <div className="text-red-600 mt-2">{genError}</div>}
          {latex && (
            <div className="mt-4 text-left bg-gray-100 p-2 rounded max-h-64 overflow-auto">
              <pre className="text-xs whitespace-pre-wrap">{latex}</pre>
            </div>
          )}
          {latex && sessionId && (
            <a
              href={`http://localhost:8000/api/render-pdf?session_id=${sessionId}`}
              className="inline-block mt-4 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 font-semibold"
              download
              target="_blank"
              rel="noopener noreferrer"
            >
              Neue Schulaufgabe als PDF herunterladen
            </a>
          )}
        </div>
      ) : null}
    </div>
  );
}
