/**
 * Test utilities and example usage for Indic Text Scraper Framework
 */

// Example 1: Language Detection
export function testLanguageDetection() {
  const samples = {
    hindi:
      'नमस्ते, यह एक हिंदी पाठ है। भारत की सरकार ने नई नीति घोषित की है।',
    bengali: 'নমস্কার, এটি একটি বাংলা পাঠ। ভারতের সরকার নতুন নীতি ঘোষণা করেছে।',
    tamil: 'வணக்கம், இது ஒரு தமிழ் உரை. இந்தியாவின் அரசு புதிய கொள்கையை அறிவித்தது.',
    telugu:
      'నమస్కారం, ఇది తెలుగు పాఠ్యం. భారతదేశ ప్రభుత్వం కొత్త విధానాన్ని ప్రకటించింది.',
    gujarati:
      'નમસ્તે, આ એક ગુજરાતી પાઠ છે. ભારતની સરકારે નવી નીતિ જાહેર કરી છે.',
    kannada:
      'ನಮಸ್ಕಾರ, ಇದು ಕನ್ನಡ ಪಠ್ಯವಾಗಿದೆ. ಭಾರತ ಸರ್ಕಾರ ಹೊಸ ನೀತಿಯನ್ನು ಘೋಷಿಸಿದೆ.',
  }

  console.log('Language Detection Test Results:')
  console.log('================================')

  for (const [lang, text] of Object.entries(samples)) {
    // This would use detectIndicLanguage in real usage
    console.log(`${lang}: "${text.substring(0, 30)}..."`)
  }
}

// Example 2: Text Normalization
export function testTextNormalization() {
  const messyTexts = [
    'नमस्ते    यह    एक    पाठ    है।',
    'বাংলা   পাঠ্য   একাধিক   স্থান   সহ।',
    'தமிழ் வரைபடம்  அதிக  இடைவெளி।',
  ]

  console.log('Text Normalization Test Results:')
  console.log('================================')

  for (const text of messyTexts) {
    // This would use normalizeIndicText in real usage
    console.log(`Input: "${text}"`)
    console.log(`Expected: Normalized without extra spaces`)
    console.log('---')
  }
}

// Example 3: Fake News Detection
export function testFakeNewsDetection() {
  const texts = [
    {
      type: 'suspicious',
      content:
        'यह अविश्वसनीय खबर है जो आपको तुरंत जानना चाहिए! सभी को यह सुनना चाहिए!',
    },
    {
      type: 'normal',
      content:
        'सरकार ने आज नई नीति की घोषणा की। अधिकारी ने विवरण साझा किया।',
    },
    {
      type: 'emotional',
      content:
        'यह एक भयानक और दर्दनाक घटना है जिसने सभी को नाराज कर दिया।',
    },
  ]

  console.log('Fake News Detection Test Results:')
  console.log('==================================')

  for (const item of texts) {
    console.log(`Type: ${item.type}`)
    console.log(`Text: "${item.content}"`)
    console.log(`Expected: Analysis with sensationalism/emotional scores`)
    console.log('---')
  }
}

// Example 4: Batch Processing
export async function testBatchProcessing() {
  const urls = [
    'https://bbc.com/hindi/world-12345',
    'https://ndtv.com/india-news/article',
    'https://indiatoday.in/latest-news',
  ]

  console.log('Batch Processing Test Results:')
  console.log('==============================')
  console.log(`Processing ${urls.length} URLs...`)

  for (const url of urls) {
    console.log(`- Processing: ${url}`)
  }

  console.log('Expected: Array of results with language and fake news analysis')
}

// Example 5: Entity Consistency Check
export function testEntityConsistency() {
  const articles = [
    'राज कुमार ने कहा कि बिल पारित हुआ।',
    'राज कुमार ने खंडन किया और कहा बिल पारित नहीं हुआ।',
    'रिपोर्ट में राज कुमार को उद्धृत किया गया है।',
  ]

  console.log('Entity Consistency Check Results:')
  console.log('=================================')

  for (const article of articles) {
    console.log(`Article: "${article}"`)
  }

  console.log('Expected: Detection of contradictory statements')
}

// Example 6: Text Statistics
export function testTextStatistics() {
  const samples = [
    { name: 'Short', text: 'नमस्ते।' },
    {
      name: 'Medium',
      text: 'नमस्ते, यह एक मध्यम लंबाई का पाठ है जिसमें कई शब्द हैं।',
    },
    {
      name: 'Long',
      text: 'नमस्ते, यह एक लंबा पाठ है।' +
        ' इसमें कई पंक्तियां हैं।' +
        ' इसमें कई वाक्य हैं।' +
        ' इसमें कई शब्द हैं।' +
        ' इसका विश्लेषण किया जाएगा।',
    },
  ]

  console.log('Text Statistics Test Results:')
  console.log('=============================')

  for (const sample of samples) {
    console.log(`${sample.name}: "${sample.text.substring(0, 30)}..."`)
    console.log('Expected: Character count, word count, line count, avg word length')
    console.log('---')
  }
}

// Example 7: Permission Checking
export function testPermissionChecking() {
  const urls = [
    'https://bbc.com/hindi/news',
    'https://ndtv.com/india',
    'https://example-unknown.com/article',
  ]

  console.log('Permission Checking Test Results:')
  console.log('=================================')

  for (const url of urls) {
    console.log(`URL: ${url}`)
    console.log('Expected: Auto-allow for trusted domains, ask for custom domains')
    console.log('---')
  }
}

// Example 8: Adapter Pattern
export function testAdapterPattern() {
  const urls = [
    'https://bbc.com/hindi/world-123',
    'https://ndtv.com/india-news',
    'https://indiatoday.in/latest',
    'https://thehindu.com/news',
  ]

  console.log('Adapter Pattern Test Results:')
  console.log('============================')

  const expectedAdapters: Record<string, string> = {
    'https://bbc.com/hindi/world-123': 'BBCHindiAdapter',
    'https://ndtv.com/india-news': 'NDTVAdapter',
    'https://indiatoday.in/latest': 'IndiaTodayAdapter',
    'https://thehindu.com/news': 'TheHinduAdapter',
  }

  for (const url of urls) {
    const adapter = expectedAdapters[url] || 'GenericNewsScraperAdapter'
    console.log(`URL: ${url}`)
    console.log(`Expected Adapter: ${adapter}`)
    console.log('---')
  }
}

// Example 9: Export Formats
export function testExportFormats() {
  const sampleResults = [
    {
      url: 'https://bbc.com/hindi/news',
      status: 'success',
      language: 'hindi',
      confidence: 0.95,
      fakeNewsScore: 0.3,
    },
    {
      url: 'https://ndtv.com/india',
      status: 'success',
      language: 'hindi',
      confidence: 0.92,
      fakeNewsScore: 0.45,
    },
  ]

  console.log('Export Formats Test Results:')
  console.log('===========================')
  console.log('JSON Format:')
  console.log(JSON.stringify(sampleResults, null, 2))
  console.log('')
  console.log('CSV Format:')
  console.log('url,status,language,confidence,fakeNewsScore')
  for (const result of sampleResults) {
    console.log(`${result.url},${result.status},${result.language},${result.confidence},${result.fakeNewsScore}`)
  }
}

// Example 10: Integration Test
export async function testFullIntegration() {
  console.log('Full Integration Test:')
  console.log('====================')
  console.log('')
  console.log('1. Language Detection')
  testLanguageDetection()
  console.log('')
  console.log('2. Text Normalization')
  testTextNormalization()
  console.log('')
  console.log('3. Fake News Detection')
  testFakeNewsDetection()
  console.log('')
  console.log('4. Batch Processing')
  await testBatchProcessing()
  console.log('')
  console.log('5. Entity Consistency')
  testEntityConsistency()
  console.log('')
  console.log('6. Text Statistics')
  testTextStatistics()
  console.log('')
  console.log('7. Permission Checking')
  testPermissionChecking()
  console.log('')
  console.log('8. Adapter Pattern')
  testAdapterPattern()
  console.log('')
  console.log('9. Export Formats')
  testExportFormats()
}

// Run all tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  testFullIntegration().catch(console.error)
}
