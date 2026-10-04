/**
 * Mirrors the dicts built in `view_gallery`. TypeScript cannot check that,
 * so a renamed field here fails silently as `undefined` at runtime.
 */
export interface Photo {
    id: number
    filename: string
    thumbnail_url: string
    preview_url: string
    flags: number[]
    is_edited: boolean
    comment_count: number
}
