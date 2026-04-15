import axios from 'axios'

const getBaseURL = () => {
  const url = import.meta.env.VITE_API_BASE_URL || ''
  if (!url) return ''
  return url.endsWith('/') ? url : `${url}/`
}

const api = axios.create({
  baseURL: getBaseURL(),
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// Automatically attach Django's CSRF token to every mutating request
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^|;\\s*)' + name + '=([^;]*)'))
  return match ? decodeURIComponent(match[2]) : null
}

api.interceptors.request.use((config) => {
  // Only send CSRF token for unsafe methods (POST, PATCH, PUT, DELETE)
  const unsafeMethods = ['post', 'patch', 'put', 'delete']
  if (unsafeMethods.includes(config.method?.toLowerCase())) {
    const csrfToken = getCookie('csrftoken')
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken
    }
  }
  return config
})


// Auth
export const getGoogleLoginUrl = () => api.get('/api/auth/google/login/')
export const getMe = () => api.get('/api/auth/me/')
export const updateMe = (data) => api.patch('/api/auth/me/', data)
export const uploadAsset = (formData) => api.post('/api/auth/asset-upload/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const logout = () => api.post('/api/auth/logout/')

// Jobs
export const createJob = (data) => api.post('/api/jobs/create/', data)
export const getJobs = (params) => api.get('/api/jobs/', { params })
export const getJobStatus = (id) => api.get(`/api/jobs/${id}/status/`)
export const getJobDetail = (id) => api.get(`/api/jobs/${id}/`)
export const regenerateJob = (id) => api.post(`/api/jobs/${id}/regenerate/`)

// Subjects
export const getSubjects = () => api.get('/api/subjects/')
export const createSubject = (data) => api.post('/api/subjects/', data)
export const deleteSubject = (id) => api.delete(`/api/subjects/${id}/`)

export default api
