import { createContext, useContext, type ReactNode } from 'react'
import type { ProductionSource } from './types'

const ProductionSourceContext = createContext<ProductionSource | undefined>(undefined)

export function ProductionSourceProvider({ source, children }: { source: ProductionSource; children: ReactNode }) {
  return <ProductionSourceContext.Provider value={source}>{children}</ProductionSourceContext.Provider>
}

export function useProvidedProductionSource(): ProductionSource | undefined {
  return useContext(ProductionSourceContext)
}

const adapterIds = new WeakMap<ProductionSource['adapter'], number>()
let nextAdapterId = 0
export function productionAdapterKey(adapter: ProductionSource['adapter']): number {
  if (!adapterIds.has(adapter)) adapterIds.set(adapter, ++nextAdapterId)
  return adapterIds.get(adapter)!
}

