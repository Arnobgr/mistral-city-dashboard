import { useState } from 'react'
import { RiSearchLine } from '@remixicon/react'

export function SearchBar({ onSearch, loading, error }: { onSearch: (city: string) => void; loading: boolean; error?: string | null }) {
  const [city, setCity] = useState<string>('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (city.trim() && !loading) {
      onSearch(city.trim())
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="Entrez une ville, commune ou département..."
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-french-blue focus:border-transparent text-lg"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !city.trim()}
          className={`px-6 py-3 bg-french-blue text-white rounded-lg shadow-sm hover:bg-[#002570] focus:outline-none focus:ring-2 focus:ring-french-blue focus:ring-offset-2 transition-colors ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              Chargement...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <RiSearchLine className="w-5 h-5" />
              Analyser
            </span>
          )}
        </button>
      </form>
      <p className="mt-4 text-sm text-gray-600 text-center">
        Exemple : Paris, Lyon, Marseille, Seine-Saint-Denis
      </p>
      {error && (
        <p className="mt-2 text-sm text-french-red" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}