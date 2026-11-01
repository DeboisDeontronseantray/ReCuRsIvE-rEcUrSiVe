import { useLayoutEffect, useRef, type TextareaHTMLAttributes } from 'react'

// A textarea that grows to fit its content instead of scrolling internally.
function AutoGrowTextarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const ref = useRef<HTMLTextAreaElement>(null)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [props.value])

  return <textarea {...props} ref={ref} rows={1} />
}

export default AutoGrowTextarea
