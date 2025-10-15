'use client'

import { useState, useEffect } from 'react'
import { DocumentType, MediaType, DocumentStatus, InventoryItem } from '@/types'
import { getInventory, deleteDocument, requestDocumentAccess, approveDocument, submitForProcessing, processDocument, rejectDocument } from '@/lib/api'
import toast from 'react-hot-toast'
import AddDocumentUrl from './AddDocumentUrl'
import ClassificationModal from './ClassificationModal'

export default function DocumentInventory() {
  const [items, setItems] = useState<InventoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [docToDelete, setDocToDelete] = useState<string | null>(null)
  const [showAddUrl, setShowAddUrl] = useState(false)
  const [docToAddUrl, setDocToAddUrl] = useState<{id: string, title: string} | null>(null)
  const [showClassificationModal, setShowClassificationModal] = useState(false)
  const [docToClassify, setDocToClassify] = useState<{id: string, title: string, currentCategory: string} | null>(null)
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    page_size: 20,
    total_pages: 1
  })
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 20,
    doc_type: '',
    media_type: '',
    status: '',
    q: '',
  })

  useEffect(() => {
    loadInventory()
  }, [filters])
  
  useEffect(() => {
    // Listen for project changes from header selector
    const handleProjectChange = (event: any) => {
      const projectId = event.detail?.projectId || ''
      // Update filters to include selected project
      setFilters(prev => ({ ...prev, page: 1 }))
      loadInventory(projectId)
    }
    
    window.addEventListener('projectChanged', handleProjectChange)
    return () => window.removeEventListener('projectChanged', handleProjectChange)
  }, [])

  const loadInventory = async (projectIdOverride?: string) => {
    setLoading(true)
    try {
      // Ensure auth token is set before making API call
      if (!localStorage.getItem('auth_token')) {
        localStorage.setItem('auth_token', 'test-token')
      }
      
      // Get selected project from localStorage or parameter
      const selectedProjectId = projectIdOverride !== undefined 
        ? projectIdOverride 
        : localStorage.getItem('selected_project_id') || ''
      
      // Add project_id to filters if selected
      const queryParams = { ...filters }
      if (selectedProjectId) {
        (queryParams as any).project_id = selectedProjectId
      }
      
      const response = await getInventory(queryParams)
      setItems(response.items)
      setPagination({
        total: response.total,
        page: response.page,
        page_size: response.page_size,
        total_pages: response.total_pages
      })
    } catch (error) {
      toast.error('Failed to load inventory')
      console.error('Inventory error:', error)
      console.error('Error details:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateFilter = (key: string, value: string) => {
    // Only reset to page 1 when changing filters other than page
    if (key === 'page') {
      setFilters(prev => ({ ...prev, page: parseInt(value) }))
    } else {
      setFilters(prev => ({ ...prev, [key]: value, page: 1 }))
    }
  }


  const handleDelete = async (docId: string) => {
    try {
      await deleteDocument(docId)
      toast.success('Document deleted successfully')
      setShowDeleteConfirm(false)
      setDocToDelete(null)
      loadInventory()
    } catch (error) {
      toast.error('Failed to delete document')
      console.error('Deletion error:', error)
    }
  }

  const openDeleteConfirm = (docId: string) => {
    setDocToDelete(docId)
    setShowDeleteConfirm(true)
  }

  const openAddUrl = (docId: string, docTitle: string) => {
    setDocToAddUrl({ id: docId, title: docTitle })
    setShowAddUrl(true)
  }

  const handleAddUrlSuccess = () => {
    setShowAddUrl(false)
    setDocToAddUrl(null)
    loadInventory() // Reload to show updated status
  }

  const handleAddUrlCancel = () => {
    setShowAddUrl(false)
    setDocToAddUrl(null)
  }

  const openClassificationModal = (docId: string, docTitle: string, currentCategory: string) => {
    setDocToClassify({ id: docId, title: docTitle, currentCategory })
    setShowClassificationModal(true)
  }

  const handleClassificationSuccess = () => {
    setShowClassificationModal(false)
    setDocToClassify(null)
    loadInventory() // Reload to show updated classification
  }

  const handleClassificationCancel = () => {
    setShowClassificationModal(false)
    setDocToClassify(null)
  }

  const handleRequestAccess = async (docId: string) => {
    try {
      await requestDocumentAccess(docId, { share_with_team: true })
      toast.success('Access request sent to document owner')
      loadInventory()
    } catch (error) {
      toast.error('Failed to request document access')
      console.error('Request access error:', error)
    }
  }

  const handleApprove = async (docId: string) => {
    try {
      await approveDocument(docId)
      toast.success('Document approved successfully')
      loadInventory()
    } catch (error) {
      toast.error('Failed to approve document')
      console.error('Approval error:', error)
    }
  }

  const handleSubmitForProcessing = async (docId: string) => {
    try {
      await submitForProcessing(docId)
      toast.success('Document submitted for processing')
      loadInventory()
    } catch (error) {
      toast.error('Failed to submit document for processing')
      console.error('Submit processing error:', error)
    }
  }

  const handleProcess = async (docId: string) => {
    try {
      await processDocument(docId)
      toast.success('Document processing started')
      loadInventory()
    } catch (error) {
      toast.error('Failed to process document')
      console.error('Processing error:', error)
    }
  }

  const handleReject = async (docId: string, reason: string) => {
    try {
      await rejectDocument(docId, { reason })
      toast.success('Document rejected')
      loadInventory()
    } catch (error) {
      toast.error('Failed to reject document')
      console.error('Rejection error:', error)
    }
  }

  const getAvailableActions = (item: InventoryItem) => {
    const actions = []
    
    switch (item.status) {
      case 'uploaded':
        actions.push(
          <button
            key="approve"
            onClick={() => handleApprove(item.doc_id)}
            className="text-green-600 hover:text-green-800 text-xs underline mr-2"
          >
            Approve
          </button>
        )
        actions.push(
          <button
            key="reject"
            onClick={() => {
              const reason = prompt('Reason for rejection:')
              if (reason) handleReject(item.doc_id, reason)
            }}
            className="text-red-600 hover:text-red-800 text-xs underline mr-2"
          >
            Reject
          </button>
        )
        break
        
      case 'request_access':
        actions.push(
          <button
            key="request-access"
            onClick={() => handleRequestAccess(item.doc_id)}
            className="text-blue-600 hover:text-blue-800 text-xs underline mr-2"
          >
            Request Access
          </button>
        )
        break
        
      case 'access_granted':
      case 'awaiting_approval':
        actions.push(
          <button
            key="approve"
            onClick={() => handleApprove(item.doc_id)}
            className="text-green-600 hover:text-green-800 text-xs underline mr-2"
          >
            Approve
          </button>
        )
        break
        
      case 'approved':
        actions.push(
          <button
            key="submit-processing"
            onClick={() => handleSubmitForProcessing(item.doc_id)}
            className="text-blue-600 hover:text-blue-800 text-xs underline mr-2"
          >
            Submit for Processing
          </button>
        )
        break
        
      case 'processing_requested':
        actions.push(
          <button
            key="process"
            onClick={() => handleProcess(item.doc_id)}
            className="text-purple-600 hover:text-purple-800 text-xs underline mr-2"
          >
            Process Now
          </button>
        )
        break
        
      case 'processing':
        actions.push(
          <span key="processing" className="text-gray-500 text-xs">
            Processing...
          </span>
        )
        break
        
      case 'processed':
        actions.push(
          <span key="processed" className="text-green-500 text-xs">
            ✓ Processed
          </span>
        )
        break
        
      case 'quarantined':
        actions.push(
          <span key="quarantined" className="text-red-500 text-xs">
            Quarantined
          </span>
        )
        break
        
      case 'failed':
        actions.push(
          <button
            key="retry"
            onClick={() => handleProcess(item.doc_id)}
            className="text-orange-600 hover:text-orange-800 text-xs underline mr-2"
          >
            Retry
          </button>
        )
        break
    }
    
    return actions
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              value={filters.q}
              onChange={(e) => updateFilter('q', e.target.value)}
              placeholder="Search documents..."
              className="w-full input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Document Type
            </label>
            <select
              value={filters.doc_type}
              onChange={(e) => updateFilter('doc_type', e.target.value)}
              className="w-full input-field"
            >
              <option value="">All Types</option>
              <option value="sow">SOW</option>
              <option value="timeline">Timeline</option>
              <option value="deliverable">Deliverable</option>
              <option value="misc">Miscellaneous</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Media Type
            </label>
            <select
              value={filters.media_type}
              onChange={(e) => updateFilter('media_type', e.target.value)}
              className="w-full input-field"
            >
              <option value="">All Media</option>
              <option value="document">Document</option>
              <option value="image">Image</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => updateFilter('status', e.target.value)}
              className="w-full input-field"
            >
              <option value="">All Statuses</option>
              <option value="uploaded">Uploaded</option>
              <option value="request_access">Request Access</option>
              <option value="access_requested">Access Requested</option>
              <option value="access_granted">Access Granted</option>
              <option value="awaiting_approval">Awaiting Approval</option>
              <option value="approved">Approved</option>
              <option value="processing_requested">Processing Requested</option>
              <option value="processing">Processing</option>
              <option value="processed">Processed</option>
              <option value="quarantined">Quarantined</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-medium text-gray-900">
            Document Inventory ({pagination.total} documents)
          </h2>
          <button className="btn-secondary">
            Export CSV
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
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
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {items.map((item) => (
                  <tr key={item.doc_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {item.thumbnail && (
                          <img
                            src={item.thumbnail}
                            alt={item.title}
                            className="h-10 w-10 object-cover rounded mr-3"
                          />
                        )}
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {item.title}
                          </div>
                          <div className="text-sm text-gray-500">
                            {item.doc_id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {item.doc_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        item.status === 'processed' ? 'bg-green-100 text-green-800' :
                        item.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                        item.status === 'processing' ? 'bg-purple-100 text-purple-800' :
                        item.status === 'processing_requested' ? 'bg-yellow-100 text-yellow-800' :
                        item.status === 'awaiting_approval' ? 'bg-orange-100 text-orange-800' :
                        item.status === 'access_granted' ? 'bg-blue-100 text-blue-800' :
                        item.status === 'access_requested' ? 'bg-orange-100 text-orange-800' :
                        item.status === 'request_access' ? 'bg-red-100 text-red-800' :
                        item.status === 'uploaded' ? 'bg-gray-100 text-gray-800' :
                        item.status === 'quarantined' ? 'bg-red-100 text-red-800' :
                        item.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {item.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          item.doc_type === 'sow' ? 'bg-blue-100 text-blue-800' :
                          item.doc_type === 'timeline' ? 'bg-green-100 text-green-800' :
                          item.doc_type === 'deliverable' ? 'bg-purple-100 text-purple-800' :
                          item.doc_type === 'misc' ? 'bg-gray-100 text-gray-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {item.doc_type || 'Unclassified'}
                        </span>
                        <button
                          onClick={() => openClassificationModal(item.doc_id, item.title, item.doc_type)}
                          className="text-blue-600 hover:text-blue-800 text-xs underline"
                        >
                          Edit
                        </button>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {item.created_by}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                         <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                           {/* Workflow Actions */}
                           <div className="flex flex-wrap gap-1">
                             {getAvailableActions(item)}
                           </div>
                           
                           {/* Additional Actions */}
                           <div className="flex flex-wrap gap-1 mt-1">
                             {/* Show Add URL button for documents that need URL */}
                             {!item.thumbnail && (
                               <button
                                 onClick={() => openAddUrl(item.doc_id, item.title)}
                                 className="text-blue-600 hover:text-blue-900 text-xs underline"
                               >
                                 Add URL
                               </button>
                             )}
                             
                             {/* View button for processed documents */}
                             {item.thumbnail && (
                               <a
                                 href={`/documents/${item.doc_id}`}
                                 className="text-primary-600 hover:text-primary-900 text-xs underline"
                               >
                                 View
                               </a>
                             )}
                             
                             {/* Delete button */}
                             <button
                               onClick={() => openDeleteConfirm(item.doc_id)}
                               className="text-red-600 hover:text-red-900 text-xs underline"
                             >
                               Delete
                             </button>
                           </div>
                         </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Controls */}
        {pagination.total_pages > 1 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => updateFilter('page', Math.max(1, pagination.page - 1).toString())}
                disabled={pagination.page === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => updateFilter('page', Math.min(pagination.total_pages, pagination.page + 1).toString())}
                disabled={pagination.page === pagination.total_pages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing <span className="font-medium">{(pagination.page - 1) * pagination.page_size + 1}</span> to{' '}
                  <span className="font-medium">
                    {Math.min(pagination.page * pagination.page_size, pagination.total)}
                  </span>{' '}
                  of <span className="font-medium">{pagination.total}</span> results
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                  <button
                    onClick={() => updateFilter('page', Math.max(1, pagination.page - 1).toString())}
                    disabled={pagination.page === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Previous</span>
                    ←
                  </button>
                  
                  {/* Page numbers */}
                  {Array.from({ length: pagination.total_pages }, (_, i) => {
                    const pageNum = i + 1;
                    
                    // Show first 3 pages, last 3 pages, and current page with neighbors
                    const shouldShow = 
                      pageNum <= 3 || // First 3 pages
                      pageNum > pagination.total_pages - 3 || // Last 3 pages
                      Math.abs(pageNum - pagination.page) <= 1; // Current page ± 1
                    
                    if (!shouldShow) {
                      // Show ellipsis
                      if (pageNum === 4 && pagination.page > 5) {
                        return <span key={pageNum} className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">...</span>
                      }
                      if (pageNum === pagination.total_pages - 3 && pagination.page < pagination.total_pages - 4) {
                        return <span key={pageNum} className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">...</span>
                      }
                      return null;
                    }
                    
                    const isCurrentPage = pageNum === pagination.page;
                    return (
                      <button
                        key={pageNum}
                        onClick={() => updateFilter('page', pageNum.toString())}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          isCurrentPage
                            ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  
                  <button
                    onClick={() => updateFilter('page', Math.min(pagination.total_pages, pagination.page + 1).toString())}
                    disabled={pagination.page === pagination.total_pages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Next</span>
                    →
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

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
                  ⚠️ This will permanently remove the document from the repository and make it unavailable to users.
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

      {/* Add Document URL Modal */}
      {showAddUrl && docToAddUrl && (
        <AddDocumentUrl
          docId={docToAddUrl.id}
          docTitle={docToAddUrl.title}
          onSuccess={handleAddUrlSuccess}
          onCancel={handleAddUrlCancel}
        />
      )}

      {/* Classification Modal */}
      {showClassificationModal && docToClassify && (
        <ClassificationModal
          docId={docToClassify.id}
          docTitle={docToClassify.title}
          currentCategory={docToClassify.currentCategory}
          onSuccess={handleClassificationSuccess}
          onCancel={handleClassificationCancel}
        />
      )}
    </div>
  )
}
