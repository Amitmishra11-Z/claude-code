/**
 * Fake news detection and analysis module for Indic language content
 */

export interface FakeNewsAnalysisResult {
  score: number // 0-1, where 1 is most likely fake
  confidence: number // 0-1, confidence in the analysis
  flags: string[]
  details: {
    sensationalismScore: number
    emotionalLanguageScore: number
    claimCount: number
    verifiableEntities: number
  }
}

/**
 * Patterns that indicate sensationalism or unreliable content
 */
const SENSATIONALISM_PATTERNS = [
  /यह\s+(तुरंत|अब)\s+जानना\s+चाहिए/i, // Must know right now (Hindi)
  /एक\s+हमले|प्रकोप|घटना/i, // Explosion/incident language
  /विश्वास\s+नहीं|अविश्वसनीय/i, // Disbelief markers
  /सभी\s+को|हर\s+किसी\s+को/i, // Universalizing statements
]

const EMOTIONAL_MARKERS = [
  /भयानक|भयावह|डरावना/i, // Terrible/horrible (Hindi)
  /मज़बूरी|दर्द|पीड़ा/i, // Pain/suffering markers
  /क्रोध|नाराज़गी|गुस्सा/i, // Anger markers
  /अन्याय|अत्याचार/i, // Injustice markers
]

/**
 * Analyze text for fake news indicators
 */
export function analyzeFakeNewsIndicators(
  text: string,
): FakeNewsAnalysisResult {
  const textLower = text.toLowerCase()

  // Count sensationalism patterns
  let sensationalismCount = 0
  for (const pattern of SENSATIONALISM_PATTERNS) {
    const matches = text.match(pattern)
    if (matches) {
      sensationalismCount += matches.length
    }
  }

  // Count emotional language
  let emotionalCount = 0
  for (const pattern of EMOTIONAL_MARKERS) {
    const matches = text.match(pattern)
    if (matches) {
      emotionalCount += matches.length
    }
  }

  // Count sentences and claims
  const sentences = text.split(/[।.!?]+/).filter((s) => s.trim().length > 0)
  const claimCount = sentences.length

  // Simple entity recognition (words in quotes or capitalized)
  const entityPattern = /[""']([^""']+)[""']|(?:^|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/gm
  const entities = new Set(text.match(entityPattern) || [])
  const verifiableEntities = entities.size

  // Calculate scores
  const sensationalismScore = Math.min(
    1,
    sensationalismCount / Math.max(1, sentences.length),
  )
  const emotionalLanguageScore = Math.min(
    1,
    emotionalCount / Math.max(1, sentences.length),
  )

  // Combine scores (higher = more likely fake)
  const combinedScore = (sensationalismScore * 0.4 + emotionalLanguageScore * 0.3) * 0.7

  const flags: string[] = []
  if (sensationalismScore > 0.2) flags.push('High sensationalism detected')
  if (emotionalLanguageScore > 0.2) flags.push('Excessive emotional language')
  if (claimCount > 50)
    flags.push('Unusually high number of claims for article length')
  if (verifiableEntities < 3) flags.push('Few verifiable entities mentioned')

  return {
    score: combinedScore,
    confidence: Math.min(1, (sensationalismScore + emotionalLanguageScore) / 2),
    flags,
    details: {
      sensationalismScore,
      emotionalLanguageScore,
      claimCount,
      verifiableEntities,
    },
  }
}

/**
 * Check for consistency of entities across multiple texts
 */
export function checkEntityConsistency(texts: string[]): {
  consistent: boolean
  consistencyScore: number
  conflicts: string[]
} {
  if (texts.length < 2) {
    return {
      consistent: true,
      consistencyScore: 1.0,
      conflicts: [],
    }
  }

  // Simple implementation: check for contradictory patterns
  const conflicts: string[] = []

  // This would be enhanced with proper NER in production
  // For now, just check for obvious contradictions
  const hasContradictions = texts.some((text) =>
    /(?:नहीं|नहीं कहा|खंडन)/i.test(text),
  )

  return {
    consistent: !hasContradictions,
    consistencyScore: hasContradictions ? 0.5 : 0.9,
    conflicts: conflicts,
  }
}

/**
 * Detect temporal anomalies (unusual timing patterns)
 */
export function checkTemporalPatterns(publishDates: Date[]): {
  anomalousPattern: boolean
  clusteringScore: number
} {
  if (publishDates.length < 2) {
    return {
      anomalousPattern: false,
      clusteringScore: 0,
    }
  }

  // Sort by date
  const sorted = [...publishDates].sort(
    (a, b) => a.getTime() - b.getTime(),
  )

  // Calculate time differences between consecutive articles
  const timeDiffs: number[] = []
  for (let i = 1; i < sorted.length; i++) {
    const diff = sorted[i].getTime() - sorted[i - 1].getTime()
    timeDiffs.push(diff)
  }

  // Check if all articles come within a short timeframe
  const avgDiff =
    timeDiffs.reduce((a, b) => a + b, 0) / timeDiffs.length
  const shortTimeframe = avgDiff < 3600000 // 1 hour

  // Calculate clustering (standard deviation of time differences)
  const variance =
    timeDiffs.reduce((sum, diff) => sum + Math.pow(diff - avgDiff, 2), 0) /
    timeDiffs.length
  const stdDev = Math.sqrt(variance)
  const clusteringScore = Math.min(1, stdDev / (avgDiff || 1))

  return {
    anomalousPattern: shortTimeframe && timeDiffs.length > 3,
    clusteringScore,
  }
}

/**
 * Generate comprehensive fake news assessment
 */
export function assessCredibility(text: string): {
  score: number
  level: 'low' | 'medium' | 'high'
  recommendation: string
} {
  const analysis = analyzeFakeNewsIndicators(text)

  let level: 'low' | 'medium' | 'high'
  let recommendation: string

  if (analysis.score < 0.3) {
    level = 'high'
    recommendation = 'This content appears to be reliable based on current indicators.'
  } else if (analysis.score < 0.6) {
    level = 'medium'
    recommendation = 'This content has some concerning patterns. Verify claims independently.'
  } else {
    level = 'low'
    recommendation = 'This content shows strong indicators of misinformation. Verify before sharing.'
  }

  return {
    score: 1 - analysis.score, // Invert to make higher = more credible
    level,
    recommendation,
  }
}
