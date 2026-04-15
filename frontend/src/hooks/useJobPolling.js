import { useState, useEffect, useRef } from 'react'
import { getJobStatus } from '../services/api.js'

export function useJobPolling(jobId, onComplete) {
  const [status, setStatus] = useState(null)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (!jobId) return

    const poll = async () => {
      try {
        const res = await getJobStatus(jobId)
        const data = res.data
        setStatus(data)

        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(intervalRef.current)
          if (onComplete) onComplete(data)
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }

    poll()
    intervalRef.current = setInterval(poll, 3000)

    return () => clearInterval(intervalRef.current)
  }, [jobId])

  return status
}
