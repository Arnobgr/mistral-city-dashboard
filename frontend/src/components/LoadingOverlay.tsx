import { useEffect, useState } from 'react'
import { RiDatabaseLine, RiSearchLine, RiBarChartLine, RiDashboardLine } from '@remixicon/react'

export function LoadingOverlay() {
  const [messageIndex, setMessageIndex] = useState(0)
  const messages = [
    { text: "Recherche des jeux de données...", icon: <RiDatabaseLine className="w-8 h-8 text-white" /> },
    { text: "Interrogation de data.gouv.fr...", icon: <RiSearchLine className="w-8 h-8 text-white" /> },
    { text: "Analyse des données...", icon: <RiBarChartLine className="w-8 h-8 text-white" /> },
    { text: "Assemblage du tableau de bord...", icon: <RiDashboardLine className="w-8 h-8 text-white" /> },
  ]

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length)
    }, 2000)
    return () => clearInterval(interval)
  }, [messages.length])

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50" style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}>
      <div className="p-8 rounded-xl max-w-sm w-full text-center">
        <div className="mb-6">
          <div className="w-16 h-16 border-4 border-white/30 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
        </div>
        <div className="flex items-center justify-center gap-3">
          {messages[messageIndex].icon}
          <span className="text-lg font-medium text-white">
            {messages[messageIndex].text}
          </span>
        </div>
        <p className="mt-4 text-sm text-white/90">
          Cela peut prendre quelques secondes...
        </p>
      </div>
    </div>
  )
}