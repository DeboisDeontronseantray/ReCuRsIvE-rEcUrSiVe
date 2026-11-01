import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'

interface ErrorContextValue {
  error: string | null
  reportError: (message: string) => void
  clearError: () => void
}

const ErrorContext = createContext<ErrorContextValue | null>(null)

export function ErrorProvider({ children }: { children: ReactNode }) {
  const [error, setError] = useState<string | null>(null)

  const reportError = useCallback((message: string) => setError(message), [])
  const clearError = useCallback(() => setError(null), [])

  const value = useMemo(
    () => ({ error, reportError, clearError }),
    [error, reportError, clearError],
  )

  return <ErrorContext.Provider value={value}>{children}</ErrorContext.Provider>
}

// Access the shared error state. Must be used within an ErrorProvider.
export function useError() {
  const context = useContext(ErrorContext)
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider')
  }
  return context
}
