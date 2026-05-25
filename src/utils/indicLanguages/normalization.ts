/**
 * Text normalization and preprocessing for Indic languages
 */

// Common Indic diacritical marks and combining characters
const DIACRITICAL_MARKS = {
  devanagari: [0x0900, 0x0903, 0x0904, 0x093c, 0x0941, 0x0942, 0x0943, 0x0944],
  bengali: [0x0981, 0x0982, 0x0983, 0x09bc, 0x09be, 0x09d7],
  gujarati: [0x0a81, 0x0a82, 0x0a83, 0x0abc],
}

/**
 * Normalize Indic text by removing extra whitespace and standardizing format
 */
export function normalizeIndicText(text: string): string {
  // Remove excessive whitespace
  let normalized = text.replace(/\s+/g, ' ').trim()

  // Remove common non-content characters
  normalized = normalized.replace(/[^\p{L}\p{N}\s.,!?;:\-'"]/gu, '')

  return normalized
}

/**
 * Remove diacritical marks from Indic text while preserving base characters
 * Note: This is a simplified version that removes combining characters
 */
export function removeDiacriticals(text: string): string {
  // Remove combining diacritical marks and modifiers
  return text.replace(/[\u0300-\u036f\u0485-\u0486\u064b-\u0655]/g, '')
}

/**
 * Convert text to lowercase (works with Indic scripts)
 */
export function toLowerCaseIndic(text: string): string {
  // JavaScript's built-in toLowerCase works well with Unicode
  return text.toLowerCase()
}

/**
 * Extract words from Indic text
 */
export function extractWords(text: string): string[] {
  const normalized = normalizeIndicText(text)
  return normalized.split(/\s+/).filter((word) => word.length > 0)
}

/**
 * Calculate text statistics for Indic content
 */
export interface TextStatistics {
  characterCount: number
  wordCount: number
  lineCount: number
  averageWordLength: number
  uniqueCharacters: number
}

export function calculateTextStatistics(text: string): TextStatistics {
  const lines = text.split('\n')
  const words = extractWords(text)
  const uniqueChars = new Set(text).size

  return {
    characterCount: text.length,
    wordCount: words.length,
    lineCount: lines.length,
    averageWordLength:
      words.length > 0
        ? words.reduce((sum, word) => sum + word.length, 0) / words.length
        : 0,
    uniqueCharacters: uniqueChars,
  }
}

/**
 * Truncate text to maximum length while preserving word boundaries
 */
export function truncateText(
  text: string,
  maxLength: number,
  suffix = '...',
): string {
  if (text.length <= maxLength) {
    return text
  }

  const truncated = text.substring(0, maxLength - suffix.length)
  const lastSpaceIndex = truncated.lastIndexOf(' ')

  if (lastSpaceIndex > 0) {
    return truncated.substring(0, lastSpaceIndex) + suffix
  }

  return truncated + suffix
}

/**
 * Detect if text has unusual character patterns (potential spam/bot content)
 */
export function detectRepetitivePatterns(
  text: string,
  threshold = 0.4,
): boolean {
  if (text.length < 10) return false

  // Count character frequencies
  const charFreq = new Map<string, number>()
  for (const char of text) {
    charFreq.set(char, (charFreq.get(char) || 0) + 1)
  }

  // Find most frequent character ratio
  const maxFreq = Math.max(...charFreq.values())
  const ratio = maxFreq / text.length

  return ratio > threshold
}
