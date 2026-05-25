/**
 * Utilities for Indic Text Scraper Command
 */

import { detectIndicLanguage } from '../../utils/indicLanguages/detection.js'
import { analyzeFakeNewsIndicators } from '../../utils/fakeNewsDetection/analyzer.js'

export interface ScrapingOptions {
  urls: string[]
  analyzeFakeNews: boolean
  extractLanguage: boolean
  maxContentLength: number
  exportFormat: 'json' | 'csv' | 'text'
}

export interface ScrapingResult {
  url: string
  status: 'success' | 'error' | 'skipped'
  content?: string
  language?: string
  languageConfidence?: number
  fakeNewsScore?: number
  fakeNewsFlags?: string[]
  error?: string
  processingTime?: number
}

/**
 * Format results for display
 */
export function formatResults(results: ScrapingResult[]): string {
  let output = 'Scraping Results\n'
  output += '================\n\n'

  for (const result of results) {
    output += `URL: ${result.url}\n`
    output += `Status: ${result.status}\n`

    if (result.status === 'success') {
      output += `Language: ${result.language}\n`
      output += `Confidence: ${(result.languageConfidence || 0).toFixed(2)}\n`

      if (result.fakeNewsScore !== undefined) {
        output += `Fake News Score: ${result.fakeNewsScore.toFixed(2)}\n`
        if (result.fakeNewsFlags && result.fakeNewsFlags.length > 0) {
          output += `Flags: ${result.fakeNewsFlags.join(', ')}\n`
        }
      }

      if (result.content) {
        output += `Content Length: ${result.content.length} characters\n`
      }
    } else if (result.error) {
      output += `Error: ${result.error}\n`
    }

    output += '\n'
  }

  return output
}

/**
 * Validate URLs
 */
export function validateUrls(urls: string[]): {
  valid: string[]
  invalid: Array<{ url: string; reason: string }>
} {
  const valid: string[] = []
  const invalid: Array<{ url: string; reason: string }> = []

  for (const url of urls) {
    try {
      const parsed = new URL(url)
      if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
        valid.push(url)
      } else {
        invalid.push({
          url,
          reason: 'Only HTTP/HTTPS protocols are supported',
        })
      }
    } catch {
      invalid.push({
        url,
        reason: 'Invalid URL format',
      })
    }
  }

  return { valid, invalid }
}

/**
 * Export results to JSON format
 */
export function exportToJSON(results: ScrapingResult[]): string {
  return JSON.stringify(results, null, 2)
}

/**
 * Export results to CSV format
 */
export function exportToCSV(results: ScrapingResult[]): string {
  const headers = [
    'url',
    'status',
    'language',
    'confidence',
    'fakeNewsScore',
    'flags',
    'contentLength',
    'error',
  ]

  let csv = headers.join(',') + '\n'

  for (const result of results) {
    const row = [
      escapeCSV(result.url),
      result.status,
      result.language || '',
      result.languageConfidence?.toFixed(2) || '',
      result.fakeNewsScore?.toFixed(2) || '',
      escapeCSV((result.fakeNewsFlags || []).join(';')),
      result.content?.length || '',
      escapeCSV(result.error || ''),
    ]
    csv += row.join(',') + '\n'
  }

  return csv
}

/**
 * Escape CSV values
 */
function escapeCSV(value: string): string {
  if (value.includes(',') || value.includes('"') || value.includes('\n')) {
    return `"${value.replace(/"/g, '""')}"`
  }
  return value
}

/**
 * Batch process URLs
 */
export async function batchScrapeUrls(
  urls: string[],
  options: Partial<ScrapingOptions> = {},
): Promise<ScrapingResult[]> {
  const results: ScrapingResult[] = []

  for (const url of urls) {
    const startTime = Date.now()

    try {
      // This would call the actual tool in production
      // For now, returning a stub result
      const result: ScrapingResult = {
        url,
        status: 'success',
        language: 'devanagari',
        languageConfidence: 0.8,
        content: 'Sample content',
        processingTime: Date.now() - startTime,
      }

      if (options.analyzeFakeNews) {
        // Mock fake news analysis
        result.fakeNewsScore = Math.random() * 0.5
        result.fakeNewsFlags = ['Sample flag']
      }

      results.push(result)
    } catch (error) {
      results.push({
        url,
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
        processingTime: Date.now() - startTime,
      })
    }
  }

  return results
}
