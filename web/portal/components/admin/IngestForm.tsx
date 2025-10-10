'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { ingestDocument, ingestCSV, syncGoogleDrive, checkDuplicateDocument } from '@/lib/api'
import toast from 'react-hot-toast'

interface IngestFormData {
  title: string
  doc_type: string
  source_uri: string
  tags: string
  owner?: string
  version?: string
  sow_number?: string
  deliverable?: string
  responsible_party?: string
  deliverable_id?: string
  confidence?: string
  link?: string
  notes?: string
}

export default function IngestForm() {
  const [activeTab, setActiveTab] = useState<'single' | 'bulk' | 'sheets'>('single')
  const [isLoading, setIsLoading] = useState(false)
  const [duplicateCheck, setDuplicateCheck] = useState<{
    isDuplicate: boolean
    existingDocument?: any
    showOverwriteDialog: boolean
  }>({
    isDuplicate: false,
    showOverwriteDialog: false
  })

  const { register, handleSubmit, reset, getValues, formState: { errors } } = useForm<IngestFormData>()

  const onSubmitSingle = async (data: IngestFormData) => {
    setIsLoading(true)
    try {
      // First check for duplicates
      const duplicateResult = await checkDuplicateDocument({
        title: data.title,
        source_uri: data.source_uri
      })

      if (duplicateResult.is_duplicate) {
        setDuplicateCheck({
          isDuplicate: true,
          existingDocument: duplicateResult.existing_document,
          showOverwriteDialog: true
        })
        setIsLoading(false)
        return
      }

      // No duplicate found, proceed with ingestion
      await proceedWithIngestion(data)
    } catch (error) {
      toast.error('Failed to check for duplicates')
      console.error('Duplicate check error:', error)
      setIsLoading(false)
    }
  }

  const proceedWithIngestion = async (data: IngestFormData, overwrite = false) => {
    try {
      const tags = data.tags.split(',').map(tag => tag.trim()).filter(Boolean)
      const result = await ingestDocument({
        title: data.title,
        doc_type: data.doc_type,
        source_uri: data.source_uri,
        tags,
        owner: data.owner,
        version: data.version,
        overwrite, // Add overwrite flag
        sow_number: data.sow_number,
        deliverable: data.deliverable,
        responsible_party: data.responsible_party,
        deliverable_id: data.deliverable_id,
        confidence: data.confidence,
        link: data.link,
        notes: data.notes
      })
      
      toast.success(result.message)
      reset()
      setDuplicateCheck({
        isDuplicate: false,
        showOverwriteDialog: false
      })
    } catch (error) {
      toast.error('Failed to ingest document')
      console.error('Ingest error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleOverwriteConfirm = async (data: IngestFormData) => {
    setDuplicateCheck({
      isDuplicate: false,
      showOverwriteDialog: false
    })
    await proceedWithIngestion(data, true)
  }

  const handleOverwriteCancel = () => {
    setDuplicateCheck({
      isDuplicate: false,
      showOverwriteDialog: false
    })
    setIsLoading(false)
  }

  const onSubmitBulk = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const file = formData.get('csvFile') as File
    
    if (!file) {
      toast.error('Please select a CSV file')
      return
    }

    setIsLoading(true)
    try {
      const result = await ingestCSV(file)
      toast.success(result.message)
    } catch (error) {
      toast.error('Failed to ingest CSV')
      console.error('CSV ingest error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const onSubmitSheets = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const folderIds = formData.get('folderIds') as string
    const recursive = formData.get('recursive') === 'on'
    
    if (!folderIds.trim()) {
      toast.error('Please enter at least one folder ID')
      return
    }

    setIsLoading(true)
    try {
      const folderIdArray = folderIds.split(',').map(id => id.trim()).filter(Boolean)
      const result = await syncGoogleDrive({
        folder_ids: folderIdArray,
        recursive
      })
      toast.success(`Sync started: ${result.folders_processed} folders, ${result.files_found} files found`)
    } catch (error) {
      toast.error('Failed to sync Google Drive')
      console.error('Google Drive sync error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('single')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'single'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Single Document
          </button>
          <button
            onClick={() => setActiveTab('bulk')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'bulk'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Bulk Upload (CSV)
          </button>
          <button
            onClick={() => setActiveTab('sheets')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'sheets'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Google Sheets/Drive
          </button>
        </nav>
      </div>

      {/* Single Document Form */}
      {activeTab === 'single' && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Ingest Single Document
          </h2>
          <form onSubmit={handleSubmit(onSubmitSingle)} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Title *
                </label>
                <input
                  {...register('title', { required: 'Title is required' })}
                  className="w-full input-field"
                  placeholder="Enter document title"
                />
                {errors.title && (
                  <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Document Type *
                </label>
                <select
                  {...register('doc_type', { required: 'Document type is required' })}
                  className="w-full input-field"
                >
                  <option value="">Select type</option>
                  <option value="sow">Statement of Work</option>
                  <option value="timeline">Timeline</option>
                  <option value="deliverable">Deliverable</option>
                  <option value="misc">Miscellaneous</option>
                </select>
                {errors.doc_type && (
                  <p className="mt-1 text-sm text-red-600">{errors.doc_type.message}</p>
                )}
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Source URI *
                </label>
                <input
                  {...register('source_uri', { required: 'Source URI is required' })}
                  className="w-full input-field"
                  placeholder="gs://bucket/file.pdf or https://example.com/file.pdf"
                />
                {errors.source_uri && (
                  <p className="mt-1 text-sm text-red-600">{errors.source_uri.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags (comma-separated)
                </label>
                <input
                  {...register('tags')}
                  className="w-full input-field"
                  placeholder="tag1, tag2, tag3"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Owner
                </label>
                <input
                  {...register('owner')}
                  className="w-full input-field"
                  placeholder="owner@transparent.partners"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Version
                </label>
                <input
                  {...register('version')}
                  className="w-full input-field"
                  placeholder="1.0"
                />
              </div>
            </div>

            {/* Additional Metadata Fields */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="text-sm font-medium text-blue-900 mb-3">
                Deliverable Metadata (Optional)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    SOW #
                  </label>
                  <input
                    {...register('sow_number')}
                    className="w-full input-field"
                    placeholder="SOW-2024-001"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Deliverable
                  </label>
                  <input
                    {...register('deliverable')}
                    className="w-full input-field"
                    placeholder="Phase 1 Report"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Responsible Party
                  </label>
                  <input
                    {...register('responsible_party')}
                    className="w-full input-field"
                    placeholder="John Smith"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Deliverable ID
                  </label>
                  <input
                    {...register('deliverable_id')}
                    className="w-full input-field"
                    placeholder="DEL-001"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Confidence
                  </label>
                  <select
                    {...register('confidence')}
                    className="w-full input-field"
                  >
                    <option value="">Select confidence level</option>
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
                    {...register('link')}
                    className="w-full input-field"
                    placeholder="https://example.com/document"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Leave blank if document is not a URL link
                  </p>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Notes
                  </label>
                  <textarea
                    {...register('notes')}
                    className="w-full input-field"
                    rows={3}
                    placeholder="Additional notes or context about this document..."
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary disabled:opacity-50"
            >
              {isLoading ? 'Checking...' : 'Ingest Document'}
            </button>
          </form>

          {/* Duplicate Warning Dialog */}
          {duplicateCheck.showOverwriteDialog && duplicateCheck.existingDocument && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                <div className="flex items-center mb-4">
                  <div className="flex-shrink-0">
                    <svg className="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-lg font-medium text-gray-900">
                      Document Already Exists
                    </h3>
                  </div>
                </div>
                
                <div className="mb-4">
                  <p className="text-sm text-gray-600 mb-3">
                    A document with the same title or source URI already exists:
                  </p>
                  
                  <div className="bg-gray-50 rounded-lg p-3 mb-3">
                    <div className="text-sm">
                      <div className="font-medium text-gray-900 mb-1">
                        {duplicateCheck.existingDocument.title}
                      </div>
                      <div className="text-gray-600 text-xs">
                        <div>Type: {duplicateCheck.existingDocument.doc_type}</div>
                        <div>Status: {duplicateCheck.existingDocument.status}</div>
                        <div>Uploaded: {new Date(duplicateCheck.existingDocument.upload_date).toLocaleDateString()}</div>
                        <div className="truncate">URI: {duplicateCheck.existingDocument.source_uri}</div>
                      </div>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600">
                    Do you want to overwrite the existing document?
                  </p>
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={handleOverwriteCancel}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleOverwriteConfirm(getValues())}
                    className="flex-1 px-4 py-2 bg-red-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Overwrite Document
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Bulk Upload Form */}
      {activeTab === 'bulk' && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Bulk Upload Documents
          </h2>
          
          <div className="mb-4 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium text-blue-900 mb-2">CSV Format</h3>
            <p className="text-sm text-blue-700">
              Upload a CSV file with columns: title, doc_type, source_uri, owner, version, tags, approved
            </p>
            <div className="mt-2 text-xs text-blue-600">
              <strong>Note:</strong> Set 'approved' column to 'false' to queue documents for admin approval before vectorization.
            </div>
          </div>

          <form onSubmit={onSubmitBulk} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                CSV File *
              </label>
              <input
                type="file"
                name="csvFile"
                accept=".csv"
                className="w-full input-field"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary disabled:opacity-50"
            >
              {isLoading ? 'Processing...' : 'Upload CSV'}
            </button>
          </form>
        </div>
      )}

      {/* Google Sheets/Drive Form */}
      {activeTab === 'sheets' && (
        <div className="card">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Connect Google Sheets/Drive
          </h2>
          
          <div className="mb-4 p-4 bg-green-50 rounded-lg">
            <h3 className="font-medium text-green-900 mb-2">Google Drive Integration</h3>
            <p className="text-sm text-green-700">
              Connect Google Drive folders or specific Google Sheets to automatically index project deliverables. 
              Documents will be queued for admin approval before vectorization.
            </p>
          </div>

          <form onSubmit={onSubmitSheets} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Google Drive Folder IDs *
              </label>
              <input
                type="text"
                name="folderIds"
                className="w-full input-field"
                placeholder="1ABC123DEF456, 2XYZ789GHI012"
                required
              />
              <p className="mt-1 text-sm text-gray-500">
                Enter comma-separated folder IDs. You can find these in the Google Drive URL.
              </p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                name="recursive"
                id="recursive"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="recursive" className="ml-2 block text-sm text-gray-900">
                Include subfolders (recursive)
              </label>
            </div>

            <div className="p-4 bg-yellow-50 rounded-lg">
              <h4 className="font-medium text-yellow-900 mb-2">Important Notes:</h4>
              <ul className="text-sm text-yellow-700 space-y-1">
                <li>• Documents will be queued for admin approval before processing</li>
                <li>• Only approved documents will be vectorized and made searchable</li>
                <li>• Supported formats: PDF, DOCX, TXT, MD, HTML, Google Sheets</li>
                <li>• Ensure the service account has access to the folders</li>
              </ul>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary disabled:opacity-50"
            >
              {isLoading ? 'Connecting...' : 'Connect Google Drive'}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
