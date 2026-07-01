import axios from 'axios'

const apiBasePath = import.meta.env.BASE_URL.replace(/\/$/, '')

const api = axios.create({
  baseURL: `${apiBasePath}/api`,
})

// Attach bearer token from localStorage on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Surface a readable error message
api.interceptors.response.use(
  (res) => res,
  (error) => {
    const detail = error?.response?.data?.detail
    if (Array.isArray(detail)) {
      // pydantic validation errors
      error.message = detail.map((d) => d.msg).join('；')
    } else if (typeof detail === 'string') {
      error.message = detail
    }
    return Promise.reject(error)
  }
)

export default api
