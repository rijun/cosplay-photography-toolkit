export interface FlagDef {
    /** Matches `Flag.color` server-side. */
    color: number
    label: string
    hex: string
    /** Used for the glow on active picker dots and lightbox buttons. */
    glow: string
}

/**
 * Order is render order: the five personal colors first, `final` last.
 */
export const FLAG_DEFS: readonly FlagDef[] = [
    { color: 1, label: 'rose', hex: '#d4857a', glow: 'rgba(212,133,122,0.35)' },
    { color: 2, label: 'lavender', hex: '#a888b8', glow: 'rgba(168,136,184,0.35)' },
    { color: 3, label: 'sage', hex: '#88a888', glow: 'rgba(136,168,136,0.35)' },
    { color: 4, label: 'sky', hex: '#7a9ab8', glow: 'rgba(122,154,184,0.35)' },
    { color: 5, label: 'amber', hex: '#c4a050', glow: 'rgba(196,160,80,0.35)' },
    { color: 0, label: 'final', hex: '#22a355', glow: 'rgba(34,163,85,0.35)' },
]

const byColor = new Map(FLAG_DEFS.map((flag) => [flag.color, flag]))

/** Lookup for rendering a photo's marks, where only the color is known. */
export function flagDef(color: number): FlagDef | undefined {
    return byColor.get(color)
}
