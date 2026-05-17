import { useState, useEffect, useCallback, useRef } from 'react';

const MAX_READINGS = 100;
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export function useSensorStream() {
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [latestReadings, setLatestReadings] = useState({});
  const [readingsHistory, setReadingsHistory] = useState({});
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const fetchDevices = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/devices`);
      if (response.ok) {
        const data = await response.json();
        setDevices(data);
      }
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    }
  }, []);

  const fetchLatestReadings = useCallback(async () => {
    try {
      const url = selectedDevice
        ? `${API_BASE}/api/v1/readings/latest?device_id=${selectedDevice}`
        : `${API_BASE}/api/v1/readings/latest`;
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        const readingMap = {};
        data.readings.forEach(reading => {
          const key = `${reading.device_id}-${reading.sensor}`;
          readingMap[key] = reading;
        });
        setLatestReadings(readingMap);
      }
    } catch (error) {
      console.error('Failed to fetch latest readings:', error);
    }
  }, [selectedDevice]);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`${API_BASE}/api/v1/stream`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setConnected(true);
      console.log('SSE connected');
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.payload) {
          const reading = data.payload;
          const key = `${reading.device_id}-${reading.sensor}`;

          setLatestReadings(prev => ({
            ...prev,
            [key]: reading
          }));

          setReadingsHistory(prev => {
            const history = prev[key] || [];
            const newHistory = [...history, reading].slice(-MAX_READINGS);
            return { ...prev, [key]: newHistory };
          });

          if (!selectedDevice) {
            setSelectedDevice(reading.device_id);
          }
        }
      } catch (error) {
        console.error('SSE parse error:', error);
      }
    };

    eventSource.onerror = () => {
      setConnected(false);
      eventSource.close();
      eventSourceRef.current = null;

      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    };
  }, [selectedDevice]);

  useEffect(() => {
    fetchDevices();
    fetchLatestReadings();
    connect();

    const interval = setInterval(fetchDevices, 10000);
    const latestInterval = setInterval(fetchLatestReadings, 5000);

    return () => {
      clearInterval(interval);
      clearInterval(latestInterval);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect, fetchDevices, fetchLatestReadings]);

  return {
    devices,
    selectedDevice,
    setSelectedDevice,
    latestReadings,
    readingsHistory,
    connected
  };
}