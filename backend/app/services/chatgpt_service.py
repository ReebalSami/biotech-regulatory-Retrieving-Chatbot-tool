import os
from typing import List
from openai import AsyncOpenAI
from fastapi import Depends, HTTPException

class ChatGPTService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
            )
            
        self.client = AsyncOpenAI(api_key=api_key)
        self.max_context_length = 7000  # Maximum context length for GPT-4
        
        self.system_prompt = """You are an AI assistant specializing in biotech regulatory compliance. 
        Your role is to help users understand and navigate regulatory requirements for biotech products.
        When providing information:
        1. Be precise and accurate
        2. Cite specific regulations when possible
        3. Highlight any important deadlines or requirements
        4. Suggest next steps or additional considerations
        5. If unsure, acknowledge limitations and suggest consulting official sources
        6. When analyzing documents, focus on extracting and explaining key regulatory information

        Base your responses on the provided context and your knowledge of regulations.
        If you receive document content in the context, analyze it and provide insights about the regulatory aspects.
        """

    def _chunk_text(self, text: str, chunk_size: int = 4000) -> List[str]:
        """Split text into chunks that fit within token limits."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            # Rough estimate: 1 word ≈ 1.3 tokens
            word_length = len(word) * 1.3
            if current_length + word_length > chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    async def generate_response(
        self,
        user_message: str,
        context: List[str],
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a response using GPT-4 based on the user's message and context.
        
        Args:
            user_message: The user's question or message
            context: List of relevant document contents to provide context
            max_tokens: Maximum number of tokens in the response
            temperature: Controls randomness in the response (0.0-1.0)
            
        Returns:
            Generated response string
            
        Raises:
            HTTPException: If there is an error generating the response
        """
        try:
            # Prepare context by chunking long texts
            chunked_context = []
            for ctx in context:
                chunked_context.extend(self._chunk_text(ctx))
            
            # Calculate available context space
            system_tokens = len(self.system_prompt.split()) * 1.3
            message_tokens = len(user_message.split()) * 1.3
            available_tokens = self.max_context_length - system_tokens - message_tokens - max_tokens
            
            # Select context chunks that fit within token limit
            selected_context = []
            current_tokens = 0
            for chunk in chunked_context:
                chunk_tokens = len(chunk.split()) * 1.3
                if current_tokens + chunk_tokens > available_tokens:
                    break
                selected_context.append(chunk)
                current_tokens += chunk_tokens
            
            # Prepare messages
            messages = [
                {"role": "system", "content": self.system_prompt},
            ]
            
            # Add context if available
            if selected_context:
                context_text = "\n\n".join(selected_context)
                messages.append({
                    "role": "system",
                    "content": f"Here is relevant context from regulatory documents:\n\n{context_text}"
                })
            
            # Add user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = await self.client.chat.completions.create(
                model="gpt-4",  # You can change this to gpt-4-turbo if needed
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating response: {str(e)}"
            )

    def __call__(self):
        """Make the service injectable in FastAPI"""
        return self
