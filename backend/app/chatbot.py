from typing import List, Tuple, Any
from app.document_storage import DocumentStorage
from app.utils.document_types import DocumentMetadata

async def process_query(
    query: str,
    doc_storage: DocumentStorage,
    reference_docs: List[DocumentMetadata],
    chat_attachments: List[DocumentMetadata],
    context_size: int = 3
) -> Tuple[str, List[dict]]:
    """
    Process a chat query using both reference documents and chat attachments.
    
    Args:
        query: The user's question
        doc_storage: Document storage instance
        reference_docs: List of reference documents
        chat_attachments: List of chat attachments
        context_size: Number of relevant documents to consider
    
    Returns:
        Tuple containing:
        - Response text
        - List of source documents used
    """
    try:
        # Combine reference docs and chat attachments
        all_docs = reference_docs + chat_attachments
        
        # For now, return a simple response (you can integrate with an LLM here)
        if not all_docs:
            return (
                "I couldn't find any relevant documents to answer your question. " +
                "Please try rephrasing your question or provide more context.",
                []
            )
        
        # Simple response based on found documents
        response = (
            "Based on your product description (Diagnostic device, life-threatening use, " +
            "for healthcare professionals, requiring sterilization, 3-day body contact), " +
            "here are the key regulations:\n\n" +
            "1. EU MDR 2017/745 - Your product likely falls under Class III due to:\n" +
            "   - Life-threatening use\n" +
            "   - Invasive nature (3-day body contact)\n" +
            "   - Sterilization requirement\n\n" +
            "2. ISO 13485:2016 - Quality Management System\n" +
            "3. ISO 14971:2019 - Risk Management\n" +
            "4. ISO 11137 - Sterilization Standards\n\n" +
            "The EU MDR is particularly critical as it defines safety requirements, " +
            "clinical evaluation needs, and post-market surveillance obligations."
        )
        
        # Mock sources for now
        sources = [{
            "id": "1",
            "title": "EU MDR 2017/745",
            "type": "REFERENCE"
        }, {
            "id": "2",
            "title": "ISO 13485:2016",
            "type": "REFERENCE"
        }]
        
        return response, sources
    
    except Exception as e:
        raise Exception(f"Error processing query: {str(e)}")
