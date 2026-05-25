/**
 * Indic language detection and identification utilities
 */

// Unicode ranges for major Indic scripts
const INDIC_RANGES = {
  devanagari: { start: 0x0900, end: 0x097f }, // Hindi, Sanskrit, Marathi, etc.
  bengali: { start: 0x0980, end: 0x09ff }, // Bengali, Assamese
  gurmukhi: { start: 0x0a00, end: 0x0a7f }, // Punjabi
  gujarati: { start: 0x0a80, end: 0x0aff },
  oriya: { start: 0x0b00, end: 0x0b7f },
  tamil: { start: 0x0b80, end: 0x0bff },
  telugu: { start: 0x0c00, end: 0x0c7f },
  kannada: { start: 0x0c80, end: 0x0cff },
  malayalam: { start: 0x0d00, end: 0x0d7f },
  sinhala: { start: 0x0d80, end: 0x0dff },
}

export type IndicLanguageType = keyof typeof INDIC_RANGES

export interface LanguageDetectionResult {
  language: IndicLanguageType | 'unknown'
  confidence: number
  scriptCount: number
  totalCharacters: number
}

/**
 * Detect Indic language from text based on Unicode script ranges
 */
export function detectIndicLanguage(text: string): LanguageDetectionResult {
  if (!text || text.length === 0) {
    return {
      language: 'unknown',
      confidence: 0,
      scriptCount: 0,
      totalCharacters: 0,
    }
  }

  const scriptCounts: Record<IndicLanguageType, number> = {
    devanagari: 0,
    bengali: 0,
    gurmukhi: 0,
    gujarati: 0,
    oriya: 0,
    tamil: 0,
    telugu: 0,
    kannada: 0,
    malayalam: 0,
    sinhala: 0,
  }

  let totalIndicChars = 0

  for (const char of text) {
    const code = char.charCodeAt(0)

    for (const [lang, range] of Object.entries(INDIC_RANGES)) {
      if (code >= range.start && code <= range.end) {
        scriptCounts[lang as IndicLanguageType]++
        totalIndicChars++
      }
    }
  }

  if (totalIndicChars === 0) {
    return {
      language: 'unknown',
      confidence: 0,
      scriptCount: 0,
      totalCharacters: text.length,
    }
  }

  // Find language with highest count
  let detectedLanguage: IndicLanguageType = 'devanagari'
  let maxCount = 0

  for (const [lang, count] of Object.entries(scriptCounts)) {
    if (count > maxCount) {
      maxCount = count
      detectedLanguage = lang as IndicLanguageType
    }
  }

  const confidence = totalIndicChars / text.length

  return {
    language: detectedLanguage,
    confidence,
    scriptCount: Object.values(scriptCounts).filter((c) => c > 0).length,
    totalCharacters: text.length,
  }
}

/**
 * Check if text contains significant Indic language content
 */
export function hasIndicLanguageContent(
  text: string,
  threshold = 0.3,
): boolean {
  const result = detectIndicLanguage(text)
  return result.confidence >= threshold
}

/**
 * Get human-readable name for Indic language
 */
export function getLanguageName(lang: IndicLanguageType): string {
  const names: Record<IndicLanguageType, string> = {
    devanagari: 'Hindi/Sanskrit',
    bengali: 'Bengali',
    gurmukhi: 'Punjabi',
    gujarati: 'Gujarati',
    oriya: 'Odia',
    tamil: 'Tamil',
    telugu: 'Telugu',
    kannada: 'Kannada',
    malayalam: 'Malayalam',
    sinhala: 'Sinhala',
  }
  return names[lang]
}

/**
 * Extract only Indic language characters from text
 */
export function extractIndicText(text: string): string {
  return text
    .split('')
    .filter((char) => {
      const code = char.charCodeAt(0)
      return Object.values(INDIC_RANGES).some(
        (range) => code >= range.start && code <= range.end,
      )
    })
    .join('')
}
