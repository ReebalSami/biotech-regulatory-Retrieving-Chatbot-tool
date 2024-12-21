from typing import List, Dict
import openai
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.document_retrieval import DocumentRetrieval

class Chatbot:
    def __init__(self, document_retrieval: DocumentRetrieval):
        self.document_retrieval = document_retrieval
        self.llm = ChatOpenAI(temperature=0.7, model="gpt-3.5-turbo")
        
        template = """You are an AI assistant helping with regulatory compliance for biotech companies.
        Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        
        Questionnaire Context:
        {questionnaire_context}
        
        Document Context:
        {document_context}
        
        Question: {question}
        
        Based on the questionnaire context and available documents, provide a tailored response that specifically addresses the user's situation.
        If certain requirements are particularly relevant to their case (based on the questionnaire data), emphasize those points.
        
        Answer:"""
        
        self.prompt = PromptTemplate.from_template(template)
        
        # Create the chain
        self.chain = (
            {
                "document_context": self.get_relevant_context,
                "question": RunnablePassthrough(),
                "questionnaire_context": lambda x: self.format_questionnaire_context(x.get("questionnaire_data", {}))
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def format_questionnaire_context(self, questionnaire_data: Dict) -> str:
        """Format questionnaire data into a readable string"""
        if not questionnaire_data:
            return "No questionnaire data provided."
            
        context_parts = [
            f"Product Purpose: {questionnaire_data.get('intended_purpose', 'Not specified')}",
            f"Life-threatening Use: {'Yes' if questionnaire_data.get('life_threatening') else 'No'}",
            f"User Type: {questionnaire_data.get('user_type', 'Not specified')}",
            f"Requires Sterilization: {'Yes' if questionnaire_data.get('requires_sterilization') else 'No'}",
            f"Body Contact Duration: {questionnaire_data.get('body_contact_duration', 'Not specified')}"
        ]
        
        return "\n".join(context_parts)

    def get_relevant_context(self, query: str) -> str:
        """Get relevant documents for the query"""
        documents = self.document_retrieval.search(query)
        if not documents:
            return "No relevant documents found."
        return "\n\n".join([f"Document {i+1}:\n{doc['content']}" 
                           for i, doc in enumerate(documents)])

    async def get_response(self, query: str, questionnaire_data: Dict = None) -> str:
        """Get a response from the chatbot"""
        try:
            response = self.chain.invoke({
                "question": query,
                "questionnaire_data": questionnaire_data or {}
            })
            return response
        except Exception as e:
            print(f"Error getting chatbot response: {str(e)}")
            return "I apologize, but I encountered an error while processing your request. Please try again."
