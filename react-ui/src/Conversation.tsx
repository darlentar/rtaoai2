import React, { useState, useEffect, useRef } from 'react';

export interface ConversationModel {
   input_transcript: string[];
   output_transcript: string[];
   number: number;
};

const Conversation = ({input_transcript, output_transcript, number}: ConversationModel) => {
   return (
       <div>
         <p> {number} </p>
         <p>Client: {input_transcript} </p>
         <p>Server: {output_transcript}</p>
       </div>
   )
};

export default Conversation;
