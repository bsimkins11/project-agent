'use client'

import { useState } from 'react'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import ChatInterface from '@/components/ChatInterface'
import DocumentFilters from '@/components/DocumentFilters'
import { DocumentType, MediaType } from '@/types'

export default function HomePage() {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({
    doc_type: undefined as DocumentType | undefined,
    media_type: undefined as MediaType | undefined,
  })

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Project Agent
              </h1>
              <span className="ml-2 text-sm text-gray-500">
                Transparent Partners
              </span>
            </div>
            <nav className="flex space-x-8">
              <a href="/admin" className="text-gray-600 hover:text-gray-900">
                Admin
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Search Filters
              </h2>
              <DocumentFilters filters={filters} onFiltersChange={setFilters} />
            </div>
          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-3">
            <div className="card">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Ask a Question
              </h2>
              <ChatInterface filters={filters} />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
