import React from "react";
import "./index.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import KnowledgeGraphPage from "./pages/KnowledgeGraphPage";
import RAGQueryPage from "./pages/RAGQueryPage";

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<KnowledgeGraphPage />} />
        <Route path="/rag" element={<RAGQueryPage />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
