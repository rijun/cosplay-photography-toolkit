/**
 * Orchestration between the `gallery` state and the API: optimistic updates and
 * what to do when the server disagrees.
 */
import * as api from './api'
import type { Photo } from './photo'
import { gallery } from './state.svelte'

function setFlag(photo: Photo, color: number, on: boolean) {
    const index = photo.flags.indexOf(color)
    if (on && index === -1) photo.flags.push(color)
    if (!on && index !== -1) photo.flags.splice(index, 1)
}

/**
 * Toggle a mark, defaulting to the visitor's own color.
 *
 * Applied locally first so the tap feels instant, then reconciled against the
 * server's answer — flags are shared across galleries, so another cosplayer may
 * have changed the same one in between.
 */
export async function toggleFlag(photo: Photo, color = gallery.activeFlag) {
    const wasOn = photo.flags.includes(color)
    setFlag(photo, color, !wasOn)

    try {
        const { active } = await api.toggleFlag(gallery.token, photo.id, color)
        setFlag(photo, color, active)
    } catch {
        setFlag(photo, color, wasOn)
        gallery.showToast('Could not save, please try again.')
    }
}
