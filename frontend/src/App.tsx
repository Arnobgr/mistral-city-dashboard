import { useState } from 'react'
import { SearchBar } from './components/SearchBar'
import { Dashboard } from './components/Dashboard'
import { LoadingOverlay } from './components/LoadingOverlay'
import { DashboardData, DashboardResponse } from './types'
import { fetchDashboard } from './api'

function App() {
  const [city, setCity] = useState<string>('')
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (cityName: string) => {
    setCity(cityName)
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
    <div className="min-h-screen bg-french-white">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8 text-french-blue">
          Ma Ville en Chiffres
        </h1>
        
        {dashboardData ? (
          <Dashboard data={dashboardData} onBack={handleBack} />
        ) : (
          <SearchBar onSearch={handleSearch} loading={loading} error={error} />
        )}
        
        {loading && <LoadingOverlay />}
      </div>
    </div>
  )
}

export default App