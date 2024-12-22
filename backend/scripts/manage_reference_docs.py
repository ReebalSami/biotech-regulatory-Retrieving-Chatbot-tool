#!/usr/bin/env python3

import argparse
import os
import requests
from pathlib import Path
from typing import List, Optional

def upload_document(
    file_path: str,
    title: str,
    description: Optional[str] = None,
    categories: Optional[List[str]] = None,
    base_url: str = "http://localhost:8000"
) -> dict:
    """Upload a reference document to the system."""
    url = f"{base_url}/admin/documents/upload"
    
    # Prepare the file
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Prepare form data
    files = {"file": (file_path.name, open(file_path, "rb"))}
    data = {
        "title": title,
        "description": description or "",
        "categories": categories or []
    }
    
    # Make the request
    response = requests.post(url, files=files, data=data)
    response.raise_for_status()
    
    return response.json()

def list_documents(base_url: str = "http://localhost:8000") -> List[dict]:
    """List all reference documents in the system."""
    url = f"{base_url}/admin/documents"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def delete_document(doc_id: str, base_url: str = "http://localhost:8000") -> dict:
    """Delete a reference document from the system."""
    url = f"{base_url}/admin/documents/{doc_id}"
    response = requests.delete(url)
    response.raise_for_status()
    return response.json()

def main():
    parser = argparse.ArgumentParser(description="Manage reference documents")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload a reference document")
    upload_parser.add_argument("file", help="Path to the document file")
    upload_parser.add_argument("title", help="Document title")
    upload_parser.add_argument("--description", help="Document description")
    upload_parser.add_argument("--categories", nargs="+", help="Document categories")
    
    # List command
    subparsers.add_parser("list", help="List all reference documents")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a reference document")
    delete_parser.add_argument("doc_id", help="Document ID to delete")
    
    args = parser.parse_args()
    
    try:
        if args.command == "upload":
            result = upload_document(
                file_path=args.file,
                title=args.title,
                description=args.description,
                categories=args.categories
            )
            print(f"Document uploaded successfully: {result}")
        
        elif args.command == "list":
            documents = list_documents()
            print("\nReference Documents:")
            print("-" * 80)
            for doc in documents:
                print(f"ID: {doc['id']}")
                print(f"Title: {doc['title']}")
                print(f"Filename: {doc['filename']}")
                print(f"Upload Date: {doc['upload_date']}")
                if doc.get('categories'):
                    print(f"Categories: {', '.join(doc['categories'])}")
                print("-" * 80)
        
        elif args.command == "delete":
            result = delete_document(args.doc_id)
            print(f"Document deleted successfully: {result}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
