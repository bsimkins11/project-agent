'use client'

import { useState, useEffect } from 'react'
import { getDocumentsByCategory } from '@/lib/api'

interface Document {
  id: string
  title: string
  type: string
  upload_date: string
  size: number
  status: string
  doc_type: string
  created_by?: string
  webViewLink?: string
  web_view_link?: string
  approved_by?: string
  approved_date?: string
}

export default function TimelineDocuments() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    setLoading(true)
    try {
      const response = await getDocumentsByCategory('timeline')
      setDocuments(response.documents)
    } catch (error) {
      console.error('Failed to load timeline documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = (doc: Document) => {
    const link = doc.web_view_link || doc.webViewLink
    if (link) {
      window.open(link, '_blank')
    }
  }

  const handleDownload = (doc: Document) => {
    const link = doc.web_view_link || doc.webViewLink
    if (link) {
      window.open(link, '_blank')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Timeline Documents
          </h2>
          <p className="text-gray-600">
            Approved project timelines, schedules, and milestone documents.
          </p>
        </div>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : documents.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
            <div className="text-gray-500 mb-2">No timeline documents available</div>
            <p className="text-sm text-gray-400">Check back later for approved documents</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Available Documents ({documents.length})
              </h3>
            </div>
            <div className="divide-y divide-gray-200">
              {documents.map((doc) => (
                <div key={doc.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-gray-900 mb-1">
                        {doc.title}
                      </h4>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>Type: {doc.type}</span>
                        <span>Uploaded: {new Date(doc.upload_date).toLocaleDateString()}</span>
                        {doc.approved_by && (
                          <span>Approved by: {doc.approved_by}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handlePreview(doc)}
                        className="px-3 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100 transition-colors"
                      >
                        Preview
                      </button>
                      <button
                        onClick={() => handleDownload(doc)}
                        className="px-3 py-1 text-xs font-medium text-green-600 bg-green-50 rounded-md hover:bg-green-100 transition-colors"
                      >
                        Download
                      </button>
                      <button
                        onClick={() => handlePreview(doc)}
                        className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-50 rounded-md hover:bg-gray-100 transition-colors"
                      >
                        Go to Document
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}