/**
 * Base adapter for website scraping
 */

export interface ScrapedContent {
  url: string
  title?: string
  content: string
  author?: string
  publishedDate?: string
  language: string
  metadata: Record<string, unknown>
}

export interface ScraperOptions {
  timeout?: number
  maxRetries?: number
  userAgent?: string
}

export interface ScrapeResult {
  success: boolean
  data?: ScrapedContent
  error?: string
}

/**
 * Base adapter class for implementing website-specific scrapers
 */
export abstract class ScraperAdapter {
  protected url: string
  protected options: ScraperOptions

  constructor(url: string, options: ScraperOptions = {}) {
    this.url = url
    this.options = {
      timeout: 10000,
      maxRetries: 3,
      userAgent:
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      ...options,
    }
  }

  abstract canHandle(url: string): boolean
  abstract scrape(): Promise<ScrapeResult>

  /**
   * Validate if URL is appropriate for scraping
   */
  protected validateUrl(url: string): boolean {
    try {
      const parsed = new URL(url)
      // Don't scrape local files
      if (parsed.protocol === 'file:' || parsed.protocol === 'data:') {
        return false
      }
      return true
    } catch {
      return false
    }
  }

  /**
   * Extract domain from URL
   */
  protected getDomain(url: string): string {
    try {
      return new URL(url).hostname
    } catch {
      return ''
    }
  }
}

/**
 * Generic HTML scraper for news websites
 */
export class GenericNewsScraperAdapter extends ScraperAdapter {
  canHandle(_url: string): boolean {
    // Generic scraper handles most URLs
    return this.validateUrl(this.url)
  }

  async scrape(): Promise<ScrapeResult> {
    try {
      // This is a stub - actual implementation would use fetch + HTML parsing
      // For now, we're returning an error as we need cheerio or similar
      return {
        success: false,
        error: 'Generic scraper requires HTML parsing library',
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }
    }
  }
}

/**
 * Scraper registry for managing multiple adapters
 */
export class ScraperRegistry {
  private adapters: ScraperAdapter[] = []

  registerAdapter(adapter: ScraperAdapter): void {
    this.adapters.push(adapter)
  }

  async scrape(url: string, options?: ScraperOptions): Promise<ScrapeResult> {
    const adapter =
      this.adapters.find((a) => a.canHandle(url)) ||
      new GenericNewsScraperAdapter(url, options)

    return adapter.scrape()
  }

  getAdapters(): ScraperAdapter[] {
    return [...this.adapters]
  }
}

// Global registry instance
export const globalScraperRegistry = new ScraperRegistry()
