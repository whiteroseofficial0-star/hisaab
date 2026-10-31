import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { About, Contact, GuidePage, GuidesIndex, Home, Privacy, Terms, ToolPage, ToolsIndex } from './pages/Pages'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="tools" element={<ToolsIndex />} />
        <Route path="tools/:slug" element={<ToolPage />} />
        <Route path="guides" element={<GuidesIndex />} />
        <Route path="guides/:slug" element={<GuidePage />} />
        <Route path="about" element={<About />} />
        <Route path="privacy" element={<Privacy />} />
        <Route path="terms" element={<Terms />} />
        <Route path="contact" element={<Contact />} />
        <Route path="*" element={<ToolPage />} />
      </Route>
    </Routes>
  )
}
