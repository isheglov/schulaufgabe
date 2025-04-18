import React, { useCallback, useState } from "react";
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

  const onDrop = useCallback((acceptedFiles: File[]) => {
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
    } catch (err: any) {
      setError(err.message || 'Upload error');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
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
          {/* Next step UI can go here */}
        </div>
      ) : null}
    </div>
  );
}
