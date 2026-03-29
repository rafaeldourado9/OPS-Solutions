import { api } from './client'

export type MovementType = 'in' | 'out' | 'adjustment'

export interface Product {
  id: string
  tenant_id: string
  name: string
  sku: string
  unit?: string
  description?: string
  unit_price: number | null
  cost_price?: number | null
  stock: number
  min_stock: number
  active: boolean
  is_low_stock?: boolean
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
  unit_price?: number | null
  cost_price?: number | null
  stock?: number
  min_stock?: number
}

export interface AddMovementPayload {
  type: MovementType
  quantity: number
  notes?: string
}

function mapProduct(p: any): Product {
  return {
    id: p.id,
    tenant_id: p.tenant_id,
    name: p.name,
    sku: p.sku,
    unit: p.unit,
    description: p.description,
    unit_price: p.price ?? p.unit_price ?? null,
    cost_price: p.cost ?? p.cost_price ?? null,
    stock: p.stock_quantity ?? p.stock ?? 0,
    min_stock: p.min_stock_alert ?? p.min_stock ?? 0,
    active: p.is_active ?? p.active ?? true,
    is_low_stock: p.is_low_stock,
    created_at: p.created_at,
    updated_at: p.updated_at,
  }
}

function mapMovement(m: any): StockMovement {
  return {
    id: m.id,
    product_id: m.product_id,
    type: m.type,
    quantity: m.quantity,
    notes: m.reason ?? m.notes,
    created_at: m.created_at,
    created_by: m.created_by,
  }
}

export const productsApi = {
  list: (params?: { q?: string; active_only?: boolean; low_stock_only?: boolean }) =>
    api.get('/api/v1/products', { params }).then((r: any) => {
      const d = r.data
      const items = Array.isArray(d) ? d : (d?.items ?? [])
      return items.map(mapProduct) as Product[]
    }),
  get: (id: string) =>
    api.get(`/api/v1/products/${id}`).then((r: any) => mapProduct(r.data)),
  create: (data: CreateProductPayload) =>
    api.post('/api/v1/products', {
      name: data.name,
      sku: data.sku,
      description: data.description,
      ...(data.unit_price !== undefined && { price: data.unit_price }),
      ...(data.cost_price !== undefined && { cost: data.cost_price }),
      stock_quantity: data.stock ?? 0,
      min_stock_alert: data.min_stock ?? 0,
    }).then((r: any) => mapProduct(r.data)),
  update: (id: string, data: Partial<CreateProductPayload>) =>
    api.put(`/api/v1/products/${id}`, {
      ...(data.name !== undefined && { name: data.name }),
      ...(data.sku !== undefined && { sku: data.sku }),
      ...(data.description !== undefined && { description: data.description }),
      ...(data.unit_price !== undefined && { price: data.unit_price }),
      ...(data.cost_price !== undefined && { cost: data.cost_price }),
      ...(data.stock !== undefined && { stock_quantity: data.stock }),
      ...(data.min_stock !== undefined && { min_stock_alert: data.min_stock }),
    }).then((r: any) => mapProduct(r.data)),
  addMovement: (id: string, data: AddMovementPayload) =>
    api.post(`/api/v1/products/${id}/stock-movements`, {
      type: data.type,
      quantity: data.quantity,
      reason: data.notes ?? '',
    }).then((r: any) => mapMovement(r.data?.movement ?? r.data)),
  getMovements: (id: string, params?: { page?: number; limit?: number }) =>
    api.get(`/api/v1/products/${id}/stock-movements`, { params }).then((r: any) => {
      const d = r.data
      const items = Array.isArray(d) ? d : (d?.items ?? [])
      return items.map(mapMovement) as StockMovement[]
    }),
  delete: (id: string) =>
    api.delete(`/api/v1/products/${id}`).then((r: any) => r.data),
  exportReport: () =>
    api.get('/api/v1/products/report/pdf', { responseType: 'arraybuffer' }).then((r: any) => r.data),
}
