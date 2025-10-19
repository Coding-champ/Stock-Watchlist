// Centralized frontend configuration
// Export the base URL the frontend should use to contact the backend API.
// Can be overridden with the REACT_APP_API_BASE environment variable.
const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8080';

export default API_BASE;
