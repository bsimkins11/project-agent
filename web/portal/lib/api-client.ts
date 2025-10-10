/**
 * Production-grade API client with error handling, retry logic, and interceptors
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ChatRequest, ChatResponse, InventoryResponse, Document } from '@/types'

// API Configuration
const API_CONFIG = {
  baseURL: process.env.NODE_ENV === 'production' ? '' : 'http://localhost:3000',
  timeout: 30000,
  retries: 3,
  retryDelay: 1000,
}

// Custom error class for API errors
export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public errorCode?: string,
    public details?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

// Retry configuration for specific error codes
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]

/**
 * Sleep utility for retry delays
 */
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * Create axios instance with interceptors
 */
class APIClient {
  private instance: AxiosInstance
  private retryCount: Map<string, number> = new Map()

  constructor() {
    this.instance = axios.create({
      baseURL: API_CONFIG.baseURL,
      timeout: API_CONFIG.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors() {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        // Add auth token
        const token = this.getAuthToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId()

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.instance.interceptors.response.use(
      (response) => {
        // Reset retry count on success
        const requestKey = this.getRequestKey(response.config)
        this.retryCount.delete(requestKey)
        return response
      },
      async (error: AxiosError) => {
        return this.handleResponseError(error)
      }
    )
  }

  /**
   * Handle response errors with retry logic
   */
  private async handleResponseError(error: AxiosError): Promise<any> {
    const config = error.config
    if (!config) {
      return Promise.reject(this.transformError(error))
    }

    const requestKey = this.getRequestKey(config)
    const currentRetryCount = this.retryCount.get(requestKey) || 0

    // Check if error is retryable
    const isRetryable = 
      error.response && 
      RETRYABLE_STATUS_CODES.includes(error.response.status) &&
      currentRetryCount < API_CONFIG.retries

    if (isRetryable) {
      this.retryCount.set(requestKey, currentRetryCount + 1)
      
      // Calculate delay with exponential backoff
      const delay = API_CONFIG.retryDelay * Math.pow(2, currentRetryCount)
      
      console.warn(`Retrying request (${currentRetryCount + 1}/${API_CONFIG.retries}) after ${delay}ms`)
      await sleep(delay)
      
      return this.instance.request(config)
    }

    // Clear retry count
    this.retryCount.delete(requestKey)
    
    return Promise.reject(this.transformError(error))
  }

  /**
   * Transform axios error to custom APIError
   */
  private transformError(error: AxiosError): APIError {
    if (error.response) {
      // Server responded with error
      const data = error.response.data as any
      return new APIError(
        data?.detail?.message || data?.message || 'An error occurred',
        error.response.status,
        data?.detail?.error || data?.error,
        data?.detail?.details || data?.details
      )
    } else if (error.request) {
      // Request made but no response
      return new APIError(
        'No response from server. Please check your connection.',
        undefined,
        'network_error'
      )
    } else {
      // Error setting up request
      return new APIError(
        error.message || 'An unexpected error occurred',
        undefined,
        'client_error'
      )
    }
  }

  /**
   * Get auth token from storage
   */
  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('auth_token')
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Get request key for retry tracking
   */
  private getRequestKey(config: AxiosRequestConfig): string {
    return `${config.method}-${config.url}`
  }

  /**
   * Generic GET request
   */
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config)
    return response.data
  }

  /**
   * Generic POST request
   */
  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config)
    return response.data
  }

  /**
   * Generic PUT request
   */
  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config)
    return response.data
  }

  /**
   * Generic DELETE request
   */
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config)
    return response.data
  }
}

// Create singleton instance
const apiClient = new APIClient()

export default apiClient

