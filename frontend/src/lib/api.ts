/**
 * Thin wrappers over the gallery's token-scoped endpoints. No state here — see
 * actions.ts for the optimistic updates these sit underneath.
 */

function csrfToken(): string {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/)
    return match ? decodeURIComponent(match[1]) : ''
}

async function post(path: string): Promise<Response> {
    const response = await fetch(path, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken() },
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
