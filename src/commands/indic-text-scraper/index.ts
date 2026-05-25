/**
 * Indic Text Scraper Command Index
 */

import type { Command } from '../../commands.js'
import IndicTextScraperCommand from './scraper.js'

const IndicTextScraperCommandDef: Command = {
  name: 'indic-text-scraper',
  aliases: ['scrape-indic', 'indic-scraper'],
  description: 'Scrape and analyze text in Indic languages for fake news detection',
  category: 'Data Analysis',
  skipGlobalOptions: false,
  action: async (app) => {
    return app.showComponent(<IndicTextScraperCommand />)
  },
}

export default IndicTextScraperCommandDef
