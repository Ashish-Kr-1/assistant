import { BrowserRouter, Routes, Route } from "react-router-dom"
import Home from "./pages/Home/Home"
import Assistant from "./pages/Assistant/Assistant"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />}></Route>
        <Route path="/assistant" element={<Assistant />}></Route>
        <Route path="/chatbot" element={<Assistant />}></Route>
        <Route path="/knowledge-graph" element={<Assistant initialSection="knowledge-base" />}></Route>
        <Route path="/ip-guidance" element={<Assistant initialSection="ip-guidance" />}></Route>
      </Routes>
    </BrowserRouter>
  )
}