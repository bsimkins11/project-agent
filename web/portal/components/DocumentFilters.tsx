'use client'

import { DocumentType, MediaType } from '@/types'

interface DocumentFiltersProps {
  filters: {
    doc_type?: DocumentType
    media_type?: MediaType
  }
  onFiltersChange: (filters: {
    doc_type?: DocumentType
    media_type?: MediaType
  }) => void
}

export default function DocumentFilters({ filters, onFiltersChange }: DocumentFiltersProps) {
  const updateFilter = (key: string, value: string | undefined) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined
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
          onChange={(e) => updateFilter('doc_type', e.target.value)}
          className="w-full input-field"
        >
          <option value="">All Types</option>
          <option value="sow">Statement of Work</option>
          <option value="timeline">Timeline</option>
          <option value="deliverable">Deliverable</option>
          <option value="misc">Miscellaneous</option>
        </select>
      </div>

      {/* Media Type Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Media Type
        </label>
        <select
          value={filters.media_type || ''}
          onChange={(e) => updateFilter('media_type', e.target.value)}
          className="w-full input-field"
        >
          <option value="">All Media</option>
          <option value="document">Document</option>
          <option value="image">Image</option>
        </select>
      </div>

      {/* Clear Filters */}
      {(filters.doc_type || filters.media_type) && (
        <button
          onClick={() => onFiltersChange({})}
          className="w-full btn-secondary"
        >
          Clear Filters
        </button>
      )}
    </div>
  )
}
