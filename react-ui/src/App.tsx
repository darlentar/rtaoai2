import React, { useState, useEffect, useRef } from 'react';

import useWebSocket, { ReadyState } from 'react-use-websocket';

import Conversation, {ConversationModel} from './Conversation';
import Conversations, {ConversationsModel} from './Conversations';


// WebSocket URL (replace with your WebSocket server URL)
const WEBSOCKET_URL = 'ws://127.0.0.1:8000/ws';

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
