'use client'

import { useState, useEffect } from 'react'

interface HeaderProps {
  title?: string
  subtitle?: string
  showDocumentsDropdown?: boolean
  showAdminLink?: boolean
  showSignOut?: boolean
  isAdminPage?: boolean
}

export default function Header({ 
  title,
  subtitle,
  showDocumentsDropdown = true,
  showAdminLink = true,
  showSignOut = true,
  isAdminPage = false
}: HeaderProps) {
  // Set default titles based on page type
  const defaultTitle = isAdminPage ? "Project Deliverable Agent Admin" : "Project Deliverable Agent"
  const defaultSubtitle = isAdminPage ? "Transparent Partners" : "AI-Powered Project Deliverable Knowledge Assistant"
  
  const finalTitle = title || defaultTitle
  const finalSubtitle = subtitle || defaultSubtitle
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [email, setEmail] = useState('')
  const [isHydrated, setIsHydrated] = useState(false)

  useEffect(() => {
    // Mark as hydrated to avoid SSR issues
    setIsHydrated(true)
    
    // Check authentication state
    const savedAuth = localStorage.getItem('isAuthenticated')
    const savedEmail = localStorage.getItem('userEmail')
    const authToken = localStorage.getItem('auth_token')
    
    // Consider authenticated if either the main auth or admin auth token exists
    if ((savedAuth === 'true' && savedEmail) || authToken) {
      setIsAuthenticated(true)
      setEmail(savedEmail || 'admin@transparent.partners')
    }
  }, [])

  const handleSignOut = () => {
    setIsAuthenticated(false)
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('userEmail')
    localStorage.removeItem('auth_token')
    window.location.href = '/'
  }

  // Don't render until hydrated to avoid SSR issues
  if (!isHydrated) {
    return null
  }

  if (!isAuthenticated) {
    return null
  }

  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <a href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <img 
                src="/transparent-partners-logo.png" 
                alt="Transparent Partners" 
                className="h-8 w-auto"
              />
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  {finalTitle}
                </h1>
                <p className="text-xs text-gray-500">
                  {finalSubtitle}
                </p>
              </div>
            </a>
          </div>
          <nav className="flex items-center space-x-6">
            {/* Home Link (shown on admin page) */}
            {isAdminPage && (
              <a 
                href="/" 
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Home
              </a>
            )}

            {/* Documents Dropdown */}
            {showDocumentsDropdown && (
              <div className="relative group">
                <button className="text-sm text-gray-600 hover:text-gray-900 transition-colors flex items-center space-x-1">
                  <span>Documents</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {/* Dropdown Menu */}
                <div className="absolute top-full left-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="py-1">
                    <a 
                      href="/documents/sow" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      SOW
                    </a>
                    <a 
                      href="/documents/timeline" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      Timeline
                    </a>
                    <a 
                      href="/documents/deliverables" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      Deliverables
                    </a>
                    <a 
                      href="/documents/misc" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      Misc
                    </a>
                  </div>
                </div>
              </div>
            )}

            {showAdminLink && (
              <a 
                href="/admin" 
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Admin
              </a>
            )}
            
            {showSignOut && (
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <span>Demo Mode</span>
                <button 
                  onClick={handleSignOut}
                  className="text-blue-600 hover:text-blue-800"
                >
                  Sign Out
                </button>
              </div>
            )}
          </nav>
        </div>
      </div>
    </header>
  )
}
