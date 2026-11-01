import { useState } from 'react'
import CopyDialog from './CopyDialog'
import Novel from './Novel'
import PromptForm, { EMPTY_PROMPT_FORM_VALUES, toNovelCreatePayload, type PromptFormValues } from './PromptForm'

interface NovelsProps {
  selectedNovel: string | null
  onSelectNovel: (id: string | null) => void
  onNovelCreated: () => void
}

function Novels({ selectedNovel, onSelectNovel, onNovelCreated }: NovelsProps) {
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (selectedNovel) {
    return <Novel name={selectedNovel} onNovelCreated={onNovelCreated} onSelectNovel={onSelectNovel} />
  }

  async function handleCreate(values: PromptFormValues) {
    setError(null)
    setCreating(true)
    try {
      const res = await fetch('/api/v1/novel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(toNovelCreatePayload(values)),
      })
      if (!res.ok) throw new Error(`POST /api/v1/novel failed: ${res.status}`)
      const { id } = await res.json()
      onNovelCreated()
      onSelectNovel(id)
    } catch (err) {
      console.error(err)
      setError('Failed to create novel. Please try again.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <>
      {creating && <CopyDialog title="New Season" message="Generating your novel..." />}
      <PromptForm
        legend="New Season"
        submitLabel="Create"
        submitPendingLabel="Creating..."
        initialValues={EMPTY_PROMPT_FORM_VALUES}
        submitting={creating}
        error={error}
        onSubmit={handleCreate}
      />
    </>
  )
}

export default Novels
