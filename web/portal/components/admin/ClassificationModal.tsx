'use client'

import { useState, useEffect } from 'react'
import { assignDocumentCategory, getClassificationOptions } from '@/lib/api'
import { ClassificationOptions } from '@/types'
import toast from 'react-hot-toast'

interface ClassificationModalProps {
  docId: string
  docTitle: string
  currentType: string
  onSuccess: () => void
  onCancel: () => void
}

export default function ClassificationModal({
  docId,
  docTitle,
  currentType,
  onSuccess,
  onCancel
}: ClassificationModalProps) {
  const [loading, setLoading] = useState(false)
  const [classificationOptions, setClassificationOptions] = useState<ClassificationOptions | null>(null)
  const [selectedDocType, setSelectedDocType] = useState(currentType || '')
  const [selectedCategory, setSelectedCategory] = useState('')
  const [selectedSubcategory, setSelectedSubcategory] = useState('')

  useEffect(() => {
    loadClassificationOptions()
  }, [])

  const loadClassificationOptions = async () => {
    try {
      console.log('Loading classification options...')
      const options = await getClassificationOptions()
      console.log('Classification options loaded:', options)
      setClassificationOptions(options)
    } catch (error) {
      console.error('Failed to load classification options:', error)
      toast.error('Failed to load classification options')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedDocType) {
      toast.error('Please select a document type')
      return
    }

    console.log('Submitting classification:', {
      docId,
      doc_type: selectedDocType,
      category: selectedCategory,
      subcategory: selectedSubcategory
    })

    setLoading(true)
    try {
      const result = await assignDocumentCategory(docId, {
        doc_type: selectedDocType,
        category: selectedCategory || undefined,
        subcategory: selectedSubcategory || undefined
      })
      
      console.log('Classification result:', result)
      toast.success('Document classification updated successfully')
      onSuccess()
    } catch (error) {
      console.error('Classification update error:', error)
      toast.error('Failed to update document classification')
    } finally {
      setLoading(false)
    }
  }

  const handleDocTypeChange = (docType: string) => {
    setSelectedDocType(docType)
    // Reset category and subcategory when doc type changes
    setSelectedCategory('')
    setSelectedSubcategory('')
  }

  if (!classificationOptions) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">Loading classification options...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">
            Classify Document
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
            <strong>Current Type:</strong> {currentType || 'Unclassified'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Document Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Document Type *
            </label>
            <select
              value={selectedDocType}
              onChange={(e) => handleDocTypeChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select Document Type</option>
              {classificationOptions.doc_types.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category (Optional)
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Category</option>
              {classificationOptions.categories.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
          </div>

          {/* Subcategory */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Subcategory (Optional)
            </label>
            <select
              value={selectedSubcategory}
              onChange={(e) => setSelectedSubcategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Subcategory</option>
              {classificationOptions.subcategories.map((subcategory) => (
                <option key={subcategory.value} value={subcategory.value}>
                  {subcategory.label}
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
              disabled={loading || !selectedDocType}
              className="px-4 py-2 bg-blue-600 border border-transparent rounded-md text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Updating...' : 'Update Classification'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
