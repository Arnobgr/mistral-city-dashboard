import { useState } from 'react'
import { SearchBar } from './components/SearchBar'
import { Dashboard } from './components/Dashboard'
import { LoadingOverlay } from './components/LoadingOverlay'
import { DashboardData, DashboardResponse } from './types'
import { fetchDashboard } from './api'

function App() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (cityName: string) => {
    setLoading(true)
    setError(null)
    
    try {
      const response: DashboardResponse = await fetchDashboard(cityName)
      setDashboardData(response.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data')
      setDashboardData(null)
    } finally {
      setLoading(false)
    }
  }

  const handleBack = () => {
    setDashboardData(null)
    setError(null)
  }

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Magazine-style Top Border */}
      <div className="w-full h-2 bg-french-blue"></div>
      <div className="w-full h-1 bg-french-red mt-1"></div>

      <header className="pt-6 pb-6 border-b-4 border-ink-black mx-4 md:mx-12 lg:mx-24 mb-8">
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-display text-center text-ink-black uppercase tracking-wide leading-none">
          Ma Ville <span className="text-french-blue">en Chiffres</span>
        </h1>
        <p className="text-center mt-4 text-lg md:text-xl font-body italic text-gray-700 max-w-2xl mx-auto">
          Données civiques officielles, analysées et structurées en temps réel par intelligence artificielle.
        </p>
      </header>

      <main className="flex-grow container mx-auto px-4 md:px-12 lg:px-24 pb-20">
        {dashboardData ? (
          <Dashboard data={dashboardData} onBack={handleBack} />
        ) : (
          <div className="mt-8 md:mt-24">
            <SearchBar onSearch={handleSearch} loading={loading} error={error} />
          </div>
        )}
      </main>
      
      {loading && <LoadingOverlay />}
    </div>
  )
}

export default App