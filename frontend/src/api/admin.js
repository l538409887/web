import request from './request'

export const getStats = () => request.get('/admin/stats')

export const getAdminBooks = (params) => request.get('/admin/books', { params })
export const createBook = (payload) => request.post('/admin/books', payload)
export const updateBookStatus = (id, payload) =>
  request.put(`/admin/books/${id}/status`, payload)
export const previewChapters = (id, rawText) =>
  request.post(`/admin/books/${id}/chapters/preview`, { raw_text: rawText })
export const importChapters = (id, rawText) =>
  request.post(`/admin/books/${id}/chapters/import`, { raw_text: rawText })

export const getAdminUsers = (params) => request.get('/admin/users', { params })
export const updateUser = (id, payload) => request.put(`/admin/users/${id}`, payload)

export const getAdminComments = (params) => request.get('/admin/comments', { params })
export const updateCommentStatus = (id, status) =>
  request.put(`/admin/comments/${id}/status`, { status })

export const getAdminReports = (params) => request.get('/admin/reports', { params })
export const handleReport = (id, action) =>
  request.put(`/admin/reports/${id}`, { action })

export const getParagraphComments = (params) =>
  request.get('/admin/paragraph-comments', { params })
export const updateParagraphStatus = (id, status) =>
  request.put(`/admin/paragraph-comments/${id}/status`, { status })

export const getAdminNotices = (params) => request.get('/admin/notices', { params })
export const createNotice = (payload) => request.post('/admin/notices', payload)
export const updateNotice = (id, payload) => request.put(`/admin/notices/${id}`, payload)
export const deleteNotice = (id) => request.delete(`/admin/notices/${id}`)

export const getCategories = () => request.get('/categories')
export const createCategory = (payload) => request.post('/admin/categories', payload)
export const updateCategory = (id, payload) =>
  request.put(`/admin/categories/${id}`, payload)
export const deleteCategory = (id) => request.delete(`/admin/categories/${id}`)