export interface Photo {
    id: number
    filename: string
    thumbnail_url: string
    preview_url: string
    flags: number[]
    is_edited: boolean
}