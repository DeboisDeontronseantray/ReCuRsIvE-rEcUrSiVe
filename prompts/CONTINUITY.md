# Continuity

Chaining rules for a clip that has to meet the clips around it.

1. One continuous take per clip. One location per clip. The setting changes only between clips, through a shown action.
2. Each clip starts from the previous clip's true last frame. That frame is the final decoded frame.
3. Remove a camera HUD from a last frame before that frame starts the next clip.
4. Restate night, rain, and wardrobe in every prompt.
5. Exits never move toward the lens. Use "stays down" when a character must stay out.
6. A MUTATE pins both ends. The start frame is the true last frame of the clip before the slot. The end frame is the replaced clip's true last frame. Nothing after that slot re-renders. Forward re-render is a priced last resort. An EXTEND uses a start frame only.
