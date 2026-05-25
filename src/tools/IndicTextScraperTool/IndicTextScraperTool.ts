/**
 * Indic Text Scraper Tool - Core implementation following buildTool pattern
 */

import { z } from 'zod/v4'
import { buildTool, type ToolDef } from '../../Tool.js'
import { lazySchema } from '../../utils/lazySchema.js'
import {
  detectIndicLanguage,
  hasIndicLanguageContent,
} from '../../utils/indicLanguages/detection.js'
import {
  normalizeIndicText,
  calculateTextStatistics,
} from '../../utils/indicLanguages/normalization.js'
import { analyzeFakeNewsIndicators } from '../../utils/fakeNewsDetection/analyzer.js'
import type { PermissionDecision } from '../../utils/permissions/PermissionResult.js'

const TOOL_NAME = 'IndicTextScraper'

const inputSchema = lazySchema(() =>
  z.strictObject({
    url: z
      .string()
      .url()
      .describe('URL of the webpage to scrape content from'),
    maxLength: z
      .number()
      .int()
      .positive()
      .default(50000)
      .describe('Maximum content length to extract in characters'),
    analyzeFakeNews: z
      .boolean()
      .default(true)
      .describe('Whether to analyze content for fake news indicators'),
    extractLanguage: z
      .boolean()
      .default(true)
      .describe('Whether to detect and extract Indic language content'),
  }),
)
type InputSchema = ReturnType<typeof inputSchema>
type Input = z.infer<InputSchema>

const outputSchema = lazySchema(() =>
  z.object({
    url: z.string().describe('The URL that was scraped'),
    success: z.boolean().describe('Whether scraping was successful'),
    content: z
      .string()
      .describe('Extracted text content from the webpage'),
    contentLength: z
      .number()
      .describe('Length of extracted content in characters'),
    language: z
      .object({
        detected: z
          .string()
          .describe('Detected primary Indic language'),
        confidence: z
          .number()
          .describe('Confidence score (0-1) for language detection'),
        hasIndicContent: z
          .boolean()
          .describe('Whether significant Indic language content was found'),
      })
      .describe('Language detection results'),
    statistics: z
      .object({
        characterCount: z.number().describe('Total characters'),
        wordCount: z.number().describe('Estimated word count'),
        lineCount: z.number().describe('Line count'),
      })
      .describe('Content statistics'),
    fakeNewsAnalysis: z
      .object({
        score: z.number().describe('Fake news likelihood (0-1)'),
        flags: z.array(z.string()).describe('Detected warning flags'),
      })
      .optional()
      .describe('Fake news analysis results if requested'),
    error: z
      .string()
      .optional()
      .describe('Error message if scraping failed'),
  }),
)
type OutputSchema = ReturnType<typeof outputSchema>

export type Output = z.infer<OutputSchema>

export const IndicTextScraperTool = buildTool({
  name: TOOL_NAME,
  searchHint: 'scrape and analyze Indic language text from websites',
  description: {
    type: 'text' as const,
    text: 'Scrape text content from websites and analyze for Indic language presence and fake news indicators',
  },
  async description(input) {
    const { url } = input as { url: string }
    try {
      const hostname = new URL(url).hostname
      return `Scraping Indic language content from ${hostname}`
    } catch {
      return 'Scraping webpage for Indic language content'
    }
  },
  userFacingName() {
    return 'Indic Text Scraper'
  },
  getActivityDescription(input) {
    const { url } = input as { url: string }
    try {
      const hostname = new URL(url).hostname
      return `Scraping ${hostname} for Indic content`
    } catch {
      return 'Scraping webpage for Indic content'
    }
  },
  get inputSchema(): InputSchema {
    return inputSchema()
  },
  get outputSchema(): OutputSchema {
    return outputSchema()
  },
  isConcurrencySafe() {
    return true
  },
  isReadOnly() {
    return true
  },
  toAutoClassifierInput(input) {
    return `Scrape Indic text from: ${(input as Input).url}`
  },
  async checkPermissions(input): Promise<PermissionDecision> {
    const { url } = input as { url: string }
    try {
      const parsedUrl = new URL(url)
      const hostname = parsedUrl.hostname

      // Allow common news sites
      const trustedDomains = [
        'bbc.com',
        'ndtv.com',
        'indiatoday.in',
        'thehindu.com',
        'hindustantimes.com',
        'wikipedia.org',
        'news.google.com',
      ]

      const isTrusted = trustedDomains.some((domain) =>
        hostname.includes(domain),
      )

      return {
        behavior: isTrusted ? 'allow' : 'ask',
        updatedInput: input,
        decisionReason: isTrusted
          ? { type: 'other', reason: 'Trusted news domain' }
          : { type: 'other', reason: 'Custom domain - user confirmation needed' },
      }
    } catch {
      return {
        behavior: 'ask',
        updatedInput: input,
        decisionReason: {
          type: 'other',
          reason: 'Invalid URL format',
        },
      }
    }
  },
  async execute(input): Promise<Output> {
    const { url, maxLength, analyzeFakeNews, extractLanguage } = input as Input

    try {
      // Fetch content from URL
      // Note: In production, this would use fetch() and HTML parsing
      // For now, returning a stub implementation

      const placeholderContent = 'Sample content placeholder'

      // Detect language if requested
      let languageResult = {
        detected: 'unknown',
        confidence: 0,
        hasIndicContent: false,
      }

      if (extractLanguage) {
        const detection = detectIndicLanguage(placeholderContent)
        languageResult = {
          detected: detection.language,
          confidence: detection.confidence,
          hasIndicContent: hasIndicLanguageContent(placeholderContent),
        }
      }

      // Calculate statistics
      const stats = calculateTextStatistics(placeholderContent)

      // Analyze for fake news
      let fakeNewsResult = undefined
      if (analyzeFakeNews && placeholderContent.length > 0) {
        const analysis = analyzeFakeNewsIndicators(placeholderContent)
        fakeNewsResult = {
          score: analysis.score,
          flags: analysis.flags,
        }
      }

      return {
        url,
        success: true,
        content: placeholderContent,
        contentLength: placeholderContent.length,
        language: languageResult,
        statistics: {
          characterCount: stats.characterCount,
          wordCount: stats.wordCount,
          lineCount: stats.lineCount,
        },
        fakeNewsAnalysis: fakeNewsResult,
      }
    } catch (error) {
      return {
        url,
        success: false,
        content: '',
        contentLength: 0,
        language: {
          detected: 'unknown',
          confidence: 0,
          hasIndicContent: false,
        },
        statistics: {
          characterCount: 0,
          wordCount: 0,
          lineCount: 0,
        },
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  },
})
