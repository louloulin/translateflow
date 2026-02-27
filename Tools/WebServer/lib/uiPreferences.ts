import { UiPreferences } from '@/types'

const UI_PREFS_STORAGE_KEY = 'ainiee_ui_prefs_v1'

/**
 * Returns the default UI preferences used when no saved state exists.
 */
export function getDefaultUiPreferences(): UiPreferences {
  return {
    contentWidthMode: 'fluid',
    density: 'comfortable',
    taskConsole: {
      splitRatio: 0.45,
      minTerminalPx: 260,
    },
    updatedAt: Date.now(),
  }
}

/**
 * Coerces and clamps a raw value into a valid UiPreferences structure.
 */
export function normalizeUiPreferences(raw: unknown): UiPreferences {
  const defaults = getDefaultUiPreferences()
  const obj = (raw && typeof raw === 'object') ? (raw as any) : {}

  const contentWidthMode = obj.contentWidthMode === 'contained' ? 'contained' : 'fluid'
  const density = obj.density === 'compact' ? 'compact' : 'comfortable'

  const splitRatioNum = typeof obj?.taskConsole?.splitRatio === 'number' ? obj.taskConsole.splitRatio : defaults.taskConsole.splitRatio
  const splitRatio = Math.min(0.8, Math.max(0.2, splitRatioNum))

  const minTerminalNum = typeof obj?.taskConsole?.minTerminalPx === 'number' ? obj.taskConsole.minTerminalPx : defaults.taskConsole.minTerminalPx
  const minTerminalPx = Math.min(800, Math.max(140, Math.floor(minTerminalNum)))

  const updatedAtNum = typeof obj.updatedAt === 'number' ? obj.updatedAt : Date.now()

  return {
    contentWidthMode,
    density,
    taskConsole: {
      splitRatio,
      minTerminalPx,
    },
    updatedAt: updatedAtNum,
  }
}

/**
 * Loads UI preferences from localStorage.
 */
export function loadUiPreferences(): UiPreferences {
  try {
    const s = localStorage.getItem(UI_PREFS_STORAGE_KEY)
    if (!s) return getDefaultUiPreferences()
    return normalizeUiPreferences(JSON.parse(s))
  } catch {
    return getDefaultUiPreferences()
  }
}

/**
 * Saves UI preferences to localStorage.
 */
export function saveUiPreferences(prefs: UiPreferences) {
  try {
    localStorage.setItem(UI_PREFS_STORAGE_KEY, JSON.stringify(prefs))
  } catch {
    return
  }
}

/**
 * Clears persisted UI preferences.
 */
export function clearUiPreferences() {
  try {
    localStorage.removeItem(UI_PREFS_STORAGE_KEY)
  } catch {
    return
  }
}

