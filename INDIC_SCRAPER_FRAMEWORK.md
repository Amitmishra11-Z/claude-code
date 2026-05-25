# Indic Text Scraper Framework

## Overview

This framework provides comprehensive tools for scraping, analyzing, and detecting fake news in Indic language content. It integrates seamlessly into the Claude Code CLI and provides both programmatic APIs and user-facing commands.

## Architecture

The framework is organized into several key modules:

### 1. Language Detection (`src/utils/indicLanguages/detection.ts`)

Detects and identifies Indic languages using Unicode character range analysis.

**Supported Languages:**
- Devanagari (Hindi, Sanskrit, Marathi)
- Bengali
- Gurmukhi (Punjabi)
- Gujarati
- Odia
- Tamil
- Telugu
- Kannada
- Malayalam
- Sinhala

**Key Functions:**
- `detectIndicLanguage(text)` - Returns language, confidence, and script count
- `hasIndicLanguageContent(text, threshold)` - Checks if text has significant Indic content
- `extractIndicText(text)` - Extracts only Indic characters
- `getLanguageName(language)` - Returns human-readable language name

### 2. Text Normalization (`src/utils/indicLanguages/normalization.ts`)

Handles text preprocessing and normalization for Indic scripts.

**Key Functions:**
- `normalizeIndicText(text)` - Removes extra whitespace and standardizes format
- `removeDiacriticals(text)` - Removes diacritical marks
- `extractWords(text)` - Splits text into words
- `calculateTextStatistics(text)` - Returns character, word, and line counts
- `truncateText(text, maxLength)` - Truncates while preserving word boundaries
- `detectRepetitivePatterns(text)` - Detects spam/bot content patterns

### 3. Fake News Detection (`src/utils/fakeNewsDetection/analyzer.ts`)

Analyzes text for indicators of misinformation and unreliable content.

**Key Functions:**
- `analyzeFakeNewsIndicators(text)` - Returns fake news score and flags
- `checkEntityConsistency(texts)` - Verifies consistency across multiple texts
- `checkTemporalPatterns(dates)` - Detects unusual timing patterns
- `assessCredibility(text)` - Provides comprehensive credibility assessment

**Analyzed Patterns:**
- Sensationalism and clickbait language
- Emotional manipulation markers
- Entity consistency
- Temporal anomalies
- Repetitive patterns (spam detection)

### 4. Web Scraper Adapters (`src/utils/indicLanguages/scrapers/`)

Provides extensible adapter pattern for website-specific scrapers.

**Base Adapter Pattern:**
- `ScraperAdapter` - Abstract base class for implementing custom scrapers
- `GenericNewsScraperAdapter` - Fallback generic scraper
- `ScraperRegistry` - Manages multiple adapter instances

**Implemented Adapters:**
- `BBCHindiAdapter` - BBC Hindi website
- `NDTVAdapter` - NDTV India
- `IndiaTodayAdapter` - India Today
- `TheHinduAdapter` - The Hindu

### 5. Core Tool (`src/tools/IndicTextScraperTool/`)

The main tool that integrates all components following the Claude Code CLI `buildTool()` pattern.

**Input Schema:**
```typescript
{
  url: string          // URL to scrape
  maxLength: number    // Max content length (default: 50000)
  analyzeFakeNews: boolean  // Enable fake news analysis
  extractLanguage: boolean  // Enable language detection
}
```

**Output Schema:**
```typescript
{
  url: string
  success: boolean
  content: string
  contentLength: number
  language: {
    detected: string
    confidence: number
    hasIndicContent: boolean
  }
  statistics: {
    characterCount: number
    wordCount: number
    lineCount: number
  }
  fakeNewsAnalysis?: {
    score: number
    flags: string[]
  }
  error?: string
}
```

### 6. User Command (`src/commands/indic-text-scraper/`)

Interactive command for end-users to scrape and analyze content.

**Command:** `/indic-text-scraper`

**Aliases:** `scrape-indic`, `indic-scraper`

**Features:**
- Single URL scraping
- Batch URL processing
- Interactive configuration
- Export to JSON/CSV
- Real-time progress updates

## Usage Examples

### Programmatic API

#### Language Detection
```typescript
import { detectIndicLanguage, hasIndicLanguageContent } from 'src/utils/indicLanguages/detection.js'

const text = "नमस्ते, यह एक हिंदी पाठ है।"
const result = detectIndicLanguage(text)
console.log(result.language)      // 'devanagari'
console.log(result.confidence)    // 0.95
```

#### Text Normalization
```typescript
import { normalizeIndicText, calculateTextStatistics } from 'src/utils/indicLanguages/normalization.js'

const text = "नमस्ते   यह   एक   पाठ   है।"
const normalized = normalizeIndicText(text)
const stats = calculateTextStatistics(normalized)
```

#### Fake News Detection
```typescript
import { analyzeFakeNewsIndicators, assessCredibility } from 'src/utils/fakeNewsDetection/analyzer.js'

const text = "यह अविश्वसनीय खबर है जो आपको तुरंत जानना चाहिए!"
const analysis = analyzeFakeNewsIndicators(text)
const assessment = assessCredibility(text)
console.log(assessment.level)  // 'low', 'medium', or 'high'
```

#### Web Scraping
```typescript
import { globalScraperRegistry } from 'src/utils/indicLanguages/scrapers/BaseAdapter.js'

const result = await globalScraperRegistry.scrape('https://bbc.com/hindi/...')
if (result.success) {
  console.log(result.data?.content)
}
```

### CLI Command

```bash
# Interactive mode
/indic-text-scraper

# Or use aliases
/scrape-indic
/indic-scraper
```

## Integration with Claude Code CLI

The framework is fully integrated into the Claude Code CLI:

1. **As a Tool:** Available via `IndicTextScraperTool` for agent use
2. **As a Command:** Available via `/indic-text-scraper` command
3. **Automatic Language Detection:** Works alongside existing tools
4. **Permission Management:** Respects CLI permission system

## Key Features

### 1. Multi-Site Support
Extensible adapter pattern allows easy addition of new website scrapers:
```typescript
class MyNewsAdapter extends ScraperAdapter {
  canHandle(url: string): boolean {
    return url.includes('mynews.com')
  }
  
  async scrape(): Promise<ScrapeResult> {
    // Custom scraping logic
  }
}
```

### 2. Language Intelligence
- Automatic detection of 10 major Indic languages
- Unicode-based character analysis (no ML required)
- Confidence scoring for detection accuracy
- Support for mixed-language content

### 3. Fake News Scoring
- Sensationalism pattern detection
- Emotional language markers
- Entity consistency checking
- Temporal pattern analysis
- Confidence-weighted scoring (0-1)

### 4. Batch Processing
Process multiple URLs with:
```typescript
const results = await batchScrapeUrls(
  ['url1', 'url2', 'url3'],
  { analyzeFakeNews: true, exportFormat: 'json' }
)
```

### 5. Data Export
- JSON format for programmatic processing
- CSV format for spreadsheet analysis
- Text format for human review

### 6. Performance
- Memoization of expensive computations
- Efficient Unicode-based language detection
- Optional caching for repeated queries
- Rate limiting support

### 7. Security & Compliance
- URL validation and sanitization
- Preapproved host lists
- robots.txt compliance checking
- User confirmation for custom domains
- Rate limiting to avoid server overload

## File Structure

```
src/
├── tools/
│   └── IndicTextScraperTool/
│       ├── IndicTextScraperTool.ts
│       └── index.ts
├── commands/
│   └── indic-text-scraper/
│       ├── scraper.tsx
│       ├── index.tsx
│       └── utils.ts
└── utils/
    ├── indicLanguages/
    │   ├── detection.ts
    │   ├── normalization.ts
    │   ├── index.ts
    │   └── scrapers/
    │       ├── BaseAdapter.ts
    │       ├── NewsAdapters.ts
    │       └── index.ts
    └── fakeNewsDetection/
        ├── analyzer.ts
        └── index.ts
```

## Future Enhancements

1. **HTML Parsing Integration**
   - Add cheerio for HTML parsing
   - Support for JavaScript-rendered content via Playwright
   - DOM-based content extraction

2. **Advanced NLP**
   - Proper Named Entity Recognition (NER)
   - Sentiment analysis with Indic language models
   - Semantic similarity checking

3. **Historical Analysis**
   - Cross-reference with fact-checking databases
   - Temporal clustering of similar articles
   - Source reliability scoring

4. **Extended Language Support**
   - Additional Indic scripts
   - Mixed-script detection
   - Transliteration support

5. **Machine Learning Integration**
   - Training on labeled fake news datasets
   - Feature extraction pipelines
   - Model serving integration

## Development

### Adding a New Website Adapter

1. Create a new adapter class extending `ScraperAdapter`:
```typescript
export class CustomNewsAdapter extends ScraperAdapter {
  canHandle(url: string): boolean {
    return url.includes('custom.news')
  }
  
  async scrape(): Promise<ScrapeResult> {
    // Implement scraping logic
  }
}
```

2. Register with the global registry:
```typescript
globalScraperRegistry.registerAdapter(new CustomNewsAdapter(url))
```

### Adding Language Detection Patterns

Update `INDIC_RANGES` in `detection.ts` to add new Unicode ranges for additional scripts.

### Customizing Fake News Patterns

Modify `SENSATIONALISM_PATTERNS` and `EMOTIONAL_MARKERS` in `analyzer.ts` to add new detection patterns.

## Testing

The framework includes utilities for testing:
- Unit test examples in each module
- Mock scrapers for development
- Test data generators
- Integration test helpers

## Limitations & Future Work

**Current Limitations:**
1. HTML parsing requires external library (currently stubbed)
2. No ML-based models (heuristic-based only)
3. Limited website adapters (expandable)
4. No transliteration support yet

**Future Improvements:**
1. Full HTML parsing implementation
2. Integration with ML models for accuracy
3. More website-specific adapters
4. Advanced entity recognition
5. Cross-reference with fact-checking APIs

## License

This framework is part of the Claude Code CLI and follows the same license.

## Support

For issues, questions, or contributions, please follow the Claude Code CLI contribution guidelines.
