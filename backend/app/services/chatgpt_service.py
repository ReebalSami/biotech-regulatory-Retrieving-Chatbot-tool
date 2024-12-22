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
        
        self.system_prompt = """You are an AI assistant specializing in biotech regulatory compliance. 
        Your role is to help users understand and navigate regulatory requirements for biotech products.
        When providing information:
        1. Be precise and accurate
        2. Cite specific regulations when possible
        3. Highlight any important deadlines or requirements
        4. Suggest next steps or additional considerations
        5. If unsure, acknowledge limitations and suggest consulting official sources

        Base your responses on the provided context and your knowledge of regulations.
        """

    async def generate_response(
        self,
        user_message: str,
        context: List[str],
        max_tokens: int = 1000,
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
            # Prepare context
            context_text = "\n\n".join(context) if context else ""
            
            # Prepare messages
            messages = [
                {"role": "system", "content": self.system_prompt},
            ]
            
            # Add context if available
            if context_text:
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
