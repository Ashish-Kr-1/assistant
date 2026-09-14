import { BrowserRouter, Routes, Route } from "react-router-dom"
import Home from "./pages/Home/Home"
import ChatBot from "./pages/ChatBot/ChatBot"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />}></Route>
        <Route path="/chatbot" element={<ChatBot />}></Route>
      </Routes>
    </BrowserRouter>
  )
}