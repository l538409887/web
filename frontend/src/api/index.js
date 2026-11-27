import request from './request'

export const getHome = () => request.get('/home')
export const getNotices = (limit = 6) => request.get('/notices', { params: { limit } })

export const getReportReasons = () => request.get('/reports/reasons')
export const createReport = (payload) => request.post('/reports', payload)

export const getAuthor = (id) => request.get(`/authors/${id}`)
export const getAuthorBooks = (id, params) => request.get(`/authors/${id}/books`, { params })
export const followAuthor = (id) => request.post(`/authors/${id}/follow`)
export const unfollowAuthor = (id) => request.delete(`/authors/${id}/follow`)
export const getMyFollows = (params) => request.get('/user/follows', { params })
export const getCategories = () => request.get('/categories')

export const getBooks = (params) => request.get('/books', { params })
export const getBook = (id) => request.get(`/books/${id}`)
export const getChapters = (bookId, params) =>
  request.get(`/books/${bookId}/chapters`, { params })

export const getChapter = (chapterId) => request.get(`/chapters/${chapterId}`)

export const register = (payload) => request.post('/auth/register', payload)
export const login = (payload) => request.post('/auth/login', payload)
export const getMe = () => request.get('/auth/me')
export const updateProfile = (payload) => request.put('/auth/me', payload)
export const changePassword = (payload) => request.put('/auth/password', payload)
export const logout = () => request.post('/auth/logout')

export const getShelf = (params) => request.get('/bookshelf', { params })
export const addShelf = (bookId) => request.post('/bookshelf', { book_id: bookId })
export const removeShelf = (bookId) => request.delete(`/bookshelf/${bookId}`)

export const getHistory = (limit = 10) => request.get('/history', { params: { limit } })
export const postHistory = (payload) => request.post('/history', payload)

export const getBookComments = (bookId, params) =>
  request.get(`/books/${bookId}/comments`, { params })
export const getChapterComments = (chapterId, params) =>
  request.get(`/chapters/${chapterId}/comments`, { params })
export const createComment = (payload) => request.post('/comments', payload)
export const deleteComment = (id) => request.delete(`/comments/${id}`)

export const getMyComments = (params) => request.get('/user/comments', { params })

export const getParagraphComments = (chapterId) =>
  request.get(`/chapters/${chapterId}/paragraph-comments`)
export const addParagraphComment = (payload) => request.post('/paragraph-comments', payload)
export const getMyParagraphComments = (params) =>
  request.get('/user/paragraph-comments', { params })
export const reactParagraph = (id, reaction) =>
  request.post(`/paragraph-comments/${id}/react`, { reaction })
export const deleteParagraphComment = (id) => request.delete(`/paragraph-comments/${id}`)

export const getMonthlyRank = (limit = 10) => request.get('/rank/monthly', { params: { limit } })

export const purchaseBook = (bookId) => request.post(`/books/${bookId}/purchase`)
export const purchaseChapters = (bookId, chapterIds) =>
  request.post(`/books/${bookId}/purchase-chapters`, { chapter_ids: chapterIds })
export const feedWatermelon = (bookId, count = 1) =>
  request.post(`/books/${bookId}/feed-watermelon`, { count })

export const uploadImage = (file, scene = 'cover') => {
  const form = new FormData()
  form.append('file', file)
  form.append('scene', scene)
  return request.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}