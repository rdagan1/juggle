import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { uploadApi, type GioAttachment } from "../api/client";
import { he } from "../i18n/he";

interface FileDropzoneProps {
  onAttachment?: (attachment: GioAttachment) => void;
}

export function FileDropzone({ onAttachment }: FileDropzoneProps) {
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const pdf = acceptedFiles.find((f) => f.name.toLowerCase().endsWith(".pdf"));
      if (!pdf) return;

      setIsUploading(true);
      try {
        const { data } = await uploadApi.uploadPdf(pdf);
        onAttachment?.({
          id: data.document_id,
          type: "pdf",
          title: pdf.name.replace(/\.pdf$/i, ""),
          parseStatus: "pending",
        });
      } catch {
        // Silent fail — Gio will show an error message via WS
      } finally {
        setIsUploading(false);
        setIsDraggingOver(false);
      }
    },
    [onAttachment],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: false,
    noClick: true, // Global drag-over only; explicit button in settings
  });

  // Global drag-over detection
  useEffect(() => {
    const handleDragEnter = () => setIsDraggingOver(true);
    const handleDragLeave = (e: DragEvent) => {
      if (!e.relatedTarget) setIsDraggingOver(false);
    };
    const handleDrop = () => setIsDraggingOver(false);

    document.addEventListener("dragenter", handleDragEnter);
    document.addEventListener("dragleave", handleDragLeave);
    document.addEventListener("drop", handleDrop);
    return () => {
      document.removeEventListener("dragenter", handleDragEnter);
      document.removeEventListener("dragleave", handleDragLeave);
      document.removeEventListener("drop", handleDrop);
    };
  }, []);

  if (!isDragActive && !isDraggingOver && !isUploading) return null;

  return (
    <div
      {...getRootProps()}
      className="fixed inset-0 z-50 flex items-center justify-center bg-gio-500/20 backdrop-blur-sm"
      role="dialog"
      aria-label={he.fileDropzone.dragActive}
      dir="rtl"
    >
      <input {...getInputProps()} aria-label="העלאת קובץ PDF" />
      <div className="bg-white rounded-2xl shadow-xl p-10 flex flex-col items-center gap-4 border-2 border-dashed border-gio-500">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="text-gio-500">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
          <path d="M14 2v6h6M12 11v6M9 14l3-3 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <p className="text-lg font-medium text-gio-600">
          {isUploading ? "מעלה..." : he.fileDropzone.dragActive}
        </p>
        <p className="text-sm text-gray-500">{he.fileDropzone.instruction}</p>
      </div>
    </div>
  );
}

/** Clickable upload button for use inside the chat input area. */
export function UploadButton({ onAttachment }: FileDropzoneProps) {
  const [isUploading, setIsUploading] = useState(false);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop: async (files) => {
      const pdf = files[0];
      if (!pdf) return;
      setIsUploading(true);
      try {
        const { data } = await uploadApi.uploadPdf(pdf);
        onAttachment?.({
          id: data.document_id,
          type: "pdf",
          title: pdf.name.replace(/\.pdf$/i, ""),
          parseStatus: "pending",
        });
      } finally {
        setIsUploading(false);
      }
    },
    accept: { "application/pdf": [".pdf"] },
    multiple: false,
  });

  return (
    <button
      {...getRootProps()}
      type="button"
      disabled={isUploading}
      className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl
                 text-navy-200 hover:text-gio-500 hover:bg-navy-50 disabled:opacity-40 transition-colors"
      aria-label="העלאת קובץ PDF"
    >
      <input {...getInputProps()} />
      {isUploading ? (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true" className="animate-spin">
          <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="2" strokeDasharray="22 22" strokeLinecap="round" />
        </svg>
      ) : (
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d="M4 10.5V15a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <path d="M10 12V4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          <path d="M7 7l3-3 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </button>
  );
}
