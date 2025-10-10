'use client'

import { DocumentType, MediaType } from '@/types'

interface DocumentFiltersProps {
  filters: {
    doc_type?: DocumentType | undefined
    media_type?: MediaType | undefined
  }
  onFiltersChange: (filters: {
    doc_type?: DocumentType | undefined
    media_type?: MediaType | undefined
  }) => void
}

export default function DocumentFilters({ filters, onFiltersChange }: DocumentFiltersProps) {
  const documentTypes: { value: DocumentType | '', label: string }[] = [
    { value: '', label: 'All Types' },
    { value: 'PDF', label: 'PDF' },
    { value: 'DOCX', label: 'Word Document' },
    { value: 'TXT', label: 'Text File' },
    { value: 'MD', label: 'Markdown' },
    { value: 'HTML', label: 'HTML' }
  ]

  const mediaTypes: { value: MediaType | '', label: string }[] = [
    { value: '', label: 'All Media' },
    { value: 'text', label: 'Text Documents' },
    { value: 'image', label: 'Images' }
  ]

  const handleDocTypeChange = (value: string) => {
    onFiltersChange({
      ...filters,
      doc_type: (value as DocumentType) || undefined
    })
  }

  const handleMediaTypeChange = (value: string) => {
    onFiltersChange({
      ...filters,
      media_type: (value as MediaType) || undefined
    })
  }

  return (
    <div className="space-y-4">
      {/* Document Type Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Document Type
        </label>
        <select
          value={filters.doc_type || ''}
          onChange={(e) => handleDocTypeChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {documentTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Media Type Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Media Type
        </label>
        <select
          value={filters.media_type || ''}
          onChange={(e) => handleMediaTypeChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {mediaTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Clear Filters */}
      <button
        onClick={() => onFiltersChange({})}
        className="w-full px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
      >
        Clear Filters
      </button>
    </div>
  )
}