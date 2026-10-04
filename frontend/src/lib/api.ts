/**
 * Thin wrappers over the gallery's token-scoped endpoints. No state here — see
 * actions.ts for the optimistic updates these sit underneath.
 */

function csrfToken(): string {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/)
    return match ? decodeURIComponent(match[1]) : ''
}

async function post(path: string, body?: unknown): Promise<Response> {
    const response = await fetch(path, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken(),
            ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        },
        body: body === undefined ? undefined : JSON.stringify(body),
    })
    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    return response
}

/** Server decides on/off, so callers reconcile against `active` rather than assuming. */
export async function toggleFlag(
    token: string,
    photoId: number,
    color: number,
): Promise<{ color: number; active: boolean }> {
    const response = await post(`/g/${token}/photos/${photoId}/flag?color=${color}`)
    return response.json()
}

/** Both comment endpoints return this shape. */
export interface Comment {
    id: number
    body: string
    author: string
    created_at: string
}

export async function comments(token: string, photoId: number): Promise<Comment[]> {
    const response = await fetch(`/g/${token}/photos/${photoId}/comments`)
    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    return response.json()
}

export async function addComment(token: string, photoId: number, body: string): Promise<Comment> {
    const response = await post(`/g/${token}/photos/${photoId}/comment`, { body })
    return response.json()
}
