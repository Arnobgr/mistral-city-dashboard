import { MetricChart } from '../types'
import { RiExternalLinkLine } from '@remixicon/react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export function BarChartWidget(metric: MetricChart) {
  return (
    <div className="bg-white border-4 border-ink-black p-6 shadow-brutal hover:-translate-y-1 hover:shadow-brutal-hover transition-all flex flex-col justify-between group">
      <div className="flex justify-between items-start mb-6 border-b-2 border-ink-black pb-4">
        <h3 className="text-2xl font-display uppercase tracking-widest text-ink-black leading-none">
          {metric.title}
        </h3>
        <a
          href={metric.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-ink-black hover:text-french-blue transition-colors bg-white border-2 border-ink-black p-1 hover:bg-french-white"
          title="Source des données"
        >
          <RiExternalLinkLine className="w-5 h-5" />
        </a>
      </div>

      <div className="h-[300px] mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={metric.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#0a0a0a" vertical={false} />
            <XAxis 
              dataKey="label" 
              stroke="#0a0a0a" 
              tick={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 12 }}
              tickLine={{ stroke: '#0a0a0a' }}
              axisLine={{ strokeWidth: 2 }}
            />
            <YAxis 
              stroke="#0a0a0a" 
              tick={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 12 }}
              tickLine={{ stroke: '#0a0a0a' }}
              axisLine={{ strokeWidth: 2 }}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#ffffff', border: '4px solid #0a0a0a', borderRadius: '0', fontFamily: '"JetBrains Mono", monospace', textTransform: 'uppercase' }}
              labelStyle={{ color: '#0a0a0a', fontWeight: 'bold', marginBottom: '4px' }}
              itemStyle={{ color: '#003189', fontWeight: 'bold' }}
              cursor={{ fill: 'rgba(0,49,137,0.1)' }}
            />
            <Bar 
              dataKey="value"
              fill="#003189"
              stroke="#0a0a0a"
              strokeWidth={2}
              radius={[0, 0, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="text-xs font-mono text-gray-500 uppercase truncate border-t-2 border-dashed border-gray-300 pt-3 mt-auto">
        SOURCE: {metric.source_dataset}
      </div>
    </div>
  )
}