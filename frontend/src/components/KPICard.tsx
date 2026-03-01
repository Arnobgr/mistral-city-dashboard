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
    <div className="bg-white rounded-2xl shadow-md p-6 hover:shadow-lg transition-shadow min-h-[160px]">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold text-gray-800">{metric.title}</h3>
        <a
          href={metric.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-french-blue hover:text-[#002570] transition-colors"
          title="Source des données"
        >
          <RiExternalLinkLine className="w-4 h-4" />
        </a>
      </div>

      <div className="mb-4">
        <div className="text-3xl font-bold text-gray-900 mb-1">
          {metric.value} <span className="text-sm font-normal text-gray-500">{metric.unit}</span>
        </div>
        {metric.delta !== null && (
          <div className={`text-sm font-medium ${getDeltaColor()}`}>
            {getDeltaSymbol()} {Math.abs(metric.delta)} {metric.delta_label}
          </div>
        )}
      </div>

      <div className="text-xs text-gray-500 truncate">
        Source: {metric.source_dataset}
      </div>
    </div>
  )
}