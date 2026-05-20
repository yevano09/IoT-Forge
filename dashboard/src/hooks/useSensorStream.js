import { useState, useEffect, useRef, useCallback } from 'react'

const BUFFER_SIZE = 100
const RECONNECT_DELAY_MS = 3000

export function useSensorStream(apiBase = '') {
  const [readings, setReadings]   = useState(new Map())
  const [connected, setConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState(null)
  const esRef      = useRef(null)
  const retryRef   = useRef(null)

  const connect = useCallback(() => {
    if (esRef.current) {
      esRef.current.close()
      esRef.current = null
    }

    const url = `${apiBase}/api/v1/stream`
    const es  = new EventSource(url)
    esRef.current = es

    es.onopen = () => {
      setConnected(true)
      if (retryRef.current) {
        clearTimeout(retryRef.current)
        retryRef.current = null
      }
    }

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        const key = `${payload.device_id}::${payload.sensor}`

        setReadings(prev => {
          const next    = new Map(prev)
          const current = next.get(key) || []
          const updated = [...current, {
            ts:        payload.ts,
            value:     payload.value,
            unit:      payload.unit,
            quality:   payload.quality,
            device_id: payload.device_id,
            sensor:    payload.sensor,
          }].slice(-BUFFER_SIZE)
          next.set(key, updated)
          return next
        })

        setLastEvent(payload)
      } catch (e) {
      }
    }

    es.onerror = () => {
      setConnected(false)
      es.close()
      esRef.current = null
      retryRef.current = setTimeout(connect, RECONNECT_DELAY_MS)
    }
  }, [apiBase])

  useEffect(() => {
    connect()
    return () => {
      if (esRef.current)  esRef.current.close()
      if (retryRef.current) clearTimeout(retryRef.current)
    }
  }, [connect])

  return { readings, connected, lastEvent }
}
