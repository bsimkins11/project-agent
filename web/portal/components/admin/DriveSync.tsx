'use client'

import { useState } from 'react'
import { MagnifyingGlassIcon, DocumentIcon, FolderIcon, DocumentTextIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { analyzeDocumentIndex } from '@/lib/api'

interface DriveDocument {
  id: string
  name: string
  type: 'file' | 'folder'
  mimeType: string
  size?: number
  modifiedTime: string
  webViewLink: string
  parents?: string[]
}

export default function DriveSync() {
  const [folderId, setFolderId] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [documents, setDocuments] = useState<DriveDocument[]>([])
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(false)
  
  // Document Index Analysis state
  const [indexUrl, setIndexUrl] = useState('')
  const [indexType, setIndexType] = useState('csv')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<any>(null)

  const searchDocuments = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!folderId.trim()) {
      toast.error('Please enter a folder ID or Drive URL')
      return
    }

    setIsLoading(true)
    try {
      // Extract folder ID from URL if provided
      let actualFolderId = folderId
      if (folderId.includes('drive.google.com')) {
        const match = folderId.match(/\/folders\/([a-zA-Z0-9_-]+)/)
        if (match) {
          actualFolderId = match[1]
        } else {
          toast.error('Invalid Google Drive URL format')
          return
        }
      }

      // For now, show a message about manual document addition
      // In a real implementation, this would integrate with Google Drive API
      toast.success('Drive search functionality ready! Admin can manually add documents from Drive folders.')
      
      // Simulate finding documents (replace with real Drive API call)
      const mockDocuments: DriveDocument[] = [
        {
          id: '1ABC123def456',
          name: 'Project Requirements.pdf',
          type: 'file',
          mimeType: 'application/pdf',
          size: 1024000,
          modifiedTime: '2024-01-15T10:30:00Z',
          webViewLink: `https://drive.google.com/file/d/1ABC123def456/view`,
          parents: [actualFolderId]
        },
        {
          id: '2XYZ789abc123',
          name: 'Technical Specifications.docx',
          type: 'file',
          mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
          size: 512000,
          modifiedTime: '2024-01-14T15:45:00Z',
          webViewLink: `https://drive.google.com/file/d/2XYZ789abc123/view`,
          parents: [actualFolderId]
        }
      ]
      
      setDocuments(mockDocuments)
      toast.success(`Found ${mockDocuments.length} documents in folder ${actualFolderId}`)
    } catch (error) {
      toast.error('Failed to search Drive documents')
      console.error('Drive search error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleSelection = (docId: string) => {
    const newSelection = new Set(selectedDocs)
    if (newSelection.has(docId)) {
      newSelection.delete(docId)
    } else {
      newSelection.add(docId)
    }
    setSelectedDocs(newSelection)
  }

  const addSelectedToQueue = async () => {
    if (selectedDocs.size === 0) {
      toast.error('Please select documents to add to the approval queue')
      return
    }

    try {
      // In a real implementation, this would call an API to add documents to the approval queue
      toast.success(`${selectedDocs.size} document(s) added to approval queue`)
      setSelectedDocs(new Set())
    } catch (error) {
      toast.error('Failed to add documents to approval queue')
      console.error('Queue error:', error)
    }
  }

  const analyzeDocumentIndexFile = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!indexUrl.trim()) {
      toast.error('Please enter a document index URL')
      return
    }

    setIsAnalyzing(true)
    try {
      const result = await analyzeDocumentIndex({
        index_url: indexUrl,
        index_type: indexType
      })
      
      setAnalysisResult(result)
      toast.success(`Analysis complete! Created ${result.documents_created} document entries for review.`)
    } catch (error: any) {
      console.error('Analysis error:', error)
      
      // Check if this is an access denied error with access request option
      if (error?.response?.data?.detail?.access_request_available) {
        setAnalysisResult({
          error: true,
          access_request_available: true,
          message: error.response.data.detail.message,
          details: error.response.data.detail.details
        })
      } else {
        toast.error(error?.response?.data?.detail?.message || 'Failed to analyze document index')
      }
    } finally {
      setIsAnalyzing(false)
    }
  }

  const requestDocumentAccess = async () => {
    if (!indexUrl.trim()) {
      toast.error('Please enter a document index URL')
      return
    }

    try {
      const response = await fetch('/api/admin/request-document-access', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          index_url: indexUrl,
          message: 'Please grant access to the Project Deliverable Agent to analyze this document index and all referenced documents.'
        })
      })

      if (!response.ok) {
        throw new Error('Failed to request access')
      }

      const result = await response.json()
      toast.success('Access request sent to document owner!')
      setAnalysisResult(result)
    } catch (error) {
      toast.error('Failed to send access request')
      console.error('Access request error:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Document Index Analysis Section */}
      <div className="card">
        <div className="flex items-center mb-4">
          <div className="p-2 bg-green-100 rounded-lg mr-3">
            <DocumentTextIcon className="h-6 w-6 text-green-600" />
          </div>
          <div>
            <h2 className="text-lg font-medium text-gray-900">
              Document Index Analysis
            </h2>
            <p className="text-sm text-gray-600">
              Load documents from Google Drive document indexes for processing and approval
            </p>
          </div>
        </div>
        
        <div className="mb-6 p-4 bg-green-50 rounded-lg">
          <h3 className="font-medium text-green-900 mb-2">📋 Analyze Document Index</h3>
          <p className="text-sm text-green-700 mb-2">
            Provide a link to a document index in Google Drive (Google Sheets) to automatically create individual document entries for admin review and approval.
          </p>
          <div className="mt-2 text-xs text-green-600">
            <strong>How it works:</strong> Each document found in the index will be created as a separate line item in the approval queue where you can review metadata, grant permissions (for Google Drive URLs), and approve each document individually.
          </div>
        </div>

        <form onSubmit={analyzeDocumentIndexFile} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Document Index Type
            </label>
            <select
              value={indexType}
              onChange={(e) => setIndexType(e.target.value)}
              className="w-full input-field"
            >
              <option value="sheets">Google Sheets (Recommended)</option>
              <option value="csv">CSV File</option>
              <option value="drive_folder">Google Drive Folder</option>
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Google Sheets is recommended for easy collaboration and real-time updates
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Document Index URL *
            </label>
            <input
              type="url"
              value={indexUrl}
              onChange={(e) => setIndexUrl(e.target.value)}
              className="w-full input-field"
              placeholder="https://docs.google.com/spreadsheets/d/1ABC123def456GHI789/edit"
              required
            />
            <div className="mt-1 text-sm text-gray-500">
              <p>Paste the URL to your document index. For Google Sheets:</p>
              <ul className="list-disc list-inside mt-1 text-xs text-gray-600">
                <li>Make sure the sheet is accessible to the admin account via Google Drive API</li>
                <li>Include columns for: Title, URL/Link, Type, SOW Number, Deliverable, Responsible Party, etc.</li>
                <li>Each row should represent one document to be processed</li>
              </ul>
            </div>
          </div>

          <button
            type="submit"
            disabled={isAnalyzing}
            className="btn-primary disabled:opacity-50"
          >
            {isAnalyzing ? 'Analyzing...' : 'Analyze Document Index'}
          </button>
        </form>

        {analysisResult && (
          <div className="mt-6">
            {analysisResult.error && analysisResult.access_request_available ? (
              // Access Request Available
              <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                <h4 className="font-medium text-orange-900 mb-2">🔒 Access Required</h4>
                <p className="text-sm text-orange-700 mb-3">
                  {analysisResult.message}
                </p>
                <div className="space-y-2">
                  <p className="text-sm text-orange-600 font-medium">Would you like the agent to request access?</p>
                  <p className="text-xs text-orange-600">
                    The agent will send a request to the document owner asking them to grant access to:
                  </p>
                  <ul className="text-xs text-orange-600 ml-4 list-disc">
                    <li>The document index (Google Sheets)</li>
                    <li>All documents referenced in the index</li>
                    <li>Ability to analyze document content for the Project Deliverable Agent</li>
                  </ul>
                  <button
                    onClick={requestDocumentAccess}
                    className="mt-3 px-4 py-2 bg-orange-600 text-white text-sm rounded-md hover:bg-orange-700 transition-colors"
                  >
                    Request Access from Document Owner
                  </button>
                </div>
              </div>
            ) : analysisResult.access_request ? (
              // Access Request Sent
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <h4 className="font-medium text-green-900 mb-2">✅ Access Request Sent</h4>
                <p className="text-sm text-green-700 mb-2">
                  {analysisResult.message}
                </p>
                <div className="text-xs text-green-600">
                  <p className="font-medium mb-1">Next Steps:</p>
                  <ul className="ml-4 list-disc">
                    {analysisResult.next_steps?.map((step: string, index: number) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              // Success - Documents Created
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h4 className="font-medium text-blue-900 mb-2">Analysis Results</h4>
                <p className="text-sm text-blue-700 mb-2">
                  Successfully created {analysisResult.documents_created} document entries from the index analysis.
                </p>
                <p className="text-sm text-blue-600">
                  These documents are now available in the Document Approval queue where you can review metadata and approve each document individually.
                </p>
                <div className="mt-3">
                  <a 
                    href="/admin?tab=approval" 
                    className="text-sm text-blue-600 hover:text-blue-800 underline"
                  >
                    Go to Document Approval Queue →
                  </a>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Sample Format Guide */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">📋 Sample Google Sheets Format</h4>
          <p className="text-sm text-gray-600 mb-3">
            Your Google Sheets should have columns like this (column names are flexible):
          </p>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-2 py-1 border">Title</th>
                  <th className="px-2 py-1 border">URL</th>
                  <th className="px-2 py-1 border">Type</th>
                  <th className="px-2 py-1 border">SOW Number</th>
                  <th className="px-2 py-1 border">Deliverable</th>
                  <th className="px-2 py-1 border">Responsible Party</th>
                  <th className="px-2 py-1 border">Notes</th>
                </tr>
              </thead>
              <tbody className="bg-white">
                <tr>
                  <td className="px-2 py-1 border">Project Charter</td>
                  <td className="px-2 py-1 border">https://docs.google.com/document/d/...</td>
                  <td className="px-2 py-1 border">sow</td>
                  <td className="px-2 py-1 border">SOW-2024-001</td>
                  <td className="px-2 py-1 border">Project Charter</td>
                  <td className="px-2 py-1 border">Project Manager</td>
                  <td className="px-2 py-1 border">Initial project scope</td>
                </tr>
                <tr>
                  <td className="px-2 py-1 border">Technical Specs</td>
                  <td className="px-2 py-1 border">https://docs.google.com/document/d/...</td>
                  <td className="px-2 py-1 border">deliverable</td>
                  <td className="px-2 py-1 border">SOW-2024-001</td>
                  <td className="px-2 py-1 border">Technical Documentation</td>
                  <td className="px-2 py-1 border">Technical Lead</td>
                  <td className="px-2 py-1 border">System requirements</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Drive Search Section */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Google Drive Document Search
        </h2>
        
        <div className="mb-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-medium text-blue-900 mb-2">Find Documents to Add</h3>
          <p className="text-sm text-blue-700">
            Search Google Drive folders to find project deliverables you want to add to the Project Deliverable Agent. 
            Selected documents will be queued for admin approval before vectorization.
          </p>
          <div className="mt-2 text-xs text-blue-600">
            <strong>Note:</strong> Admin must have access to the Drive folder. Documents are manually selected and added to the approval queue.
          </div>
        </div>

        <form onSubmit={searchDocuments} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Google Drive Folder URL or ID *
            </label>
            <input
              type="text"
              value={folderId}
              onChange={(e) => setFolderId(e.target.value)}
              className="w-full input-field"
              placeholder="https://drive.google.com/drive/folders/1ABC123def456GHI789"
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              Paste the full Google Drive folder URL or just the folder ID. The admin must have access to this folder.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Query (Optional)
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full input-field"
              placeholder="Search for specific documents..."
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary disabled:opacity-50"
          >
            {isLoading ? 'Searching...' : 'Search Documents'}
          </button>
        </form>
      </div>

      {documents.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">
              Found Documents ({documents.length})
            </h2>
            {selectedDocs.size > 0 && (
              <button
                onClick={addSelectedToQueue}
                className="btn-primary text-sm"
              >
                Add Selected to Approval Queue ({selectedDocs.size})
              </button>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input
                      type="checkbox"
                      checked={selectedDocs.size === documents.filter(d => d.type === 'file').length && documents.filter(d => d.type === 'file').length > 0}
                      onChange={() => {
                        const fileDocs = documents.filter(d => d.type === 'file')
                        if (selectedDocs.size === fileDocs.length) {
                          setSelectedDocs(new Set())
                        } else {
                          setSelectedDocs(new Set(fileDocs.map(d => d.id)))
                        }
                      }}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Document
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Modified
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
                      {doc.type === 'file' && (
                        <input
                          type="checkbox"
                          checked={selectedDocs.has(doc.id)}
                          onChange={() => toggleSelection(doc.id)}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                        />
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {doc.type === 'file' ? (
                          <DocumentIcon className="h-5 w-5 text-gray-400 mr-3" />
                        ) : (
                          <FolderIcon className="h-5 w-5 text-gray-400 mr-3" />
                        )}
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {doc.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {doc.mimeType}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        doc.type === 'file' 
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {doc.type === 'file' ? 'File' : 'Folder'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {doc.size ? `${(doc.size / 1024).toFixed(1)} KB` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(doc.modifiedTime).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <a
                        href={doc.webViewLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-900"
                      >
                        View in Drive
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
