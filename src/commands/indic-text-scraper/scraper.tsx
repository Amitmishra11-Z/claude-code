/**
 * Indic Text Scraper Command - User-facing interface
 */

import React from 'react'
import { Box, Text } from 'ink'
import SelectInput from 'ink-select-input'

interface ScraperState {
  mode: 'menu' | 'url-input' | 'running' | 'results'
  urls: string[]
  currentUrl: string
  currentIndex: number
  results: Array<{
    url: string
    status: 'pending' | 'success' | 'error'
    content: string
    language: string
  }>
  analyzeFakeNews: boolean
  error?: string
}

export const IndicTextScraperCommand: React.FC = () => {
  const [state, setState] = React.useState<ScraperState>({
    mode: 'menu',
    urls: [],
    currentUrl: '',
    currentIndex: 0,
    results: [],
    analyzeFakeNews: true,
  })

  const menuItems = [
    { label: 'Scrape Single URL', value: 'single' },
    { label: 'Batch Scrape Multiple URLs', value: 'batch' },
    { label: 'Analyze Text for Fake News', value: 'analyze' },
    { label: 'Exit', value: 'exit' },
  ]

  const handleMenuSelect = (item: (typeof menuItems)[0]) => {
    switch (item.value) {
      case 'single':
        setState({ ...state, mode: 'url-input', currentUrl: '' })
        break
      case 'batch':
        setState({ ...state, mode: 'url-input', currentUrl: '' })
        break
      case 'analyze':
        setState({ ...state, mode: 'url-input', currentUrl: '' })
        break
      case 'exit':
        process.exit(0)
    }
  }

  if (state.mode === 'menu') {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>Indic Text Scraper and Fake News Detection</Text>
        <Text dimColor>Select an operation:</Text>
        <SelectInput items={menuItems} onSelect={handleMenuSelect} />
      </Box>
    )
  }

  if (state.mode === 'url-input') {
    return (
      <Box flexDirection="column" padding={1}>
        <Text>Enter URL to scrape (or type 'back' to return to menu):</Text>
        <Text dimColor>
          Enter URL: {/* Would use ink-text-input in actual implementation */}
        </Text>
      </Box>
    )
  }

  if (state.mode === 'running') {
    return (
      <Box flexDirection="column" padding={1}>
        <Text>Processing: {state.currentUrl}</Text>
        <Text dimColor>This may take a moment...</Text>
      </Box>
    )
  }

  if (state.mode === 'results') {
    return (
      <Box flexDirection="column" padding={1}>
        <Text bold>Results</Text>
        {state.results.map((result, idx) => (
          <Box key={idx} flexDirection="column" marginBottom={1}>
            <Text>{result.url}</Text>
            <Text dimColor>Status: {result.status}</Text>
            <Text dimColor>
              Language: {result.language}, Length: {result.content.length} chars
            </Text>
          </Box>
        ))}
      </Box>
    )
  }

  return (
    <Box padding={1}>
      <Text>Loading...</Text>
    </Box>
  )
}

export default IndicTextScraperCommand
