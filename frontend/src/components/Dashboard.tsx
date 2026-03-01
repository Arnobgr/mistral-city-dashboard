import { Metric, DashboardData } from '../types'
import { KPICard } from './KPICard'
import { LineChartWidget } from './LineChartWidget'
import { BarChartWidget } from './BarChartWidget'
import { RiArrowLeftLine, RiVolumeUpLine } from '@remixicon/react'
import { fetchTTS } from '../api'

export function Dashboard({ data, onBack }: { data: DashboardData; onBack: () => void }) {
  const renderMetric = (metric: Metric) => {
    switch (metric.type) {
      case 'kpi':
        return <KPICard key={metric.id} {...metric} />
      case 'line_chart':
        return <LineChartWidget key={metric.id} {...metric} />
      case 'bar_chart':
        return <BarChartWidget key={metric.id} {...metric} />
      default:
        return null
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-french-blue hover:text-[#002570] mb-4 transition-colors"
        >
          <RiArrowLeftLine className="w-5 h-5" />
          ← Nouvelle recherche
        </button>
        
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-[2.5rem] font-bold text-french-blue">{data.city}</h2>
            <p className="text-lg text-gray-600 mt-2">{data.summary}</p>
          </div>
          <button
            className="flex items-center gap-2 text-gray-500 hover:text-gray-700 transition-colors"
            onClick={async () => {
              try {
                const blob = await fetchTTS(data.summary)
                const url = URL.createObjectURL(blob)
                const audio = new Audio(url)
                audio.play()
                audio.onended = () => URL.revokeObjectURL(url)
              } catch (error) {
                console.error("TTS error:", error)
                // Fallback to browser TTS if ElevenLabs fails
                const utterance = new SpeechSynthesisUtterance(data.summary)
                utterance.lang = 'fr-FR'
                speechSynthesis.speak(utterance)
              }
            }}
          >
            <RiVolumeUpLine className="w-5 h-5" />
            Écouter
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data.metrics.map(renderMetric)}
      </div>
    </div>
  )
}