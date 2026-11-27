import request from './request'

export const getWallet = () => request.get('/wallet')
export const signIn = () => request.post('/wallet/sign-in')
export const getPayInfo = () => request.get('/wallet/pay-info')
export const getMyOrders = (params) => request.get('/wallet/orders', { params })
export const createOrder = (amountFen) => request.post('/wallet/orders', { amount_fen: amountFen })

export const getAdminOrders = (params) => request.get('/admin/orders', { params })
export const confirmOrder = (id) => request.put(`/admin/orders/${id}/confirm`)
export const cancelOrder = (id) => request.put(`/admin/orders/${id}/cancel`)