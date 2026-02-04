import React from "react";
import { ManuscriptEditor } from "./components/ManuscriptEditor";
import { EntitySidebar } from "./components/EntitySidebar";
import "./index.css";

function App() {
  const manuscriptId = "test-manuscript";

  return (
    <div className="editor-container">
      <ManuscriptEditor manuscriptId={manuscriptId} />
      <EntitySidebar />
    </div>
  );
}

export default App;
