import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [sourceText, setSourceText] = useState('Gyebale ko, oli otya?')
  const [translation, setTranslation] = useState('')
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('')
  const [dictionaryEntries, setDictionaryEntries] = useState([])
  const [sourceLanguage, setSourceLanguage] = useState('lg')
  const [targetLanguage, setTargetLanguage] = useState('en')
  const [isSpeaking, setIsSpeaking] = useState(false)

  const languages = {
    lg: { name: 'Luganda', badge: 'LG', placeholder: 'Wandika mu Luganda...' },
    en: { name: 'English', badge: 'EN', placeholder: 'Write in English...' },
  }

  useEffect(() => {
    fetch(`${API_URL}/api/dictionary`)
      .then((response) => response.json())
      .then((data) => setDictionaryEntries(data.entries.slice(0, 6)))
      .catch(() => setDictionaryEntries([]))
  }, [])

  async function translateText() {
    if (!sourceText.trim()) return

    setStatus('loading')
    setMessage('')
    try {
      const response = await fetch(`${API_URL}/api/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: sourceText, source: sourceLanguage, target: targetLanguage }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Translation failed')
      setTranslation(data.translation)
      setMessage(data.confidence === 'review' ? 'This phrase needs a human review.' : `Ready via ${data.provider}`)
      setStatus('success')
    } catch (error) {
      setStatus('error')
      setMessage(error.message || 'Could not reach the translation service.')
    }
  }

  function clearText() {
    setSourceText('')
    setTranslation('')
    setMessage('')
    setStatus('idle')
  }

  function fillSample(text) {
    setSourceText(text)
    setTranslation('')
    setMessage('')
    setStatus('idle')
  }

  function swapLanguages() {
    const nextSourceText = translation || sourceText
    setSourceText(nextSourceText)
    setTranslation(translation ? sourceText : '')
    setSourceLanguage(targetLanguage)
    setTargetLanguage(sourceLanguage)
    setMessage('')
    setStatus('idle')
  }

  function speakTranslation() {
    if (!translation || !('speechSynthesis' in window)) {
      setMessage('Voice playback is not supported in this browser.')
      return
    }

    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(translation)
    utterance.lang = targetLanguage === 'en' ? 'en-US' : 'lg'
    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)
    window.speechSynthesis.speak(utterance)
  }

  const source = languages[sourceLanguage]
  const target = languages[targetLanguage]

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-mark" aria-hidden="true">L</div>
        <div>
          <p className="eyebrow">LANGUAGE BRIDGE</p>
          <p className="brand-name">LUGAFLOW</p>
        </div>
        <div className="status-pill"><span className="status-dot" /> Dictionary + Google ready</div>
      </header>

      <section className="intro">
        <p className="section-kicker">{source.name} <span>to</span> {target.name}</p>
        <h1>Find the right words.<br /><em>Share the meaning.</em></h1>
        <p className="intro-copy">A colorful bridge for turning everyday language into clear meaning, one phrase at a time.</p>
      </section>

      <section className="translator" aria-label="Translation workspace">
        <div className="language-row">
          <div className="language-select"><span className="language-badge">{source.badge}</span><span>{source.name}</span><span className="chevron">⌄</span></div>
          <button type="button" className="swap-button" title="Swap languages" aria-label={`Switch to ${target.name} to ${source.name}`} onClick={swapLanguages}>⇄</button>
          <div className="language-select target"><span className="language-badge english">{target.badge}</span><span>{target.name}</span><span className="chevron">⌄</span></div>
        </div>
        <div className="translation-grid">
          <div className="text-panel source-panel">
            <label htmlFor="source-text">Your {source.name}</label>
            <textarea id="source-text" value={sourceText} onChange={(event) => setSourceText(event.target.value)} placeholder={source.placeholder} maxLength="1000" />
            <div className="panel-footer"><span>{sourceText.length} / 1,000</span><button type="button" className="text-button" onClick={clearText}>Clear</button></div>
          </div>
          <div className="text-panel result-panel">
            <div className="result-heading"><label htmlFor="translation-text">{target.name} translation</label><span className="result-state">{status === 'success' ? '● Ready' : '○ Waiting'}</span></div>
            <div id="translation-text" className={`translation-result ${!translation ? 'empty' : ''}`} aria-live="polite">{translation || 'Your translation will appear here.'}</div>
            <div className="panel-footer"><span className={status === 'error' ? 'error-text' : ''}>{message || 'Dictionary first · Google for everything else'}</span><div className="result-actions"><button type="button" className="voice-button" disabled={!translation} onClick={speakTranslation} title={`Speak in ${target.name}`}>🔊 {isSpeaking ? 'Speaking...' : 'Speak aloud'}</button><button type="button" className="text-button" disabled={!translation} onClick={() => navigator.clipboard.writeText(translation)}>Copy</button></div></div>
          </div>
        </div>
        <div className="action-row"><span className="privacy-note"><span>✦</span> Your text stays in this workspace</span><button type="button" className="translate-button" onClick={translateText} disabled={status === 'loading' || !sourceText.trim()}>{status === 'loading' ? 'Translating...' : <>Translate <span>→</span></>}</button></div>
      </section>

      <section className="samples"><div className="samples-heading"><div><p className="section-kicker">Start with a phrase</p><h2>Try something familiar</h2></div><span className="sample-count">3 examples</span></div><div className="sample-list"><button type="button" onClick={() => fillSample('Gyebale ko, oli otya?')}><span>Gyebale ko, oli otya?</span><span>How are you?</span></button><button type="button" onClick={() => fillSample('Webale nnyo')}><span>Webale nnyo</span><span>Thank you very much</span></button><button type="button" onClick={() => fillSample('Nja kudda enkya')}><span>Nja kudda enkya</span><span>I will come back tomorrow</span></button></div></section>
      <section className="dictionary-section"><div className="samples-heading"><div><p className="section-kicker">Pocket dictionary</p><h2>Everyday Luganda</h2></div><span className="sample-count">{dictionaryEntries.length || '...'} words</span></div><div className="dictionary-grid">{dictionaryEntries.map((entry) => <button type="button" key={entry.luganda} onClick={() => fillSample(entry.luganda)}><span>{entry.luganda}</span><span>{entry.english}</span></button>)}</div></section>
      <footer><span>LUGAFLOW</span><span>Built for everyday connection</span><span>v0.1 · Local mode</span></footer>
    </main>
  )
}

export default App
