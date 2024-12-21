from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.document_retrieval import DocumentRetrieval
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class Chatbot:
    def __init__(self, document_retrieval: DocumentRetrieval):
        self.document_retrieval = document_retrieval
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY
        )
    
    def format_questionnaire_context(self, questionnaire_data: dict) -> str:
        """Format questionnaire data into a readable context"""
        if not questionnaire_data:
            return "No questionnaire data available."
        
        context = []
        for key, value in questionnaire_data.items():
            if isinstance(value, (list, tuple)):
                context.append(f"{key}: {', '.join(value)}")
            else:
                context.append(f"{key}: {value}")
        
        return "\n".join(context)
    
    def get_relevant_context(self, query: str) -> str:
        """Get relevant document context for the query"""
        try:
            documents = self.document_retrieval.search(query)
            if not documents:
                return "No relevant documents found."
            
            context = []
            for doc in documents:
                context.append(f"Document: {doc.get('title', 'Untitled')}\n{doc.get('content', '')}\n")
            
            return "\n".join(context)
        except Exception as e:
            logger.error(f"Error retrieving document context: {str(e)}")
            return "Error retrieving document context."

    async def get_response(self, query: str, questionnaire_data: Dict = None) -> str:
        """Get a response from the chatbot"""
        try:
            # Get contexts
            questionnaire_context = self.format_questionnaire_context(questionnaire_data or {})
            document_context = self.get_relevant_context(query)
            
            # Create messages
            messages = [
                SystemMessage(content=f"""You are an AI assistant specializing in biotech regulations. 
                Use the following context to answer the user's question:
                
                Questionnaire Context:
                {questionnaire_context}
                
                Document Context:
                {document_context}
                
                Remember to:
                1. Be accurate and precise
                2. Cite specific regulations when possible
                3. Acknowledge if information is incomplete or uncertain"""),
                HumanMessage(content=query)
            ]
            
            # Get response
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error getting chatbot response: {str(e)}")
            return "I apologize, but I encountered an error while processing your request. Please try again."
