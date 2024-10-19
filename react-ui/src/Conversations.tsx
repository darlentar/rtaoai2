import React, { useState, useEffect, useRef } from 'react';
import Conversation, {ConversationModel} from './Conversation';

export interface ConversationsModel {
   conversations: ConversationModel[];
};

const ConversationList = ({conversations}: ConversationsModel) => {
   return (
     <div>
       {conversations.map((item) => <Conversation key={item.number} number={item.number} input_transcript={item.input_transcript} output_transcript={item.output_transcript}/>
       )}
     </div>
   )
}

export default ConversationList;
