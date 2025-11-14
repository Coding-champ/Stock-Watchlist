import { useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import API_BASE from '../config';

/**
 * Custom Hook for standardized API calls with React Query integration
 * Provides consistent error handling, automatic deduplication, and caching
 * 
 * @returns {object} Object with fetchApi function
 */
export function useApi() {
  const queryClient = useQueryClient();

  /**
   * Unified fetch function with error handling and React Query integration
   * 
   * @param {string} endpoint - API endpoint (without base URL, e.g., '/stocks/')
   * @param {object} options - Fetch options
   * @param {string} options.method - HTTP method (GET, POST, PUT, DELETE)
   * @param {object} options.body - Request body (will be JSON stringified)
   * @param {object} options.headers - Additional headers
   * @param {boolean} options.useCache - Use React Query cache (default: true for GET)
   * @param {number} options.staleTime - Cache stale time in ms (default: 30000)
   * @param {function} options.onError - Custom error handler
   * @returns {Promise<any>} Response data
   */
  const fetchApi = useCallback(async (endpoint, options = {}) => {
    const {
      method = 'GET',
      body = null,
      headers = {},
      useCache = method === 'GET',
      staleTime = 30000,
      onError = null
    } = options;

    const url = `${API_BASE}${endpoint}`;

    // Build fetch options
    const fetchOptions = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      }
    };

    if (body) {
      fetchOptions.body = JSON.stringify(body);
    }

    try {
      // Use React Query for GET requests to leverage caching and deduplication
      if (useCache && method === 'GET') {
        const data = await queryClient.fetchQuery(
          ['api', url],
          async () => {
            const response = await fetch(url, fetchOptions);
            if (!response.ok) {
              const errorText = await response.text();
              throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            return response.json();
          },
          { staleTime }
        );
        return data;
      }

      // Direct fetch for POST/PUT/DELETE or when cache is disabled
      const response = await fetch(url, fetchOptions);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();

      // Invalidate related cache entries after mutations
      if (method !== 'GET') {
        // Invalidate all queries that start with the endpoint
        await queryClient.invalidateQueries(['api', `${API_BASE}${endpoint.split('?')[0]}`]);
      }

      return data;
    } catch (error) {
      console.error(`API Error [${method} ${endpoint}]:`, error);
      
      if (onError) {
        onError(error);
      }
      
      throw error;
    }
  }, [queryClient]);

  return { fetchApi };
}

export default useApi;
