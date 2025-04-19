import React, { useCallback, useState, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import Image from "next/image";

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
  const [pdfReady, setPdfReady] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'latex' | 'pdf'>('latex');

  // Toast auto-dismiss
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3500);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const onDrop = useCallback((acceptedFiles: File[], fileRejections: import('react-dropzone').FileRejection[]) => {
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
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload error');
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
    setPdfReady(false);
    setPdfError(null);
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
      // Compile PDF automatically
      const pdfRes = await fetch('http://localhost:8000/api/compile-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, latex: text }),
      });
      const pdfData = await pdfRes.json();
      if (!pdfData.success) {
        setPdfError(pdfData.error || 'Fehler beim PDF-Export');
        setToast({ type: 'error', message: '❌ Fehler beim PDF-Export' });
        setPdfReady(false);
      } else {
        setPdfReady(true);
      }
    } catch (err: unknown) {
      setGenError(err instanceof Error ? err.message : 'Fehler beim Generieren');
      setToast({ type: 'error', message: '❌ Fehler beim Generieren' });
      setPdfReady(false);
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
    <div className="w-full max-w-2xl mx-auto">
      {/* Progress Steps UI (at the very top) */}
      <div className="w-full px-2 pt-2">
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
          <div
            className={`h-full transition-all duration-300 ${currentStep === 0 ? 'bg-blue-400 w-1/3' : currentStep === 1 ? 'bg-blue-500 w-2/3' : 'bg-green-500 w-full'}`}
          ></div>
        </div>
      </div>
      <div className="bg-white rounded-xl shadow p-8 w-full">
        <h1 className="text-2xl font-bold mb-1">MatheCheck – KI-Hausaufgabenhilfe</h1>
        <p className="text-gray-600 mb-6">
          {step === 'select' ? 'Lade ein Foto der letzten Mathe-Schulaufgabe hoch' :
            step === 'done' && !latex ? 'Super! Jetzt generieren wir eine neue Aufgabe...' :
            'MatheCheck – KI-Hausaufgabenhilfe'}
        </p>
        {/* Toast notification */}
        {toast && (
          <div
            className={`fixed top-6 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded shadow-lg text-white text-base font-medium transition-all
              ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}
          >
            {toast.message}
          </div>
        )}
        {/* Step 1: File select/upload */}
        {step === 'select' && !file ? (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition ${
              isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300"
            }`}
          >
            <input {...getInputProps()} />
            <p className="text-gray-500">
              Datei auswählen oder hierher ziehen (JPG, PNG, PDF)
            </p>
            <p className="text-xs text-gray-400 mt-2">Keine OCR. Alles bleibt privat.</p>
          </div>
        ) : step === 'select' && file ? (
          <div className="flex flex-col items-center space-y-4">
            {file.type.startsWith("image/") ? (
              <div className="w-full flex flex-col items-center relative">
                <div className="mb-6">
                  <Image
                    src={preview!}
                    alt="Preview"
                    width={128}
                    height={128}
                    style={{ objectFit: 'contain' }}
                    className="rounded shadow"
                    priority
                  />
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <span className="text-6xl">📄</span>
                <span className="text-gray-700">{file.name}</span>
              </div>
            )}
            <div className="flex space-x-2 mt-4">
              <button
                onClick={removeFile}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                disabled={uploading}
              >
                Entfernen / Ersetzen
              </button>
              <button
                onClick={uploadFile}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                disabled={uploading}
              >
                {uploading ? 'Hochladen...' : 'Hochladen'}
              </button>
            </div>
            {error && <div className="text-red-600">{error}</div>}
          </div>
        ) : step === 'uploading' ? (
          <div className="text-center">Hochladen...</div>
        ) : step === 'done' && sessionId && !latex ? (
          <div className="text-center space-y-4">
            <div className="text-green-600 font-semibold">Upload erfolgreich!</div>
            <button
              onClick={generateLatex}
              className="px-4 py-2 bg-blue-900 text-white rounded hover:bg-blue-800 mt-4"
              disabled={generating}
            >
              {generating ? 'Wird erstellt…' : 'Ähnliche Schulaufgabe erstellen'}
            </button>
            {generating && <div className="mt-2 text-gray-500">Wird erstellt…</div>}
            {genError && <div className="text-red-600 mt-2">{genError}</div>}
          </div>
        ) : step === 'done' && sessionId && latex ? (
          <div className="w-full">
            {/* Tab Switcher */}
            <div className="flex mb-4">
              <button
                className={`px-4 py-2 rounded-tl rounded-tr-none rounded-bl border-b-2 ${activeTab === 'latex' ? 'bg-gray-100 border-blue-600 text-blue-700 font-semibold' : 'bg-gray-50 border-gray-200 text-gray-500'}`}
                onClick={() => setActiveTab('latex')}
              >
                LaTeX Code
              </button>
              <button
                className={`px-4 py-2 rounded-tr rounded-tl-none rounded-br border-b-2 ${activeTab === 'pdf' ? 'bg-gray-100 border-blue-600 text-blue-700 font-semibold' : 'bg-gray-50 border-gray-200 text-gray-500'}`}
                onClick={() => setActiveTab('pdf')}
              >
                PDF Vorschau
              </button>
            </div>
            {/* Tab Content */}
            <div className="bg-gray-100 rounded-b p-4 min-h-[180px]">
              {activeTab === 'latex' ? (
                <textarea
                  className="w-full h-40 p-2 rounded bg-white border border-gray-200 text-sm font-mono resize-none"
                  value={latex}
                  readOnly
                />
              ) : (
                pdfReady ? (
                  <iframe
                    src={`http://localhost:8000/api/render-pdf?session_id=${sessionId}`}
                    title="PDF Vorschau"
                    className="w-full h-40 bg-white rounded border border-gray-200"
                  />
                ) : (
                  <div className="text-gray-400 text-center py-12">PDF Vorschau (Platzhalter)</div>
                )
              )}
            </div>
            <div className="flex justify-end mt-6">
              <a
                href={`http://localhost:8000/api/render-pdf?session_id=${sessionId}`}
                className="px-4 py-2 bg-blue-900 text-white rounded hover:bg-blue-800 font-semibold"
                download
                target="_blank"
                rel="noopener noreferrer"
              >
                Neue Schulaufgabe als PDF herunterladen
              </a>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
