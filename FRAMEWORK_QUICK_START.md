# Indic Text Scraper Framework - Quick Start Guide

## What Was Built?

A production-ready framework for scraping, analyzing, and detecting fake news in Indic language content, fully integrated into the Claude Code CLI.

## Quick Start

### For End Users

```bash
# Use the interactive command
/indic-text-scraper

# Or use aliases
/scrape-indic
/indic-scraper
```

### For Developers

#### Import and Use Language Detection
```typescript
import { detectIndicLanguage } from './src/utils/indicLanguages/detection.js'

const text = "नमस्ते, यह हिंदी है।"
const result = detectIndicLanguage(text)
console.log(result.language)  // 'devanagari'
```

#### Import and Use Fake News Detection
```typescript
import { analyzeFakeNewsIndicators } from './src/utils/fakeNewsDetection/analyzer.js'

const text = "यह अविश्वसनीय खबर है!"
const analysis = analyzeFakeNewsIndicators(text)
console.log(analysis.score)  // Fake news likelihood (0-1)
```

#### Use the Scraper Tool
```typescript
import { IndicTextScraperTool } from './src/tools/IndicTextScraperTool/index.js'

// The tool is registered and available in the CLI
// Access via agents or the command interface
```

## Core Modules

| Module | Location | Purpose |
|--------|----------|---------|
| Language Detection | `src/utils/indicLanguages/detection.ts` | Identify Indic languages |
| Text Normalization | `src/utils/indicLanguages/normalization.ts` | Clean and analyze text |
| Fake News Detection | `src/utils/fakeNewsDetection/analyzer.ts` | Detect misinformation |
| Web Scrapers | `src/utils/indicLanguages/scrapers/` | Scrape website content |
| Core Tool | `src/tools/IndicTextScraperTool/` | CLI tool implementation |
| Command | `src/commands/indic-text-scraper/` | User interface |

## Supported Indic Languages

- Hindi (Devanagari)
- Bengali
- Punjabi (Gurmukhi)
- Gujarati
- Odia
- Tamil
- Telugu
- Kannada
- Malayalam
- Sinhala

## Key Capabilities

### 1. Language Identification
Automatically detect which Indic language a text is written in with confidence scoring.

### 2. Text Analysis
Extract key metrics:
- Character count
- Word count
- Line count
- Average word length
- Unique characters

### 3. Fake News Detection
Analyzes text for:
- Sensationalism markers
- Emotional language
- Entity consistency
- Temporal anomalies
- Spam patterns

### 4. Content Scraping
- Adapter-based architecture
- Website-specific scrapers
- Generic fallback scraper
- URL validation and permissions
- Batch processing

### 5. Data Export
Export results in:
- JSON (for programmatic use)
- CSV (for spreadsheet analysis)
- Text (for human review)

## Architecture

```
┌─────────────────────────────────────────┐
│     Claude Code CLI Framework           │
│  (Tools System, Commands System)        │
└──────────┬──────────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐  ┌──────────────┐
│ Tool    │  │ Command      │
│ (Agentic)   │ (Interactive)│
└────┬────┘  └───────┬──────┘
     │               │
     └───────┬───────┘
             │
      ┌──────▼───────┐
      │ Language     │
      │ Detection    │
      └──────────────┘
             │
      ┌──────┴────────┐
      │               │
      ▼               ▼
┌──────────────┐ ┌─────────────┐
│ Text         │ │ Fake News   │
│ Normalization│ │ Detection   │
└──────────────┘ └─────────────┘
             │
      ┌──────▼───────┐
      │ Web Scrapers │
      │ (Adapters)   │
      └──────────────┘
```

## Usage Examples

### Detect Language
```typescript
import { detectIndicLanguage } from './src/utils/indicLanguages/detection.js'

detectIndicLanguage("नमस्ते")
// Returns: { language: 'devanagari', confidence: 1.0, ... }
```

### Analyze Fake News
```typescript
import { analyzeFakeNewsIndicators } from './src/utils/fakeNewsDetection/analyzer.js'

analyzeFakeNewsIndicators("यह भयानक खबर है!")
// Returns: { score: 0.6, flags: ['Excessive emotional language'], ... }
```

### Normalize Text
```typescript
import { normalizeIndicText } from './src/utils/indicLanguages/normalization.js'

normalizeIndicText("नमस्ते    यह    पाठ    है।")
// Returns: "नमस्ते यह पाठ है।"
```

### Process URLs
```typescript
import { batchScrapeUrls } from './src/commands/indic-text-scraper/utils.js'

await batchScrapeUrls(
  ['https://bbc.com/hindi/...', 'https://ndtv.com/...'],
  { analyzeFakeNews: true }
)
```

## Integration with CLI

The framework is automatically integrated:

1. **Tools**: Available to agents via `IndicTextScraperTool`
2. **Commands**: Available to users via `/indic-text-scraper`
3. **Permissions**: Respects CLI permission system
4. **Context**: Uses CLI context and state management

## Performance

- **Language Detection**: O(n) where n = text length
- **Pattern Matching**: O(m) where m = number of patterns
- **Batch Processing**: Parallel URL processing supported
- **Memory**: Minimal footprint, no ML models loaded

## Security

- URL validation and sanitization
- Permission checking for domain access
- robots.txt compliance
- Rate limiting support
- No sensitive data storage

## Extensibility

### Add a New Website Adapter
```typescript
export class MyNewsAdapter extends ScraperAdapter {
  canHandle(url: string): boolean {
    return url.includes('mynews.com')
  }
  
  async scrape(): Promise<ScrapeResult> {
    // Custom implementation
  }
}
```

### Add Language Detection Patterns
Modify `SENSATIONALISM_PATTERNS` or `EMOTIONAL_MARKERS` in the analyzer module.

### Add New Indic Language
Add Unicode range to `INDIC_RANGES` in the detection module.

## Documentation

- **INDIC_SCRAPER_FRAMEWORK.md** - Complete framework documentation
- **IMPLEMENTATION_SUMMARY.md** - Technical details and design
- **examples.ts** - Code examples and test utilities

## What's Next?

### Enhancements to Consider
1. Add HTML parsing with cheerio library
2. Integrate ML models for improved accuracy
3. Connect to fact-checking APIs
4. Add historical data storage
5. Implement advanced NER
6. Add transliteration support

### Testing
Run the example tests:
```typescript
import { testFullIntegration } from './src/utils/indicLanguages/examples.js'
await testFullIntegration()
```

## Support

For questions or improvements:
1. Check the documentation files
2. Review the examples.ts file
3. Examine existing code for patterns
4. Follow Claude Code CLI conventions

## Summary

You now have a complete, production-ready framework for:
- ✅ Detecting Indic languages
- ✅ Analyzing text for misinformation
- ✅ Scraping web content
- ✅ Processing and exporting data
- ✅ Extending with custom adapters

All fully integrated into Claude Code CLI!
