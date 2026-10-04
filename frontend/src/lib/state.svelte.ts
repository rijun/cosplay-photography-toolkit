import type { Photo } from './photo'

export type EditedFilter = 'all' | 'originals' | 'edited'

const DEFAULT_FLAG = 1

const TOAST_MS = 3000

const flagKey = (token: string) => `gallery-flag-${token}`

function readStoredFlag(token: string): number {
    try {
        const raw = localStorage.getItem(flagKey(token))
        // Guard the empty cases: Number(null) and Number('') are both 0, which is
        // a valid color ("final") and would silently win.
        if (raw === null || raw === '') return DEFAULT_FLAG
        const color = Number(raw)
        return Number.isInteger(color) && color >= 0 && color <= 5 ? color : DEFAULT_FLAG
    } catch {
        return DEFAULT_FLAG
    }
}

/**
 * Shared gallery state. Components import `gallery` and read or write it
 * directly, so no stores, no context, no prop drilling.
 *
 * Derived values are getters rather than `$derived` exports: reads go through
 * property access, so they happen inside the consumer's reactive context. A bare
 * `export const x = $derived(...)` binds importers to a value and may not track.
 */
class GalleryState {
    // Set once by hydrate(); never changes afterward, so not reactive.
    #token: string | null = null

    // Private so every writing goes through the setter and gets persisted.
    #activeFlag = $state(DEFAULT_FLAG)

    // A timer handle, not state: nothing renders from it.
    #toastTimer: ReturnType<typeof setTimeout> | undefined

    photos = $state<Photo[]>([])

    filterFlags = $state<number[]>([])
    editedFilter = $state<EditedFilter>('all')

    selectMode = $state(false)
    selected = $state<number[]>([])

    // Index into `visible`, not `photos`, as navigation walks the filtered set.
    lightboxIndex = $state<number | null>(null)

    toast = $state<string | null>(null)

    zip = $state({ active: false, done: 0, total: 0 })

    get visible(): Photo[] {
        return this.photos.filter((photo) => {
            if (this.filterFlags.length > 0 && !this.filterFlags.some((f) => photo.flags.includes(f))) {
                return false
            }
            if (this.editedFilter === 'edited' && !photo.is_edited) return false
            if (this.editedFilter === 'originals' && photo.is_edited) return false
            return true
        })
    }

    get lightboxOpen(): boolean {
        return this.lightboxIndex !== null
    }

    get lightboxPhoto(): Photo | null {
        if (this.lightboxIndex === null) return null
        return this.visible[this.lightboxIndex] ?? null
    }

    /** Whether to render the originals/edited filter bar at all. */
    get hasEdited(): boolean {
        return this.photos.some((photo) => photo.is_edited)
    }

    isSelected(id: number): boolean {
        return this.selected.includes(id)
    }

    /** Transient message, auto-dismissed. Replaces any message still showing. */
    showToast(message: string) {
        this.toast = message
        clearTimeout(this.#toastTimer)
        this.#toastTimer = setTimeout(() => (this.toast = null), TOAST_MS)
    }

    /** Throws rather than silently using an empty token in API URLs. */
    get token(): string {
        if (this.#token === null) {
            throw new Error('gallery.hydrate() has not run: no token available')
        }
        return this.#token
    }

    /** The color this visitor marks with. Assigning persists the choice. */
    get activeFlag(): number {
        return this.#activeFlag
    }

    set activeFlag(color: number) {
        this.#activeFlag = color
        try {
            localStorage.setItem(flagKey(this.token), String(color))
        } catch {
            // Storage unavailable (private mode, blocked). Not worth failing over.
        }
    }

    /** Called once from the entry, before anything reads the state. */
    hydrate(token: string, photos: Photo[]) {
        if (this.#token !== null) {
            throw new Error('gallery.hydrate() called twice')
        }
        this.#token = token
        this.photos = photos
        this.#activeFlag = readStoredFlag(token)
    }
}

export const gallery = new GalleryState()
