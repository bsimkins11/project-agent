'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { ingestDocument, ingestCSV } from '@/lib/api'
import toast from 'react-hot-toast'

interface IngestFormData {
  title: string
  doc_type: string
  source_uri: string
  tags: string
  owner?: string
  version?: string
}

export default function IngestForm() {
  const [activeTab, setActiveTab] = useState<'single' | 'bulk'>('single')
  const [isLoading, setIsLoading] = useState(false)

  const { register, handleSubmit, reset, formState: { errors } } = useForm<IngestFormData>()

  const onSubmitSingle = async (data: IngestFormData) => {
    setIsLoading(true)
    try {
      const tags = data.tags.split(',').map(tag => tag.trim()).filter(Boolean)
      const result = await ingestDocument({
        title: data.title,
        doc_type: data.doc_type,
        source_uri: data.source_uri,
        tags,
        owner: data.owner,
        version: data.version,
      })
      
      toast.success(result.message)
      reset()
    } catch (error) {
      toast.error('Failed to ingest document')
      console.error('Ingest error:', error)
    } finally {
      setIsLoading(false)
    }
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

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary disabled:opacity-50"
            >
              {isLoading ? 'Ingesting...' : 'Ingest Document'}
            </button>
          </form>
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
    </div>
  )
}
