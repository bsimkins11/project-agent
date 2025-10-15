'use client'

import { useState } from 'react'
import { assignDocumentCategory } from '@/lib/api'
import toast from 'react-hot-toast'

interface ClassificationModalProps {
  docId: string
  docTitle: string
  currentCategory: string
  onSuccess: () => void
  onCancel: () => void
}

const CATEGORY_OPTIONS = [
  { value: 'sow', label: 'SOW' },
  { value: 'timeline', label: 'Timeline' },
  { value: 'deliverables', label: 'Deliverables' },
  { value: 'misc', label: 'Misc' }
]

export default function ClassificationModal({
  docId,
  docTitle,
  currentCategory,
  onSuccess,
  onCancel
}: ClassificationModalProps) {
  const [loading, setLoading] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState(currentCategory || '')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedCategory) {
      toast.error('Please select a category')
      return
    }

    console.log('Submitting category update:', {
      docId,
      category: selectedCategory
    })

    setLoading(true)
    try {
      const result = await assignDocumentCategory(docId, {
        doc_type: selectedCategory
      })
      
      console.log('Category update result:', result)
      toast.success('Document category updated successfully')
      onSuccess()
    } catch (error) {
      console.error('Category update error:', error)
      toast.error('Failed to update document category')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            Update Document Category
          </h3>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-600">
            <strong>Document:</strong> {docTitle}
          </p>
          <p className="text-sm text-gray-600">
            <strong>Current Category:</strong> {currentCategory || 'Unclassified'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category *
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select Category</option>
              {CATEGORY_OPTIONS.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !selectedCategory}
              className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Updating...' : 'Update Category'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
