'use client'

import { useState } from 'react'
import { DocumentIcon, LinkIcon, CloudArrowUpIcon, XMarkIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { addDocumentUrl } from '@/lib/api'

interface AddDocumentUrlProps {
  docId: string
  docTitle: string
  onSuccess: () => void
  onCancel: () => void
}

export default function AddDocumentUrl({ docId, docTitle, onSuccess, onCancel }: AddDocumentUrlProps) {
  const [activeTab, setActiveTab] = useState<'url' | 'upload'>('url')
  const [url, setUrl] = useState('')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!url.trim()) {
      toast.error('Please enter a URL')
      return
    }

    setIsLoading(true)
    try {
      const result = await addDocumentUrl(docId, { source_uri: url })
      toast.success(result.message)
      onSuccess()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to add URL')
      console.error('Add URL error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!uploadFile) {
      toast.error('Please select a file to upload')
      return
    }

    setIsLoading(true)
    try {
      const result = await addDocumentUrl(docId, { upload_file: uploadFile })
      toast.success(result.message)
      onSuccess()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to upload file')
      console.error('Upload file error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Check file size (max 50MB)
      if (file.size > 50 * 1024 * 1024) {
        toast.error('File size must be less than 50MB')
        return
      }
      setUploadFile(file)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center">
            <DocumentIcon className="h-6 w-6 text-gray-400 mr-3" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">Add Document URL</h3>
              <p className="text-sm text-gray-500">{docTitle}</p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('url')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'url'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <LinkIcon className="h-4 w-4 inline mr-2" />
                Paste URL
              </button>
              <button
                onClick={() => setActiveTab('upload')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'upload'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <CloudArrowUpIcon className="h-4 w-4 inline mr-2" />
                Upload File
              </button>
            </nav>
          </div>

          {/* URL Tab */}
          {activeTab === 'url' && (
            <form onSubmit={handleUrlSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document URL *
                </label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full input-field"
                  placeholder="https://docs.google.com/document/d/... or https://example.com/file.pdf"
                  required
                />
                <p className="mt-1 text-sm text-gray-500">
                  Paste the URL to the document. Can be Google Drive, web URL, or any accessible link.
                </p>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={onCancel}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="btn-primary disabled:opacity-50"
                >
                  {isLoading ? 'Adding...' : 'Add URL'}
                </button>
              </div>
            </form>
          )}

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <form onSubmit={handleFileSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Upload Document *
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                      >
                        <span>Upload a file</span>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          className="sr-only"
                          onChange={handleFileChange}
                          accept=".pdf,.doc,.docx,.txt,.md,.html,.csv,.xlsx,.xls"
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">
                      PDF, DOC, DOCX, TXT, MD, HTML, CSV, XLSX up to 50MB
                    </p>
                  </div>
                </div>
                
                {uploadFile && (
                  <div className="mt-2 p-3 bg-green-50 rounded-md">
                    <div className="flex items-center">
                      <DocumentIcon className="h-5 w-5 text-green-400 mr-2" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-green-900">{uploadFile.name}</p>
                        <p className="text-xs text-green-700">
                          {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setUploadFile(null)}
                        className="text-green-400 hover:text-green-600"
                      >
                        <XMarkIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={onCancel}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !uploadFile}
                  className="btn-primary disabled:opacity-50"
                >
                  {isLoading ? 'Uploading...' : 'Upload File'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
