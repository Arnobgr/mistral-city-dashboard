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
    <div className="max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-6">
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="ENTREZ UNE VILLE OU UN DÉPARTEMENT..."
          className="flex-1 px-6 py-5 border-4 border-ink-black bg-white text-ink-black focus:outline-none focus:bg-french-white transition-colors text-xl font-mono uppercase placeholder-gray-400"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !city.trim()}
          className={`px-10 py-5 bg-french-blue text-white border-4 border-ink-black font-display text-3xl tracking-widest uppercase transition-all shadow-brutal hover:shadow-brutal-hover hover:-translate-y-1 active:translate-y-1 active:shadow-none ${loading ? 'opacity-70 cursor-not-allowed' : ''}`}
        >
          {loading ? (
            <span className="flex items-center gap-3">
              <span className="animate-spin rounded-full h-5 w-5 border-b-4 border-white"></span>
              RECHERCHE...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <RiSearchLine className="w-6 h-6" />
              ANALYSER
            </span>
          )}
        </button>
      </form>
      <div className="mt-8 pt-4 border-t-2 border-ink-black/20 flex flex-col md:flex-row justify-between items-center gap-4">
        <p className="text-lg font-body text-gray-600 italic">
          Exemples : Paris, Lyon, Marseille, Dijon
        </p>
        {error && (
          <p className="text-lg font-body text-french-red font-bold" role="alert">
            Erreur: {error}
          </p>
        )}
      </div>
    </div>
  )
}