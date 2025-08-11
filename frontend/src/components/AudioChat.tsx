import React, { useEffect, useRef, useState } from "react";

const WS_URL = "ws://localhost:8000/ws/audio";

export default function AudioChat() {
  const wsRef = useRef<WebSocket | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const mediaStream = useRef<MediaStream | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const processor = useRef<ScriptProcessorNode | null>(null);

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  const startRecording = async () => {
    if (isRecording) return;
    wsRef.current = new WebSocket(WS_URL);
    wsRef.current.binaryType = "arraybuffer";

    wsRef.current.onmessage = (event) => {
      // Play received audio bytes
      const audioBlob = new Blob([event.data], { type: "audio/wav" });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();
    };

    mediaStream.current = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext.current = new AudioContext({ sampleRate: 16000 });
    const source = audioContext.current.createMediaStreamSource(mediaStream.current);
    processor.current = audioContext.current.createScriptProcessor(4096, 1, 1);

    source.connect(processor.current);
    processor.current.connect(audioContext.current.destination);

    processor.current.onaudioprocess = (e) => {
      const channelData = e.inputBuffer.getChannelData(0); // Float32 [-1,1]
      // Convert to 16-bit PCM Little Endian
      const pcm16 = new Int16Array(channelData.length);
      for (let i = 0; i < channelData.length; i++) {
        pcm16[i] = Math.max(-1, Math.min(1, channelData[i])) * 32767;
      }
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(pcm16.buffer);
      }
    };

    setIsRecording(true);
  };

  const stopRecording = () => {
    setIsRecording(false);
    processor.current?.disconnect();
    mediaStream.current?.getTracks().forEach((t) => t.stop());
    wsRef.current?.close();
  };

  return (
    <div>
      <button onClick={isRecording ? stopRecording : startRecording}>
        {isRecording ? "Stop" : "Start"}
      </button>
    </div>
  );
}
