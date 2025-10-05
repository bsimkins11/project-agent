'use client'

import { useState, useEffect } from 'react'
import ChatInterface from '@/components/ChatInterface'

export default function HomePage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  // Check for existing authentication on component mount
  useEffect(() => {
    const savedAuth = localStorage.getItem('isAuthenticated')
    const savedEmail = localStorage.getItem('userEmail')
    if (savedAuth === 'true' && savedEmail) {
      setIsAuthenticated(true)
      setEmail(savedEmail)
    }
  }, [])

  const handleSignIn = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    // Validate email domain
    if (!email.endsWith('@transparent.partners')) {
      setError('Please use your @transparent.partners email address')
      return
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address')
      return
    }
    
    // Simulate authentication and save to localStorage
    setIsAuthenticated(true)
    localStorage.setItem('isAuthenticated', 'true')
    localStorage.setItem('userEmail', email)
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Transparent Partners
            </h1>
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">
              Project Deliverable Agent
            </h2>
            <p className="text-lg text-gray-600 mb-8">
              AI-Powered Project Deliverable Knowledge Assistant
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
              <p className="text-sm text-blue-800 font-medium">
                Demo Access Required
              </p>
            </div>
          </div>

          {/* Sign In Form */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">
              Welcome Back
            </h3>
            <p className="text-gray-600 mb-6">
              Sign in with your Transparent Partners email to access the demo
            </p>
            
            <form onSubmit={handleSignIn} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="your.email@transparent.partners"
                />
              </div>
              
              {error && (
                <div className="text-red-600 text-sm">{error}</div>
              )}
              
              <button
                type="submit"
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Sign In
              </button>
            </form>
            
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-900 mb-3">
                Demo Access Requirements:
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• @transparent.partners email domain</li>
                <li>• Valid email format</li>
                <li>• Session persistence enabled</li>
              </ul>
            </div>
          </div>

          {/* Demo Mode Notice */}
          <div className="text-center">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                <span className="font-medium">🚀 Demo Mode</span><br />
                This is a Proof of Concept (POC) demo application for Project Agent. 
                It simulates the functionality of an NLP-powered project knowledge assistant 
                to gather end-user feedback before actual development.
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">
            Welcome Back
          </h2>
          <p className="text-gray-600">
            Ask questions about your project documents and get AI-powered insights with citations.
          </p>
        </div>

        {/* Chat Interface */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Ask a Question
          </h3>
          <ChatInterface />
        </div>
      </main>
    </div>
  )
}
