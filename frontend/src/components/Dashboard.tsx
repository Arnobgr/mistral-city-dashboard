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
    <div className="w-full">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 border-b-4 border-ink-black pb-6 gap-6">
        <div>
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-ink-black hover:text-french-blue mb-6 transition-colors font-mono font-bold uppercase tracking-wider text-sm border-2 border-ink-black px-4 py-2 hover:bg-ink-black hover:text-white"
          >
            <RiArrowLeftLine className="w-4 h-4" />
            RETOUR
          </button>
          
          <h2 className="text-7xl md:text-8xl font-display text-ink-black uppercase leading-none tracking-tight">
            {data.city}
          </h2>
          <p className="text-2xl font-body text-gray-800 mt-4 max-w-3xl leading-relaxed border-l-4 border-french-red pl-6 py-2 bg-white/50">
            {data.summary}
          </p>
        </div>

        <div className="relative group shrink-0">
          <button
            className="flex items-center gap-3 bg-french-red text-white px-6 py-4 border-4 border-ink-black font-display text-2xl uppercase tracking-widest shadow-brutal-black hover:translate-y-1 hover:shadow-none transition-all active:bg-red-800 w-full"
            onClick={async () => {
              try {
                const blob = await fetchTTS(data.summary)
                const url = URL.createObjectURL(blob)
                const audio = new Audio(url)
                audio.play()
                audio.onended = () => URL.revokeObjectURL(url)
              } catch (error) {
                console.error("TTS error:", error)
                const utterance = new SpeechSynthesisUtterance(data.summary)
                utterance.lang = 'fr-FR'
                speechSynthesis.speak(utterance)
              }
            }}
          >
            <RiVolumeUpLine className="w-6 h-6" />
            ÉCOUTER LE RÉSUMÉ
          </button>
          <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-white text-ink-black border-2 border-ink-black px-4 py-2 text-xs font-mono font-bold uppercase whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-brutal">
            Propulsé par ElevenLabs
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-4 flex flex-col gap-8">
          {data.metrics.filter(m => m.type === 'kpi').map(renderMetric)}
        </div>
        <div className="lg:col-span-8 flex flex-col gap-8">
          {data.metrics.filter(m => m.type !== 'kpi').map(renderMetric)}
        </div>
      </div>
    </div>
  )
}