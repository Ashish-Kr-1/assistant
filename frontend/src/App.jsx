import {BrowserRouter,Routes,Route} from "react-router-dom"
import ChatBot from "./pages/ChatBot/ChatBot"

export default function App(){
  return(
    <BrowserRouter>
      <Routes>
        <Route path="/chatbot" element={<ChatBot />}></Route>
      </Routes>
    </BrowserRouter>
  )
}