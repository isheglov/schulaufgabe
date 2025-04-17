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

  return (
    <div className="w-full max-w-md mx-auto">
      {!file ? (
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
      ) : (
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
          <button
            onClick={removeFile}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Remove / Replace
          </button>
        </div>
      )}
    </div>
  );
}
