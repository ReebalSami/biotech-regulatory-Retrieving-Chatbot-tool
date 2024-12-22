"""
Text extraction module for processing PDF documents and preparing them for search.
"""

import PyPDF2
import re
from typing import List, Optional, Dict, Union
from pathlib import Path
import json
import os
import io
import magic
from docx import Document

class TextExtractor:
    def __init__(self, cache_dir: str = "./data/text_cache"):
        """Initialize the text extractor with caching capability.
        
        Args:
            cache_dir: Directory to store extracted text cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s.,;:!?()\[\]{}"\'`-]', '', text)
        return text.strip()
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks for better search.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            
            # Adjust chunk end to not split words
            if end < text_len:
                # Find the next space after chunk_size
                while end < text_len and text[end] != ' ':
                    end += 1
            
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Move start position for next chunk, considering overlap
            start = end - overlap
        
        return chunks
    
    def get_cache_path(self, file_path: str) -> Path:
        """Get the cache file path for a document.
        
        Args:
            file_path: Path to the original document
            
        Returns:
            Path to the cache file
        """
        file_hash = str(hash(file_path))
        return self.cache_dir / f"{file_hash}.json"
    
    def extract_from_pdf(self, file_path: str, force_extract: bool = False) -> Dict[str, any]:
        """Extract text from a PDF file with caching.
        
        Args:
            file_path: Path to the PDF file
            force_extract: Whether to force extraction even if cache exists
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        cache_path = self.get_cache_path(file_path)
        
        # Check cache first
        if not force_extract and cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        try:
            with open(file_path, 'rb') as file:
                # Create PDF reader object
                reader = PyPDF2.PdfReader(file)
                
                # Extract text from each page
                full_text = ""
                page_texts = []
                
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    cleaned_text = self._clean_text(text)
                    
                    if cleaned_text:
                        full_text += cleaned_text + " "
                        page_texts.append({
                            "page": page_num + 1,
                            "text": cleaned_text
                        })
                
                # Create chunks from the full text
                chunks = self._chunk_text(full_text)
                
                # Prepare the result
                result = {
                    "file_path": file_path,
                    "total_pages": len(reader.pages),
                    "full_text": full_text,
                    "pages": page_texts,
                    "chunks": chunks
                }
                
                # Cache the result
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                return result
                
        except Exception as e:
            raise Exception(f"Error extracting text from PDF {file_path}: {str(e)}")
    
    def extract_from_file(self, file_path: str, force_extract: bool = False) -> Dict[str, any]:
        """Extract text from a file based on its type.
        
        Args:
            file_path: Path to the file
            force_extract: Whether to force extraction even if cache exists
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        file_path = str(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return self.extract_from_pdf(file_path, force_extract)
        elif ext == '.txt':
            # For text files, just read them directly
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    cleaned_text = self._clean_text(text)
                    chunks = self._chunk_text(cleaned_text)
                    
                    result = {
                        "file_path": file_path,
                        "full_text": cleaned_text,
                        "chunks": chunks
                    }
                    
                    # Cache the result
                    cache_path = self.get_cache_path(file_path)
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    return result
            except Exception as e:
                raise Exception(f"Error extracting text from file {file_path}: {str(e)}")
        else:
            raise ValueError(f"Unsupported file type: {ext}")

async def extract_text_from_file(content: Union[bytes, str], filename: str) -> str:
    """
    Extract text from various file types (PDF, DOCX, TXT)
    
    Args:
        content: File content as bytes or string
        filename: Name of the file
        
    Returns:
        Extracted text from the file
        
    Raises:
        ValueError: If file type is not supported
    """
    file_ext = os.path.splitext(filename)[1].lower()
    
    if isinstance(content, str):
        return content
        
    mime = magic.Magic(mime=True)
    file_type = mime.from_buffer(content)
    
    if file_type == 'application/pdf' or file_ext == '.pdf':
        # Handle PDF files
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
        
    elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or file_ext == '.docx':
        # Handle DOCX files
        docx_file = io.BytesIO(content)
        doc = Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
        
    elif file_type.startswith('text/') or file_ext in ['.txt', '.md', '.json']:
        # Handle text files
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return content.decode('latin-1')
            except UnicodeDecodeError:
                raise ValueError(f"Could not decode text file: {filename}")
                
    else:
        raise ValueError(f"Unsupported file type: {file_type} for file: {filename}")
