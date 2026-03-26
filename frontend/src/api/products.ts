import { api } from './client'

export type MovementType = 'in' | 'out' | 'adjustment'

export interface Product {
  id: string
  tenant_id: string
  name: string
  sku: string
  description?: string
  unit_price: number
  cost_price?: number
  stock: number
  min_stock: number
  active: boolean
  created_at: string
  updated_at: string
}

export interface StockMovement {
  id: string
  product_id: string
  type: MovementType
  quantity: number
  notes?: string
  created_at: string
  created_by?: string
}

export interface CreateProductPayload {
  name: string
  sku: string
  description?: string
  unit_price: number
  cost_price?: number
  stock?: number
  min_stock?: number
}

export interface AddMovementPayload {
  type: MovementType
  quantity: number
  notes?: string
}

export const productsApi = {
  list: (params?: { q?: string; active_only?: boolean; low_stock_only?: boolean }) =>
    api.get<Product[]>('/api/v1/products', { params }).then((r: any) => r.data),
  get: (id: string) =>
    api.get<Product>(`/api/v1/products/${id}`).then((r: any) => r.data),
  create: (data: CreateProductPayload) =>
    api.post<Product>('/api/v1/products', data).then((r: any) => r.data),
  update: (id: string, data: Partial<CreateProductPayload>) =>
    api.put<Product>(`/api/v1/products/${id}`, data).then((r: any) => r.data),
  addMovement: (id: string, data: AddMovementPayload) =>
    api.post<StockMovement>(`/api/v1/products/${id}/stock-movements`, data).then((r: any) => r.data),
  getMovements: (id: string, params?: { page?: number; limit?: number }) =>
    api.get<StockMovement[]>(`/api/v1/products/${id}/stock-movements`, { params }).then((r: any) => r.data),
}
