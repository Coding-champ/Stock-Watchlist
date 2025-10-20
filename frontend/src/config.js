// Centralized frontend configuration
// Export the base URL the frontend should use to contact the backend API.
// Default to '/api' so the create-react-app dev proxy (setupProxy.js) works out of the box.
// Can be overridden with the REACT_APP_API_BASE environment variable.
const API_BASE = (process.env.REACT_APP_API_BASE || '/api').replace(/\/$/, '');

export default API_BASE;
