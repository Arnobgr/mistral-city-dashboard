import { useEffect, useState } from 'react'
import { RiDatabaseLine, RiSearchLine, RiBarChartLine, RiDashboardLine } from '@remixicon/react'

export function LoadingOverlay() {
  const [messageIndex, setMessageIndex] = useState(0)
  const messages = [
    { text: "RECHERCHE DES JEUX DE DONNÉES...", icon: <RiDatabaseLine className="w-12 h-12 text-french-white" /> },
    { text: "INTERROGATION DE DATA.GOUV.FR...", icon: <RiSearchLine className="w-12 h-12 text-french-white" /> },
    { text: "ANALYSE PAR L'IA EN COURS...", icon: <RiBarChartLine className="w-12 h-12 text-french-white" /> },
    { text: "ASSEMBLAGE DU TABLEAU DE BORD...", icon: <RiDashboardLine className="w-12 h-12 text-french-white" /> },
  ]

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length)
    }, 2000)
    return () => clearInterval(interval)
  }, [messages.length])

  return (
    <div className="fixed inset-0 flex items-center justify-center z-50 bg-ink-black/95 backdrop-blur-sm p-4">
      <div className="border-4 border-french-white p-8 md:p-16 max-w-4xl w-full text-center relative bg-ink-black shadow-[16px_16px_0px_0px_rgba(248,248,248,1)]">
        <div className="absolute top-0 left-0 w-full h-3 flex">
          <div className="h-full w-1/3 bg-french-blue animate-pulse"></div>
          <div className="h-full w-1/3 bg-french-white animate-pulse delay-75"></div>
          <div className="h-full w-1/3 bg-french-red animate-pulse delay-150"></div>
        </div>
        
        <h2 className="text-6xl md:text-8xl font-display uppercase tracking-widest text-french-white mb-12 mt-6">
          ANALYSE EN COURS
        </h2>

        <div className="flex flex-col items-center justify-center gap-8">
          <div className="p-6 border-4 border-french-white bg-ink-black animate-bounce shadow-[8px_8px_0px_0px_rgba(248,248,248,1)]">
            {messages[messageIndex].icon}
          </div>
          <div className="h-16 flex items-center justify-center overflow-hidden">
            <span className="text-2xl md:text-4xl font-mono uppercase tracking-wider text-french-white transition-opacity duration-300">
              {messages[messageIndex].text}
            </span>
          </div>
        </div>

        <p className="mt-12 text-xl font-body italic text-gray-400 border-t-2 border-dashed border-gray-700 pt-6">
          Veuillez patienter pendant que notre agent explore les données publiques.
        </p>
      </div>
    </div>
  )
}