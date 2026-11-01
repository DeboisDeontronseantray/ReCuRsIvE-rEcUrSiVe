import { Component, type ErrorInfo, type ReactNode } from 'react'
import { useError } from '../context/ErrorContext'

interface ErrorBoundaryClassProps {
  children: ReactNode
  reportError: (message: string) => void
}

interface ErrorBoundaryClassState {
  hasError: boolean
}

// Catches render-time crashes in its subtree and reports them to the shared error display.
class ErrorBoundaryClass extends Component<ErrorBoundaryClassProps, ErrorBoundaryClassState> {
  state: ErrorBoundaryClassState = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(error, info)
    this.props.reportError(error.message || 'Something went wrong.')
  }

  render() {
    if (this.state.hasError) return null
    return this.props.children
  }
}

// Function wrapper so the class boundary can read the shared error context.
function ErrorBoundary({ children }: { children: ReactNode }) {
  const { reportError } = useError()
  return <ErrorBoundaryClass reportError={reportError}>{children}</ErrorBoundaryClass>
}

export default ErrorBoundary
