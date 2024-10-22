import React, { useState, useEffect, useRef, MutableRefObject } from 'react';

import useWebSocket, { ReadyState } from 'react-use-websocket';

import Conversation, {ConversationModel} from './Conversation';
import Conversations, {ConversationsModel} from './Conversations';


// WebSocket URL (replace with your WebSocket server URL)
const WEBSOCKET_URL = 'ws://127.0.0.1:8000/ws';

function playPcm16Base64Audio(globalCurrentTime: MutableRefObject<number>, audioContext: MutableRefObject<AudioContext>, base64String: string, sampleRate = 16000, numChannels = 1) {
  // Use globalCurrentTime to ensure that multiple function calls are scheduled properly
  let startTime = Math.max(globalCurrentTime.current, audioContext.current.currentTime); // Ensure it's at least the current audio context time

  // Decode the base64 string to an ArrayBuffer
  const audioData = base64ToArrayBuffer(base64String);

  // Convert PCM 16-bit little-endian to AudioBuffer
  const audioBuffer = convertPcm16ToAudioBuffer(audioData, audioContext.current, sampleRate, numChannels);

  // Schedule the audio to play after the previous one finishes
  playAudioBuffer(audioBuffer, audioContext.current, startTime);

  // Increment startTime for the next audio clip
  startTime += audioBuffer.duration; // This makes sure the next clip is scheduled after the current one ends

  // Update globalCurrentTime after the current array is scheduled
  globalCurrentTime.current = startTime;
}

// Helper function to decode base64 to ArrayBuffer
function base64ToArrayBuffer(base64: string) {
  const binaryString = atob(base64);
  const length = binaryString.length;
  const buffer = new ArrayBuffer(length);
  const view = new Uint8Array(buffer);

  for (let i = 0; i < length; i++) {
    view[i] = binaryString.charCodeAt(i);
  }

  return buffer;
}

// Helper function to convert PCM 16-bit little-endian to AudioBuffer
function convertPcm16ToAudioBuffer(arrayBuffer: ArrayBuffer, audioContext: BaseAudioContext, sampleRate: number, numChannels: number) {
  const dataView = new DataView(arrayBuffer);
  const numSamples = arrayBuffer.byteLength / 2; // 16-bit audio (2 bytes per sample)

  // Create an empty AudioBuffer
  const audioBuffer = audioContext.createBuffer(numChannels, numSamples, sampleRate);

  // Fill the AudioBuffer with the decoded PCM data
  for (let channel = 0; channel < numChannels; channel++) {
    const buffer = audioBuffer.getChannelData(channel);
    for (let i = 0; i < numSamples; i++) {
      buffer[i] = dataView.getInt16(i * 2, true) / 32768; // 16-bit PCM is in range [-32768, 32767]
    }
  }

  return audioBuffer;
}

// Helper function to play AudioBuffer at a specified time
function playAudioBuffer(audioBuffer: AudioBuffer, audioContext: BaseAudioContext, startTime: number) {
  const source = audioContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioContext.destination);
  source.start(startTime); // Schedule to start at the given time
}
function initConversation(n: number) {
  return {input_transcript: [], output_transcript: [], number: n};
}

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<Blob | null>(null);
  const [conversationItems, setConversationItems] = useState<ConversationModel[]>([]);
  const [conversation, setConversation] = useState<ConversationModel>(initConversation(0));
  const [conversationIsFinished, setConversationIsFinished] = useState(false);


  const audioContext = useRef(new (window.AudioContext)());
  const globalCurrentTime = useRef(audioContext.current.currentTime);



  const { sendMessage, lastMessage, readyState } = useWebSocket(WEBSOCKET_URL, {
    onMessage: (event) => {
      const parsedEvent = JSON.parse(event.data);
      if(parsedEvent.type === "input_transcript") {
	setConversation(c => ({...c, input_transcript: [...c.input_transcript, parsedEvent.data]}));
	setConversationIsFinished(true);
      }
      if(parsedEvent.type === "transcript") {
	setConversation(c => ({...c, output_transcript: [...c.output_transcript, parsedEvent.data]}));
      }
      else if(parsedEvent.type === "message" && parsedEvent.data === "response.done" && conversationIsFinished) {
	setConversationItems(i => [conversation, ...i]);
	setConversation(initConversation(conversationItems.length+1));
	setConversationIsFinished(false);
      }
      else if(parsedEvent.type === "audio") {
	playPcm16Base64Audio(globalCurrentTime, audioContext, parsedEvent.data, 24000, 1);
      }
    }
  }
  );

  // Request microphone access and set up MediaRecorder
  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
	if (readyState != ReadyState.OPEN) return;
	const recorder = new MediaRecorder(stream, {
	  mimeType: 'audio/webm;codecs=pcm', // Specify PCM format
	});
	mediaRef.current =recorder;

	recorder.ondataavailable = (event: BlobEvent) => {
	  audioRef.current = event.data;
	};

	recorder.onstop = () => {
	  if (audioRef.current) {
	    const audioBlob = new Blob([audioRef.current], { type: 'audio/pcm' });
	    console.log(readyState);
	    console.log(ReadyState.OPEN);
	    if (audioBlob) {
	      sendMessage(audioBlob);
	    }
	  };
	  if (mediaRef.current) {
	    mediaRef.current.stop()
	  }
	}
      })
      .catch(error => {
	console.error('Microphone access denied:', error);
      });
  }, [sendMessage, readyState]);


  // Attach and detach event listeners for space bar
  useEffect(() => {
    if (readyState != ReadyState.OPEN) return;
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [isRecording, readyState]);


  // Handle keydown event for space bar
  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.code === 'Space' && !isRecording && mediaRef.current) {
      mediaRef.current.start();
      setIsRecording(true);
      console.log('Recording started...');
    }
  };

  // Handle keyup event to stop recording
  const handleKeyUp = (event: KeyboardEvent) => {
    if (event.code === 'Space' && isRecording && mediaRef.current) {
      mediaRef.current.stop();
      setIsRecording(false);
      console.log('Recording stopped.');
    }
  };

  return (
    <div>
      <p> Websocket Satus : {readyState == ReadyState.OPEN ? "Ready" : "Waiting"}</p>
      <p>Press and hold the space bar to record audio. Release to stop.</p>
      <p>Status: {isRecording ? 'Recording...' : 'Idle'}</p>
      <Conversation input_transcript={conversation.input_transcript} output_transcript={conversation.output_transcript} number={conversation.number}/>
      <Conversations conversations={conversationItems}/>
    </div>
  );
};

export default App;
