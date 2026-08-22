import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import type { Document } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import {
  Upload, FileText, CheckCircle2, AlertCircle,
  Loader2, Eye, X, ChevronDown, ChevronUp, RefreshCw,
  Shield, Edit3, Flag
} from 'lucide-react';

export const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [editField, setEditField] = useState<{ id: string; value: string } | null>(null);
  const [editReason, setEditReason] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const reload = async () => {
    try {
      const docs = await api.listDocuments();
      setDocuments(docs);
      if (selectedDoc) {
        const updated = docs.find(d => d.id === selectedDoc.id);
        if (updated) setSelectedDoc(updated);
      }
    } catch (err: any) {
      console.error('Failed to load documents', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { reload(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    try {
      const doc = await api.uploadDocument(file, 'INVOICE');
      setUploadSuccess(`"${doc.file_name}" uploaded and processed. Status: ${doc.processing_status}.`);
      await reload();
      setSelectedDoc(doc);
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed. Check file type and size (max 10MB).');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleVerifyField = async (docId: string, fieldId: string) => {
    setActionLoading(fieldId);
    try {
      await api.verifyDocumentField(docId, fieldId);
      await reload();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleEditField = async (docId: string, fieldId: string) => {
    if (!editField || !editField.value.trim()) return;
    setActionLoading(fieldId);
    try {
      await api.editDocumentField(docId, fieldId, editField.value, editReason || 'Manual reviewer correction');
      setEditField(null);
      setEditReason('');
      await reload();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleFlagField = async (docId: string, fieldId: string) => {
    setActionLoading(fieldId);
    try {
      await api.flagDocumentField(docId, fieldId);
      await reload();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleVerifyDocument = async (docId: string) => {
    setActionLoading(docId);
    try {
      const updated = await api.verifyDocument(docId);
      setSelectedDoc(updated);
      await reload();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const confidenceBadge = (level: string) => {
    const map: Record<string, string> = {
      HIGH: 'text-emerald-700 bg-emerald-50 border-emerald-200',
      MEDIUM: 'text-amber-700 bg-amber-50 border-amber-200',
      LOW: 'text-red-700 bg-red-50 border-red-200',
    };
    return (
      <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${map[level] || 'text-slate-600 bg-slate-100 border-slate-200'}`}>
        {level}
      </span>
    );
  };

  const verificationBadge = (status: string) => {
    const map: Record<string, string> = {
      VERIFIED: 'text-emerald-700 bg-emerald-50 border-emerald-200',
      EDITED: 'text-indigo-700 bg-indigo-50 border-indigo-200',
      FLAGGED: 'text-red-700 bg-red-50 border-red-200',
      UNVERIFIED: 'text-slate-500 bg-slate-100 border-slate-200',
    };
    return (
      <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${map[status] || 'text-slate-600 bg-slate-100 border-slate-200'}`}>
        {status}
      </span>
    );
  };

  const statusBadge = (status: string) => {
    const map: Record<string, string> = {
      VERIFIED: 'text-emerald-700 bg-emerald-50 border-emerald-200',
      EXTRACTED: 'text-indigo-700 bg-indigo-50 border-indigo-200',
      NEEDS_REVIEW: 'text-amber-700 bg-amber-50 border-amber-200',
      PROCESSING: 'text-blue-700 bg-blue-50 border-blue-200',
      UPLOADED: 'text-slate-600 bg-slate-100 border-slate-200',
      FAILED: 'text-red-700 bg-red-50 border-red-200',
    };
    return (
      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${map[status] || 'text-slate-600 bg-slate-100 border-slate-200'}`}>
        {status.replace(/_/g, ' ')}
      </span>
    );
  };

  return (
    <div className="space-y-5 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-black text-slate-900">Document Workbench</h2>
          <p className="text-xs text-slate-500 mt-0.5">Upload, extract, and verify invoice documents to feed evidence into the exception workflow.</p>
        </div>
        <button
          onClick={() => reload()}
          disabled={loading}
          className="flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-indigo-600 transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Upload Area */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">Upload Invoice Document</h3>
        <label className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-8 cursor-pointer transition-all ${
          uploading ? 'border-indigo-400 bg-indigo-50' : 'border-slate-300 hover:border-indigo-400 hover:bg-indigo-50/50'
        }`}>
          <input
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            className="hidden"
            onChange={handleUpload}
            disabled={uploading}
          />
          {uploading ? (
            <>
              <Loader2 className="h-8 w-8 text-indigo-500 animate-spin mb-2" />
              <p className="text-sm font-bold text-indigo-600">Processing document...</p>
              <p className="text-xs text-indigo-500 mt-1">Extracting fields and assigning confidence scores</p>
            </>
          ) : (
            <>
              <Upload className="h-8 w-8 text-slate-400 mb-2" />
              <p className="text-sm font-bold text-slate-700">Click to upload invoice document</p>
              <p className="text-xs text-slate-400 mt-1">PDF, PNG, JPG — Max 10MB — Synthetic demo documents only</p>
            </>
          )}
        </label>

        {uploadSuccess && (
          <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 flex items-start gap-2">
            <CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5" />
            {uploadSuccess}
          </div>
        )}
        {uploadError && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            {uploadError}
          </div>
        )}
      </div>

      {/* Documents List + Detail Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">

        {/* Document List */}
        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <p className="text-xs font-bold text-slate-700 uppercase tracking-wide">Documents ({documents.length})</p>
          </div>
          {loading ? (
            <div className="py-10 flex items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-indigo-500" />
            </div>
          ) : documents.length === 0 ? (
            <div className="py-10 text-center text-xs text-slate-400">
              <FileText className="h-8 w-8 text-slate-300 mx-auto mb-2" />
              No documents uploaded yet.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto">
              {documents.map(doc => (
                <button
                  key={doc.id}
                  onClick={() => setSelectedDoc(doc)}
                  className={`w-full text-left px-4 py-3 text-xs transition-all hover:bg-indigo-50 ${
                    selectedDoc?.id === doc.id ? 'bg-indigo-50 border-l-2 border-indigo-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="font-bold text-slate-800 truncate">{doc.file_name}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{doc.document_type} • {(doc.file_size / 1024).toFixed(1)}KB</p>
                    </div>
                    {statusBadge(doc.processing_status)}
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    {new Date(doc.created_at).toLocaleDateString()} • {doc.fields.length} fields extracted
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Document Detail */}
        <div className="lg:col-span-8">
          {!selectedDoc ? (
            <div className="bg-white border border-slate-200 rounded-xl p-10 shadow-sm h-full flex flex-col items-center justify-center text-slate-400">
              <FileText className="h-10 w-10 text-slate-300 mb-3" />
              <p className="text-sm font-bold text-slate-500">Select a document to inspect</p>
              <p className="text-xs mt-1">Upload an invoice then click to view extracted fields</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Document Header */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">{selectedDoc.file_name}</h3>
                    <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                      {statusBadge(selectedDoc.processing_status)}
                      <span className="text-[10px] text-slate-500">{selectedDoc.document_type}</span>
                      <span className="text-[10px] text-slate-500">Confidence: {Math.round(selectedDoc.classification_confidence * 100)}%</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedDoc.processing_status !== 'VERIFIED' && (
                      <button
                        onClick={() => handleVerifyDocument(selectedDoc.id)}
                        disabled={actionLoading === selectedDoc.id}
                        className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-[10px] font-bold rounded-lg transition-all disabled:opacity-60"
                      >
                        {actionLoading === selectedDoc.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle2 className="h-3 w-3" />}
                        Verify Document
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Extracted Fields */}
              <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Extracted Fields ({selectedDoc.fields.length})
                </h4>
                {selectedDoc.fields.length === 0 ? (
                  <p className="text-xs text-slate-400 py-4 text-center">No fields extracted.</p>
                ) : (
                  <div className="space-y-2">
                    {selectedDoc.fields.map(field => (
                      <div key={field.id} className={`p-3 border rounded-lg space-y-2 ${
                        field.confidence_level === 'LOW' ? 'bg-red-50 border-red-200' :
                        field.verification_status === 'VERIFIED' ? 'bg-emerald-50 border-emerald-200' :
                        field.verification_status === 'EDITED' ? 'bg-indigo-50 border-indigo-200' :
                        field.verification_status === 'FLAGGED' ? 'bg-amber-50 border-amber-200' :
                        'bg-slate-50 border-slate-200'
                      }`}>
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-bold text-slate-700">{field.field_name.replace(/_/g, ' ')}</span>
                            {confidenceBadge(field.confidence_level)}
                            {verificationBadge(field.verification_status)}
                            <span className="text-[10px] text-slate-400">Pg {field.page_number}</span>
                          </div>
                          <span className="font-mono font-bold text-xs text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200 whitespace-nowrap">
                            {field.extracted_value || '—'}
                          </span>
                        </div>

                        {/* Field action buttons */}
                        {field.verification_status === 'UNVERIFIED' && (
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleVerifyField(selectedDoc.id, field.id)}
                              disabled={actionLoading === field.id}
                              className="flex items-center gap-1 px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-[9px] font-bold rounded transition-all disabled:opacity-60"
                            >
                              <Shield className="h-2.5 w-2.5" /> Verify
                            </button>
                            <button
                              onClick={() => { setEditField({ id: field.id, value: field.extracted_value || '' }); setEditReason(''); }}
                              className="flex items-center gap-1 px-2 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-[9px] font-bold rounded transition-all"
                            >
                              <Edit3 className="h-2.5 w-2.5" /> Edit
                            </button>
                            <button
                              onClick={() => handleFlagField(selectedDoc.id, field.id)}
                              disabled={actionLoading === field.id}
                              className="flex items-center gap-1 px-2 py-1 bg-amber-600 hover:bg-amber-700 text-white text-[9px] font-bold rounded transition-all disabled:opacity-60"
                            >
                              <Flag className="h-2.5 w-2.5" /> Flag
                            </button>
                          </div>
                        )}

                        {/* Edit inline form */}
                        {editField?.id === field.id && (
                          <div className="space-y-2 pt-1">
                            <input
                              type="text"
                              value={editField.value}
                              onChange={e => setEditField({ id: field.id, value: e.target.value })}
                              className="w-full text-xs border border-indigo-300 rounded-lg px-2 py-1.5 outline-none focus:ring-1 focus:ring-indigo-500 bg-white"
                              placeholder="Enter corrected value..."
                            />
                            <input
                              type="text"
                              value={editReason}
                              onChange={e => setEditReason(e.target.value)}
                              className="w-full text-xs border border-slate-300 rounded-lg px-2 py-1.5 outline-none bg-white"
                              placeholder="Reason for edit (optional)..."
                            />
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleEditField(selectedDoc.id, field.id)}
                                disabled={actionLoading === field.id}
                                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-[9px] font-bold rounded disabled:opacity-60"
                              >
                                Save
                              </button>
                              <button
                                onClick={() => setEditField(null)}
                                className="px-3 py-1 text-[9px] font-bold text-slate-600 bg-white border border-slate-300 rounded"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}

                        {/* Field history */}
                        {field.history && field.history.length > 0 && (
                          <details className="text-[10px] text-slate-500">
                            <summary className="cursor-pointer font-bold">History ({field.history.length} changes)</summary>
                            <div className="mt-1 space-y-1 pl-2">
                              {field.history.map(h => (
                                <p key={h.id}>
                                  <span className="font-bold uppercase">{h.action}</span>
                                  {h.old_value && ` · was: ${h.old_value}`}
                                  {h.new_value && ` → ${h.new_value}`}
                                  {h.reason && ` (${h.reason})`}
                                </p>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
