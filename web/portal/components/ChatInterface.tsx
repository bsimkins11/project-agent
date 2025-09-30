'use client'

import { useState } from 'react'
import { PaperAirplaneIcon } from '@heroicons/react/24/outline'
import { ChatRequest, ChatResponse, Citation } from '@/types'
import { sendChatMessage } from '@/lib/api'
import toast from 'react-hot-toast'

interface ChatInterfaceProps {
  filters: {
    doc_type?: string
    media_type?: string
  }
}

export default function ChatInterface({ filters }: ChatInterfaceProps) {
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [response, setResponse] = useState<ChatResponse | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || isLoading) return

    setIsLoading(true)
    try {
      const request: ChatRequest = {
        query: query.trim(),
        filters: Object.keys(filters).length > 0 ? filters : undefined,
        max_results: 10
      }

      const result = await sendChatMessage(request)
      setResponse(result)
      setQuery('')
    } catch (error) {
      toast.error('Failed to send message')
      console.error('Chat error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Chat Form */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about your documents..."
          className="flex-1 input-field"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <PaperAirplaneIcon className="h-5 w-5" />
        </button>
      </form>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-2 text-gray-600">Searching...</span>
        </div>
      )}

      {/* Response */}
      {response && (
        <div className="space-y-4">
          {/* Answer */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-2">Answer</h3>
            <div className="prose prose-sm max-w-none">
              <p>{response.answer}</p>
            </div>
          </div>

          {/* Citations */}
          {response.citations.length > 0 && (
            <div>
              <h3 className="font-medium text-gray-900 mb-3">
                Sources ({response.citations.length})
              </h3>
              <div className="space-y-3">
                {response.citations.map((citation, index) => (
                  <CitationCard key={index} citation={citation} />
                ))}
              </div>
            </div>
          )}

          {/* Query Stats */}
          <div className="text-sm text-gray-500">
            Found {response.total_results} results in {response.query_time_ms}ms
          </div>
        </div>
      )}
    </div>
  )
}

function CitationCard({ citation }: { citation: Citation }) {
  return (
    <div className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="font-medium text-gray-900">{citation.title}</h4>
          {citation.page && (
            <p className="text-sm text-gray-500">Page {citation.page}</p>
          )}
          <p className="text-sm text-gray-700 mt-1">{citation.excerpt}</p>
        </div>
        {citation.thumbnail && (
          <img
            src={citation.thumbnail}
            alt={citation.title}
            className="w-16 h-16 object-cover rounded ml-3"
          />
        )}
      </div>
      <div className="mt-2">
        <a
          href={citation.uri}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary-600 hover:text-primary-700 text-sm font-medium"
        >
          View Document →
        </a>
      </div>
    </div>
  )
}
