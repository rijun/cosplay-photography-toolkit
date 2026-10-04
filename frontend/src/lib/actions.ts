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

const POLL_MS = 1500

// A running build that makes no progress for this long has stalled. Outlasts
// Nextcloud's 60s read timeout, which fails the job server-side on its own.
const STALL_MS = 90_000

// Neither is state: nothing renders from a timer handle or the download's id.
let pollTimer: ReturnType<typeof setTimeout> | undefined
let zipId: string | undefined

function stopPolling() {
    clearTimeout(pollTimer)
    pollTimer = undefined
}

function failDownload() {
    stopPolling()
    gallery.zip.active = false
    gallery.showToast('Download failed, please try again')
    // A stalled job may still be alive server-side; stop it building a zip nobody waits for.
    abandon()
}

function abandon() {
    if (!zipId) return
    // Best effort: the user has already moved on.
    api.cancelDownload(gallery.token, zipId).catch(() => {})
    zipId = undefined
}

/**
 * Chained timeouts rather than setInterval: a slow response would otherwise let
 * requests overlap and arrive out of order.
 */
function poll(downloadId: string) {
    let lastDone = -1
    let stalledSince = Date.now()

    const tick = async () => {
        try {
            const progress = await api.downloadProgress(gallery.token, downloadId)
            gallery.zip.done = progress.progress_current
            gallery.zip.total = progress.progress_total

            const finalizing = progress.progress_total > 0 && progress.progress_current >= progress.progress_total
            // Only zipping can stall: a queued job waits for a free worker, and the
            // R2 upload reports no progress and enforces its own limit.
            if (progress.status !== 'processing' || finalizing || progress.progress_current !== lastDone) {
                lastDone = progress.progress_current
                stalledSince = Date.now()
            } else if (Date.now() - stalledSince > STALL_MS) {
                return failDownload()
            }

            if (progress.status === 'completed') {
                stopPolling()
                gallery.zip.active = false
                zipId = undefined
                window.location.href = api.downloadFileUrl(gallery.token, downloadId)
                return
            }
            if (progress.status === 'failed') {
                zipId = undefined
                return failDownload()
            }
        } catch {
            // Network hiccup is not a failed zip; keep asking.
        }
        pollTimer = setTimeout(tick, POLL_MS)
    }

    pollTimer = setTimeout(tick, POLL_MS)
}

/** Omit `photoIds` to download the whole gallery, ignoring any active filter. */
export async function startDownload(photoIds?: number[]) {
    stopPolling()
    gallery.zip.active = true
    gallery.zip.done = 0
    gallery.zip.total = photoIds ? photoIds.length : gallery.photos.length

    try {
        const { download_id } = await api.startDownload(gallery.token, photoIds ?? null)
        zipId = download_id
        // Canceled while the start request was in flight.
        if (!gallery.zip.active) return abandon()
        poll(download_id)
    } catch {
        failDownload()
    }
}

export function cancelDownload() {
    stopPolling()
    gallery.zip.active = false
    abandon()
}

export function toggleSelectMode() {
    gallery.selectMode = !gallery.selectMode
    if (!gallery.selectMode) gallery.selected = []
}

export function toggleSelect(photoId: number) {
    const index = gallery.selected.indexOf(photoId)
    if (index === -1) gallery.selected.push(photoId)
    else gallery.selected.splice(index, 1)
}
