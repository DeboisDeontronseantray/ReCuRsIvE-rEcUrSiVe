import { useState } from 'react'
import CopyDialog from './CopyDialog'
import PromptForm, {
  toNovelCreatePayload,
  type DraftCharacterSeed,
  type DraftSecondaryThread,
  type PromptFormValues,
} from './PromptForm'

interface PromptsProps {
  novelId: string
  title: string
  wordCount: number
  premise: string
  toneNotes: string
  charactersNotes: string
  worldbuildingNotes: string
  characterGenerationNotes: string
  primaryThread: string
  secondaryThreads: DraftSecondaryThread[]
  primaryGenre: string
  region: string
  characterSeeds: DraftCharacterSeed[]
  author: string
  themes: string
  metadataModel: string
  genreConventionsModel: string
  charactersModel: string
  worldbuildingModel: string
  primaryThreadModel: string
  secondaryArcsModel: string
  outlineModel: string
  outlineAuditModel: string
  entitiesModel: string
  initialStateModel: string
  metadataReasoning: boolean
  genreConventionsReasoning: boolean
  charactersReasoning: boolean
  worldbuildingReasoning: boolean
  primaryThreadReasoning: boolean
  secondaryArcsReasoning: boolean
  outlineReasoning: boolean
  outlineAuditReasoning: boolean
  entitiesReasoning: boolean
  initialStateReasoning: boolean
  onRegenerated: (newId: string) => void
  // Called after a per-step "Regenerate from here" (Worldbuilding/Outline)
  // succeeds, so Novel.tsx can refresh whatever tabs the cascade touched.
  onStepRegenerated: (step: 'worldbuilding' | 'outline') => void
}

// The "Prompts" tab: the exact same PromptForm used to create a novel,
// prefilled with this novel's current values. Regenerate wipes this novel
// and creates a fresh one from the (possibly edited) fields below.
function Prompts({
  novelId,
  title,
  wordCount,
  premise,
  toneNotes,
  charactersNotes,
  worldbuildingNotes,
  characterGenerationNotes,
  primaryThread,
  secondaryThreads,
  primaryGenre,
  region,
  characterSeeds,
  author,
  themes,
  metadataModel,
  genreConventionsModel,
  charactersModel,
  worldbuildingModel,
  primaryThreadModel,
  secondaryArcsModel,
  outlineModel,
  outlineAuditModel,
  entitiesModel,
  initialStateModel,
  metadataReasoning,
  genreConventionsReasoning,
  charactersReasoning,
  worldbuildingReasoning,
  primaryThreadReasoning,
  secondaryArcsReasoning,
  outlineReasoning,
  outlineAuditReasoning,
  entitiesReasoning,
  initialStateReasoning,
  onRegenerated,
  onStepRegenerated,
}: PromptsProps) {
  const [regenerating, setRegenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const initialValues: PromptFormValues = {
    title,
    wordCount,
    premise,
    toneNotes,
    charactersNotes,
    worldbuildingNotes,
    characterGenerationNotes,
    primaryThread,
      secondaryThreads,
    primaryGenre,
    region,
    characterSeeds,
    author,
    themes,
    metadataModel,
    charactersModel,
    worldbuildingModel,
    primaryThreadModel,
    secondaryArcsModel,
    outlineModel,
    outlineAuditModel,
    entitiesModel,
    initialStateModel,
    metadataReasoning,
    charactersReasoning,
    worldbuildingReasoning,
    primaryThreadReasoning,
    secondaryArcsReasoning,
    outlineReasoning,
    outlineAuditReasoning,
    entitiesReasoning,
    initialStateReasoning,
  }

  async function handleRegenerate(values: PromptFormValues) {
    setError(null)
    setRegenerating(true)
    try {
      const deleteRes = await fetch(`/api/v1/novel/${novelId}`, { method: 'DELETE' })
      if (!deleteRes.ok) throw new Error(`DELETE /api/v1/novel/${novelId} failed: ${deleteRes.status}`)

      const createRes = await fetch('/api/v1/novel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(toNovelCreatePayload(values)),
      })
      if (!createRes.ok) throw new Error(`POST /api/v1/novel failed: ${createRes.status}`)
      const { id } = await createRes.json()
      onRegenerated(id)
    } catch (err) {
      console.error(err)
      setError('Failed to regenerate novel. Please try again.')
      setRegenerating(false)
    }
  }

  return (
    <>
      {regenerating && <CopyDialog title="Regenerating Novel" message="Generating your novel..." />}
      <PromptForm
        legend="Prompts"
        submitLabel="Regenerate"
        submitPendingLabel="Regenerating..."
        initialValues={initialValues}
        submitting={regenerating}
        error={error}
        onSubmit={handleRegenerate}
        requireDirty
        confirmTitle="Regenerate Novel"
        confirmMessage="This will permanently delete everything generated for this novel (characters, outline, worldbuilding, etc.) and generate it all again from scratch using the prompt below. This cannot be undone."
        novelId={novelId}
        onNovelRegenerated={onStepRegenerated}
      />
    </>
  )
}

export default Prompts
