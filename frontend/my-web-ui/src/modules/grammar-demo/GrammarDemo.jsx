import { useState } from 'react'
import GrammarCard from './components/GrammarCard'
import GrammarCardDetail from './components/GrammarCardDetail'
import Modal from '../shared/components/Modal'
import StartReviewButton from '../shared/components/StartReviewButton'
import FilterBar from '../shared/components/FilterBar'

const GrammarDemo = () => {
  const sampleGrammarRules = ['present-perfect', 'past-continuous', 'future-simple', 'conditional']
  const [selectedGrammar, setSelectedGrammar] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleStartReview = () => {
    console.log('Starting grammar review for rules:', sampleGrammarRules)
    // 这里可以添加开始复习的逻辑
    alert('Starting grammar review mode!')
  }

  const handleFilterChange = (filterId, value) => {
    console.log('Filter changed:', filterId, value)
    // 这里可以添加筛选逻辑
  }

  return (
    <div className="h-full bg-gradient-to-br from-green-50 to-emerald-100">
      {/* Filter Bar */}
      <FilterBar onFilterChange={handleFilterChange} />
      
      {/* Main Content */}
      <div className="p-8">
        <div className="max-w-6xl mx-auto flex items-center justify-center">
          {/* Grammar Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {sampleGrammarRules.map((grammar, index) => (
              <div key={grammar} className="flex justify-center">
                <GrammarCard 
                  grammar={grammar} 
                  onClick={() => {
                    setSelectedGrammar(grammar)
                    setIsModalOpen(true)
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Grammar Detail Modal */}
      <Modal 
        isOpen={isModalOpen} 
        onClose={() => {
          setIsModalOpen(false)
          setSelectedGrammar(null)
        }}
      >
        {selectedGrammar && (
          <GrammarCardDetail 
            grammar={selectedGrammar} 
            onClose={() => {
              setIsModalOpen(false)
              setSelectedGrammar(null)
            }}
          />
        )}
      </Modal>

      {/* Start Review Button */}
      <StartReviewButton onClick={handleStartReview} />
    </div>
  )
}

export default GrammarDemo
