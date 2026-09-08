import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { routeTree } from './app/routeTree'
import { LocalizationProvider } from './localization'
import { createConfiguredRemoteCatalogProvider } from './integrations/localization/config'
import './styles/index.css'

const remoteCatalogProvider = createConfiguredRemoteCatalogProvider()

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

const router = createRouter({
  routeTree,
  context: { queryClient },
  defaultPreload: 'intent',
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <LocalizationProvider remoteProvider={remoteCatalogProvider}>
        <RouterProvider router={router} />
      </LocalizationProvider>
    </QueryClientProvider>
  </StrictMode>
)
