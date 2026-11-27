import request from './request'

export const applyAuthor = () => request.post('/author/apply')

export const getMyBooks = (params) => request.get('/author/books', { params })
export const createMyBook = (payload) => request.post('/author/books', payload)
export const updateMyBook = (id, payload) => request.put(`/author/books/${id}`, payload)
export const submitMyBook = (id) => request.post(`/author/books/${id}/submit`)
export const applyMyBookShelf = (id) => request.post(`/author/books/${id}/apply-shelf`)

export const getMyChapters = (bookId, params) =>
  request.get(`/author/books/${bookId}/chapters`, { params })
export const createChapter = (bookId, payload) =>
  request.post(`/author/books/${bookId}/chapters`, payload)
export const previewMyChapters = (bookId, rawText) =>
  request.post(`/author/books/${bookId}/chapters/preview`, { raw_text: rawText })
export const importMyChapters = (bookId, rawText) =>
  request.post(`/author/books/${bookId}/chapters/import`, { raw_text: rawText })

export const getMyChapter = (id) => request.get(`/author/chapters/${id}`)
export const updateChapter = (id, payload) => request.put(`/author/chapters/${id}`, payload)
export const deleteChapter = (id) => request.delete(`/author/chapters/${id}`)
