import React from "react";
import AudioChat from "./components/AudioChat";

export default function App() {
  return (
    <main style={{ fontFamily: "sans-serif", padding: 20 }}>
      <h1>Voice Agent Demo</h1>
      <AudioChat />
    </main>
  );
}
