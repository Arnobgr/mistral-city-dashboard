import { MetricKPI } from '../types'
import { RiExternalLinkLine } from '@remixicon/react'

export function KPICard(metric: MetricKPI) {
  const getDeltaColor = () => {
    if (metric.delta === null) return 'text-gray-500'
    return metric.delta >= 0 ? 'text-green-600' : 'text-french-red'
  }

  const getDeltaSymbol = () => {
    if (metric.delta === null) return null
    return metric.delta >= 0 ? '▲' : '▼'
  }

  return (
    <div className="bg-white border-4 border-ink-black p-6 shadow-brutal hover:-translate-y-1 hover:shadow-brutal-hover transition-all flex flex-col justify-between min-h-[160px] relative overflow-hidden group">
      <div className="absolute top-0 right-0 w-12 h-12 bg-french-white border-l-4 border-b-4 border-ink-black -mt-2 -mr-2 group-hover:bg-french-red transition-colors z-0"></div>

      <div className="relative z-10 flex justify-between items-start mb-6">
        <h3 className="text-xl font-display uppercase tracking-widest text-ink-black max-w-[85%] leading-tight">
          {metric.title}
        </h3>
        <a
          href={metric.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-ink-black hover:text-french-blue transition-colors bg-white border-2 border-ink-black p-1 hover:bg-french-white"
          title="Source des données"
        >
          <RiExternalLinkLine className="w-4 h-4" />
        </a>
      </div>

      <div className="relative z-10 mb-4">
        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-5xl font-mono font-bold text-ink-black leading-none">
            {metric.value}
          </span>
          <span className="text-lg font-mono font-bold text-french-blue uppercase">
            {metric.unit}
          </span>
        </div>
        
        {metric.delta !== null && (
          <div className={`inline-flex items-center gap-1 px-2 py-1 border-2 border-ink-black text-sm font-mono font-bold uppercase ${getDeltaColor()}`}>
            <span>{getDeltaSymbol()}</span>
            <span>{Math.abs(metric.delta)}</span>
            <span className="text-ink-black ml-1">{metric.delta_label}</span>
          </div>
        )}
      </div>

      <div className="relative z-10 text-xs font-mono text-gray-500 uppercase truncate border-t-2 border-dashed border-gray-300 pt-3 mt-auto">
        SOURCE: {metric.source_dataset}
      </div>
    </div>
  )
}