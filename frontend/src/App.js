import React, { useState } from 'react';
import Questionnaire from './components/Questionnaire';
import RegulatoryDisplay from './components/RegulatoryDisplay';
import Chatbot from './components/Chatbot';
import './styles/modern.css';

function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [guidelines, setGuidelines] = useState([]);
  const [questionnaireData, setQuestionnaireData] = useState(null);
  const [isLoadingGuidelines, setIsLoadingGuidelines] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleQuestionnaireSubmit = async (formData) => {
    setQuestionnaireData(formData);
    setIsLoadingGuidelines(true);
    try {
      const response = await fetch('http://localhost:8000/questionnaire', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch guidelines');
      }

      const data = await response.json();
      setGuidelines(data.guidelines);
      setActiveTab(1);
    } catch (error) {
      console.error('Error fetching guidelines:', error);
    } finally {
      setIsLoadingGuidelines(false);
    }
  };

  const tabs = [
    { id: 0, label: 'Questionnaire 📋', component: <Questionnaire onSubmit={handleQuestionnaireSubmit} /> },
    { id: 1, label: 'Regulatory Guidelines 📚', component: <RegulatoryDisplay guidelines={guidelines} questionnaireData={questionnaireData} /> },
    { id: 2, label: 'AI Assistant 🤖', component: <Chatbot guidelines={guidelines} questionnaireData={questionnaireData} isLoadingGuidelines={isLoadingGuidelines} /> }
  ];

  const handleTabClick = (id) => {
    setActiveTab(id);
    setIsMobileMenuOpen(false);
  };

  return (
    <div className="modern-container">
      <header className="app-header">
        <div className="header-content">
          <h1 className="text-gradient">BioTech Regulatory Navigator ✨</h1>
          <p>Your AI-powered guide through biotech regulations</p>
        </div>
        <button 
          className="mobile-menu-button"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle menu"
        >
          <div className={`hamburger ${isMobileMenuOpen ? 'open' : ''}`}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        </button>
      </header>

      <nav className={`nav-tabs ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
        <div className="tabs-container">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => handleTabClick(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="profile-avatar">
          <span>U</span>
          <div className="profile-status"></div>
        </div>
      </nav>

      <main className="content-card">
        {tabs.find(tab => tab.id === activeTab)?.component}
      </main>
    </div>
  );
}

export default App;
