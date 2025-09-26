import type { NextApiRequest, NextApiResponse } from 'next'
import https from 'https'

// Event data interface
interface EventData {
  event_id: string
  slack_channel_id: string
  subject: string
  event_source: string
  current_status: string
  create_ts: string
  priority: string
  monitor_name?: string
  original_title?: string
}

// Event source interface
interface EventSource {
  name: string
  enabled: boolean
  fetchEvents(): Promise<EventData[]>
}

// HTTPS Agent for better performance and Zscaler compatibility
const httpsAgent = new https.Agent({
  keepAlive: true,
  maxSockets: 10,
  timeout: 60000,
  family: 4, // Force IPv4
  scheduling: 'lifo' // Last In, First Out for better performance
})

// Zscaler-optimized HTTPS agent for JIRA (if needed in future)
const zscalerAgent = new https.Agent({
  keepAlive: true,
  maxSockets: 3, // Fewer concurrent connections
  timeout: 45000, // Longer timeout
  family: 4, // IPv4 only
  scheduling: 'lifo' // LIFO scheduling
})

class SREAPISource implements EventSource {
  name = 'sre_api'
  enabled = true

  constructor() {
    this.enabled = true
  }

  async fetchEvents(): Promise<EventData[]> {
    try {
      const response = await fetch('http://localhost:8000/event_interactions/events', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'NeMo-Agent-Toolkit/1.0'
        }
      })

      if (!response.ok) {
        console.warn(`SRE API failed: ${response.status}`)
        return []
      }

      const data = await response.json()
      const events = data.result || []
      
      return events.map((event: any, index: number) => ({
        event_id: event.event_id || `sre_${index}`,
        slack_channel_id: event.slack_channel_id || '',
        subject: event.subject || event.summary || 'SRE Event',
        event_source: event.event_source || 'sre_api',
        current_status: event.current_status || event.status || 'Open',
        create_ts: event.create_ts || event.timestamp || new Date().toISOString(),
        priority: event.priority || 'P3',
        monitor_name: event.event_source || 'SRE API',
        original_title: event.subject || event.summary || 'SRE Event'
      }))
    } catch (error) {
      console.error('SRE API error:', error)
      return []
    }
  }
}

// Main API handler
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    // Extract query parameters for filtering
    const { priority, source, status, limit } = req.query
    
    // Initialize event sources - Only SRE API (provides all data including JIRA and Datadog)
    const sources: EventSource[] = [
      new SREAPISource()
    ]

    // Fetch events from all configured sources in parallel
    const allEvents: EventData[] = []
    const sourceResults: Record<string, { count: number, success: boolean, error?: string }> = {}

    for (const eventSource of sources) {
      if (!eventSource.enabled) {
        console.log(`${eventSource.name}: disabled, skipping...`)
        sourceResults[eventSource.name] = { count: 0, success: false, error: 'disabled' }
        continue
      }

      console.log(`Fetching events from ${eventSource.name}...`)
      try {
        const events = await eventSource.fetchEvents()
        allEvents.push(...events)
        sourceResults[eventSource.name] = { count: events.length, success: true }
        console.log(`✅ ${eventSource.name}: ${events.length} events`)
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error'
        console.error(`❌ ${eventSource.name}: ${errorMsg}`)
        sourceResults[eventSource.name] = { count: 0, success: false, error: errorMsg }
      }
    }

    // Apply filters
    let filteredEvents = allEvents

    // Filter by priority (supports comma-separated values like "P1,P2")
    if (priority && typeof priority === 'string') {
      const priorities = priority.split(',').map(p => p.trim().toUpperCase())
      filteredEvents = filteredEvents.filter(event => 
        priorities.includes(event.priority?.toUpperCase() || 'P3')
      )
    }

    // Filter by source (supports comma-separated values like "datadog,jira")
    if (source && typeof source === 'string') {
      const sources = source.split(',').map(s => s.trim().toLowerCase())
      filteredEvents = filteredEvents.filter(event => 
        sources.includes(event.event_source?.toLowerCase() || '')
      )
    }

    // Filter by status (supports comma-separated values like "open,investigating")
    if (status && typeof status === 'string') {
      const statuses = status.split(',').map(s => s.trim().toLowerCase())
      filteredEvents = filteredEvents.filter(event => 
        statuses.includes(event.current_status?.toLowerCase() || '')
      )
    }

    // Sort events by timestamp (newest first)
    filteredEvents.sort((a, b) => {
      const timeA = new Date(a.create_ts).getTime()
      const timeB = new Date(b.create_ts).getTime()
      return timeB - timeA
    })

    // Apply limit if specified
    if (limit && typeof limit === 'string') {
      const limitNum = parseInt(limit, 10)
      if (!isNaN(limitNum) && limitNum > 0) {
        filteredEvents = filteredEvents.slice(0, limitNum)
      }
    }

    // Return response
    res.status(200).json({
      result: filteredEvents,
      metadata: {
        total_events: allEvents.length,
        filtered_events: filteredEvents.length,
        filters_applied: {
          priority: priority || null,
          source: source || null,
          status: status || null,
          limit: limit || null
        },
        sources: sourceResults,
        fetched_at: new Date().toISOString()
      }
    })

  } catch (error) {
    console.error('API error:', error)
    res.status(500).json({ 
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}