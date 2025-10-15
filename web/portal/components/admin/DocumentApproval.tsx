'use client'

import { useState, useEffect } from 'react'
import { getPendingDocuments, approveDocument, rejectDocument, deleteDocument, updateDocumentMetadata, grantDocumentPermission, denyDocumentPermission, requestDocumentAccess } from '@/lib/api'
import toast from 'react-hot-toast'

interface PendingDocument {
  id: string
  title: string
  source_uri: string
  doc_type: string
  upload_date: string
  status: string
  created_by: string
  web_view_link: string
  sow_number?: string
  deliverable?: string
  responsible_party?: string
  deliverable_id?: string
  confidence?: string
  link?: string
  notes?: string
  from_index?: boolean
  index_source?: string
  requires_permission?: boolean
  permission_requested?: boolean
  permission_granted?: boolean
  permission_status?: string
  drive_file_id?: string
  drive_file_type?: string
}

export default function DocumentApproval() {
  const [documents, setDocuments] = useState<PendingDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDoc, setSelectedDoc] = useState<PendingDocument | null>(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [docToDelete, setDocToDelete] = useState<string | null>(null)
  const [rejectionReason, setRejectionReason] = useState('')
  const [showRejectDialog, setShowRejectDialog] = useState(false)
  const [docToReject, setDocToReject] = useState<string | null>(null)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [docToEdit, setDocToEdit] = useState<PendingDocument | null>(null)
  const [editForm, setEditForm] = useState({
    title: '',
    doc_type: '',
    sow_number: '',
    deliverable: '',
    responsible_party: '',
    deliverable_id: '',
    confidence: '',
    link: '',
    notes: ''
  })
  
  // Permission handling state
  const [showPermissionDialog, setShowPermissionDialog] = useState(false)
  const [docToPermission, setDocToPermission] = useState<PendingDocument | null>(null)
  const [permissionAction, setPermissionAction] = useState<'grant' | 'deny' | null>(null)
  const [permissionNotes, setPermissionNotes] = useState('')
  
  // Access request handling state
  const [showAccessRequestDialog, setShowAccessRequestDialog] = useState(false)
  const [docToAccessRequest, setDocToAccessRequest] = useState<PendingDocument | null>(null)
  const [accessRequestMessage, setAccessRequestMessage] = useState('')

  useEffect(() => {
    loadPendingDocuments()
  }, [])

  const loadPendingDocuments = async () => {
    setLoading(true)
    try {
      const response = await getPendingDocuments()
      setDocuments(response.documents)
    } catch (error) {
      toast.error('Failed to load pending documents')
      console.error('Pending documents error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (docId: string, docType: string) => {
    try {
      await approveDocument(docId, { doc_type: docType })
      toast.success('Document approved successfully')
      loadPendingDocuments()
    } catch (error) {
      toast.error('Failed to approve document')
      console.error('Approval error:', error)
    }
  }

  const handleReject = async (docId: string, reason: string) => {
    try {
      await rejectDocument(docId, { reason })
      toast.success('Document rejected')
      setShowRejectDialog(false)
      setRejectionReason('')
      setDocToReject(null)
      loadPendingDocuments()
    } catch (error) {
      toast.error('Failed to reject document')
      console.error('Rejection error:', error)
    }
  }

  const handleDelete = async (docId: string) => {
    try {
      await deleteDocument(docId)
      toast.success('Document deleted successfully')
      setShowDeleteConfirm(false)
      setDocToDelete(null)
      loadPendingDocuments()
    } catch (error) {
      toast.error('Failed to delete document')
      console.error('Deletion error:', error)
    }
  }

  const openRejectDialog = (docId: string) => {
    setDocToReject(docId)
    setShowRejectDialog(true)
  }

  const openDeleteConfirm = (docId: string) => {
    setDocToDelete(docId)
    setShowDeleteConfirm(true)
  }

  const openEditDialog = (doc: PendingDocument) => {
    setDocToEdit(doc)
    setEditForm({
      title: doc.title || '',
      doc_type: doc.doc_type || '',
      sow_number: doc.sow_number || '',
      deliverable: doc.deliverable || '',
      responsible_party: doc.responsible_party || '',
      deliverable_id: doc.deliverable_id || '',
      confidence: doc.confidence || '',
      link: doc.link || '',
      notes: doc.notes || ''
    })
    setShowEditDialog(true)
  }

  const handleMetadataUpdate = async () => {
    if (!docToEdit) return

    try {
      await updateDocumentMetadata(docToEdit.id, editForm)
      toast.success('Document metadata updated successfully')
      setShowEditDialog(false)
      setDocToEdit(null)
      loadPendingDocuments()
    } catch (error) {
      toast.error('Failed to update document metadata')
      console.error('Metadata update error:', error)
    }
  }

  const openPermissionDialog = (doc: PendingDocument, action: 'grant' | 'deny') => {
    setDocToPermission(doc)
    setPermissionAction(action)
    setPermissionNotes('')
    setShowPermissionDialog(true)
  }

  const handlePermissionAction = async () => {
    if (!docToPermission || !permissionAction) return

    try {
      if (permissionAction === 'grant') {
        await grantDocumentPermission(docToPermission.id, { notes: permissionNotes })
        toast.success('Permission granted successfully')
      } else {
        await denyDocumentPermission(docToPermission.id, { reason: permissionNotes })
        toast.success('Permission denied')
      }
      
      setShowPermissionDialog(false)
      setDocToPermission(null)
      setPermissionAction(null)
      setPermissionNotes('')
      loadPendingDocuments()
    } catch (error) {
      toast.error(`Failed to ${permissionAction} permission`)
      console.error('Permission action error:', error)
    }
  }

  const openAccessRequestDialog = (doc: PendingDocument) => {
    setDocToAccessRequest(doc)
    setAccessRequestMessage(`Please grant access to the Project Deliverable Agent service account to access the document: ${doc.title}`)
    setShowAccessRequestDialog(true)
  }

  const handleAccessRequest = async () => {
    if (!docToAccessRequest) return

    try {
      const result = await requestDocumentAccess(docToAccessRequest.id, {
        message: accessRequestMessage
      })
      
      toast.success('Access request sent to document owner!')
      setShowAccessRequestDialog(false)
      setDocToAccessRequest(null)
      setAccessRequestMessage('')
      loadPendingDocuments()
    } catch (error) {
      toast.error('Failed to send access request')
      console.error('Access request error:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Document Approval Queue ({documents.length} pending)
        </h2>
        <p className="text-sm text-gray-600">
          Review and approve documents before they become available to users and are vectorized for search.
        </p>
      </div>

      {/* Pending Documents Table */}
      <div className="card">
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-500 mb-2">No pending documents</div>
            <p className="text-sm text-gray-400">All documents have been reviewed</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Document
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uploaded By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Upload Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Permission Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {doc.title}
                        </div>
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {doc.source_uri}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {doc.doc_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {doc.created_by}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(doc.upload_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {doc.requires_permission ? (
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          doc.status === 'request_access' ? 'bg-red-100 text-red-800' :
                          doc.status === 'access_requested' ? 'bg-yellow-100 text-yellow-800' :
                          doc.status === 'access_granted' ? 'bg-blue-100 text-blue-800' :
                          doc.status === 'awaiting_processing' ? 'bg-purple-100 text-purple-800' :
                          doc.status === 'document_processed' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {doc.status === 'request_access' ? 'Request Access' :
                           doc.status === 'access_requested' ? 'Access Requested' :
                           doc.status === 'access_granted' ? 'Access Granted' :
                           doc.status === 'awaiting_processing' ? 'Awaiting Processing' :
                           doc.status === 'document_processed' ? 'Document Processed' :
                           'Unknown Status'}
                        </span>
                      ) : (
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          doc.status === 'uploaded' ? 'bg-blue-100 text-blue-800' :
                          doc.status === 'awaiting_processing' ? 'bg-purple-100 text-purple-800' :
                          doc.status === 'document_processed' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {doc.status === 'uploaded' ? 'Ready for Approval' :
                           doc.status === 'awaiting_processing' ? 'Awaiting Processing' :
                           doc.status === 'document_processed' ? 'Document Processed' :
                           'No Permission Required'}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      <button
                        onClick={() => openEditDialog(doc)}
                        className="text-blue-600 hover:text-blue-900 font-medium"
                      >
                        Edit
                      </button>
                      
                      {/* Access request for documents in request_access status */}
                      {doc.requires_permission && doc.status === 'request_access' && (
                        <button
                          onClick={() => openAccessRequestDialog(doc)}
                          className="text-orange-600 hover:text-orange-900 font-medium"
                        >
                          Request Access
                        </button>
                      )}
                      
                      {/* Grant permission for documents in access_requested status */}
                      {doc.requires_permission && doc.status === 'access_requested' && (
                        <button
                          onClick={() => openPermissionDialog(doc, 'grant')}
                          className="text-green-600 hover:text-green-900 font-medium"
                        >
                          Grant Permission
                        </button>
                      )}
                      
                      {/* Approve for processing for documents in access_granted status */}
                      {doc.requires_permission && doc.status === 'access_granted' && (
                        <button
                          onClick={() => handleApprove(doc.id, doc.doc_type)}
                          className="text-blue-600 hover:text-blue-900 font-medium"
                        >
                          Approve for Processing
                        </button>
                      )}
                      
                      {/* Regular approval actions for documents ready for approval (no permission required) */}
                      {!doc.requires_permission && doc.status === 'uploaded' && (
                        <button
                          onClick={() => handleApprove(doc.id, doc.doc_type)}
                          className="text-green-600 hover:text-green-900 font-medium"
                        >
                          Approve
                        </button>
                      )}
                      
                      {/* Processing status for documents awaiting processing */}
                      {doc.status === 'awaiting_processing' && (
                        <span className="text-purple-600 font-medium">
                          Processing...
                        </span>
                      )}
                      
                      {/* Completed status for processed documents */}
                      {doc.status === 'document_processed' && (
                        <span className="text-green-600 font-medium">
                          ✓ Processed
                        </span>
                      )}
                      
                      <button
                        onClick={() => openDeleteConfirm(doc.id)}
                        className="text-red-600 hover:text-red-900 font-medium"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Rejection Dialog */}
      {showRejectDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Reject Document
            </h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reason for rejection
              </label>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder="Enter reason for rejection..."
              />
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowRejectDialog(false)
                  setRejectionReason('')
                  setDocToReject(null)
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => docToReject && handleReject(docToReject, rejectionReason)}
                className="flex-1 px-4 py-2 bg-yellow-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-yellow-700"
              >
                Reject Document
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  Delete Document
                </h3>
              </div>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-3">
                Are you sure you want to permanently delete this document? This action cannot be undone.
              </p>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-800 font-medium">
                  ⚠️ This will permanently remove the document from the repository.
                </p>
              </div>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowDeleteConfirm(false)
                  setDocToDelete(null)
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => docToDelete && handleDelete(docToDelete)}
                className="flex-1 px-4 py-2 bg-red-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-red-700"
              >
                Delete Permanently
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Metadata Edit Dialog */}
      {showEditDialog && docToEdit && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Edit Document Metadata
              </h3>
              <button
                onClick={() => {
                  setShowEditDialog(false)
                  setDocToEdit(null)
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="mb-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Document:</strong> {docToEdit.title}
              </p>
              <p className="text-sm text-blue-700">
                <strong>Source:</strong> {docToEdit.source_uri}
              </p>
              {docToEdit.from_index && (
                <p className="text-sm text-blue-700">
                  <strong>From Index:</strong> {docToEdit.index_source}
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Title *
                </label>
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) => setEditForm(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full input-field"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Type *
                </label>
                <select
                  value={editForm.doc_type}
                  onChange={(e) => setEditForm(prev => ({ ...prev, doc_type: e.target.value }))}
                  className="w-full input-field"
                  required
                >
                  <option value="">Select Type</option>
                  <option value="sow">SOW</option>
                  <option value="timeline">Timeline</option>
                  <option value="deliverable">Deliverable</option>
                  <option value="misc">Miscellaneous</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  SOW Number
                </label>
                <input
                  type="text"
                  value={editForm.sow_number}
                  onChange={(e) => setEditForm(prev => ({ ...prev, sow_number: e.target.value }))}
                  className="w-full input-field"
                  placeholder="e.g., SOW-2024-001"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Deliverable
                </label>
                <input
                  type="text"
                  value={editForm.deliverable}
                  onChange={(e) => setEditForm(prev => ({ ...prev, deliverable: e.target.value }))}
                  className="w-full input-field"
                  placeholder="e.g., Project Charter"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Responsible Party
                </label>
                <input
                  type="text"
                  value={editForm.responsible_party}
                  onChange={(e) => setEditForm(prev => ({ ...prev, responsible_party: e.target.value }))}
                  className="w-full input-field"
                  placeholder="e.g., Project Manager"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Deliverable ID
                </label>
                <input
                  type="text"
                  value={editForm.deliverable_id}
                  onChange={(e) => setEditForm(prev => ({ ...prev, deliverable_id: e.target.value }))}
                  className="w-full input-field"
                  placeholder="e.g., DEL-CHARTER-001"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Confidence Level
                </label>
                <select
                  value={editForm.confidence}
                  onChange={(e) => setEditForm(prev => ({ ...prev, confidence: e.target.value }))}
                  className="w-full input-field"
                >
                  <option value="">Select Confidence</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Link
                </label>
                <input
                  type="url"
                  value={editForm.link}
                  onChange={(e) => setEditForm(prev => ({ ...prev, link: e.target.value }))}
                  className="w-full input-field"
                  placeholder="https://docs.google.com/document/d/..."
                />
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Notes
              </label>
              <textarea
                value={editForm.notes}
                onChange={(e) => setEditForm(prev => ({ ...prev, notes: e.target.value }))}
                className="w-full input-field"
                rows={3}
                placeholder="Additional notes about this document..."
              />
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowEditDialog(false)
                  setDocToEdit(null)
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleMetadataUpdate}
                className="flex-1 px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700"
              >
                Update Metadata
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Permission Action Dialog */}
      {showPermissionDialog && docToPermission && permissionAction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg className={`h-6 w-6 ${permissionAction === 'grant' ? 'text-green-600' : 'text-red-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {permissionAction === 'grant' ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  )}
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  {permissionAction === 'grant' ? 'Grant Permission' : 'Deny Permission'}
                </h3>
              </div>
            </div>
            
            <div className="mb-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Document:</strong> {docToPermission.title}
              </p>
              <p className="text-sm text-blue-700">
                <strong>Source:</strong> {docToPermission.source_uri}
              </p>
              {docToPermission.drive_file_type && (
                <p className="text-sm text-blue-700">
                  <strong>File Type:</strong> {docToPermission.drive_file_type}
                </p>
              )}
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {permissionAction === 'grant' ? 'Notes (Optional)' : 'Reason for Denial'}
              </label>
              <textarea
                value={permissionNotes}
                onChange={(e) => setPermissionNotes(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                rows={3}
                placeholder={permissionAction === 'grant' ? 'Add any notes about granting permission...' : 'Enter reason for denying permission...'}
              />
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowPermissionDialog(false)
                  setDocToPermission(null)
                  setPermissionAction(null)
                  setPermissionNotes('')
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handlePermissionAction}
                className={`flex-1 px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white ${
                  permissionAction === 'grant' 
                    ? 'bg-green-600 hover:bg-green-700' 
                    : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {permissionAction === 'grant' ? 'Grant Permission' : 'Deny Permission'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Access Request Dialog */}
      {showAccessRequestDialog && docToAccessRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">
                  Request Document Access
                </h3>
              </div>
            </div>
            
            <div className="mb-4 p-3 bg-orange-50 rounded-lg">
              <p className="text-sm text-orange-800">
                <strong>Document:</strong> {docToAccessRequest.title}
              </p>
              <p className="text-sm text-orange-700">
                <strong>Source:</strong> {docToAccessRequest.source_uri}
              </p>
              {docToAccessRequest.drive_file_id && (
                <p className="text-sm text-orange-700">
                  <strong>Drive File ID:</strong> {docToAccessRequest.drive_file_id}
                </p>
              )}
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Access Request Message
              </label>
              <textarea
                value={accessRequestMessage}
                onChange={(e) => setAccessRequestMessage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-orange-500 focus:border-orange-500"
                rows={4}
                placeholder="Enter your message to the document owner..."
              />
              <p className="mt-1 text-xs text-gray-500">
                This message will be sent to the document owner along with the access request for the Project Deliverable Agent service account.
              </p>
            </div>

            <div className="mb-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800 font-medium mb-1">What happens next:</p>
              <ul className="text-xs text-blue-700 ml-4 list-disc">
                <li>The document owner will receive a notification about this access request</li>
                <li>Once access is granted, the document status will be updated automatically</li>
                <li>You can monitor the document status in the approval queue</li>
                <li>The service account will be able to access and vectorize the document content</li>
              </ul>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowAccessRequestDialog(false)
                  setDocToAccessRequest(null)
                  setAccessRequestMessage('')
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAccessRequest}
                className="flex-1 px-4 py-2 bg-orange-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-orange-700"
              >
                Send Access Request
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}