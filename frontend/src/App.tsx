import { RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { router } from './router'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster
        position="top-right"
        toastOptions={{
          style: { fontFamily: 'Outfit, sans-serif', fontSize: '14px', borderRadius: '12px' },
          success: { iconTheme: { primary: '#0ABAB5', secondary: 'white' } },
        }}
      />
    </QueryClientProvider>
  )
}
