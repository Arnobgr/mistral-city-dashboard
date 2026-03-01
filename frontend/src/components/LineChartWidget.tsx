import { MetricChart } from '../types'
import { RiExternalLinkLine } from '@remixicon/react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export function LineChartWidget(metric: MetricChart) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-6 hover:shadow-lg transition-shadow">
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

      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={metric.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" stroke="#4b5563" />
            <YAxis stroke="#4b5563" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb' }}
              labelStyle={{ color: '#111827' }}
            />
            <Line 
              type="monotone"
              dataKey="value"
              stroke="#003189"
              strokeWidth={3}
              dot={{ r: 4, fill: '#003189' }}
              activeDot={{ r: 6, fill: '#0d9488' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="text-xs text-gray-500 truncate mt-2">
        Source: {metric.source_dataset}
      </div>
    </div>
  )
}