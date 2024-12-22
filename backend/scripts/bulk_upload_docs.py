#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
from manage_reference_docs import upload_document

def bulk_upload_documents(directory: str, base_url: str = "http://localhost:8000"):
    """Upload all PDF files from a directory."""
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    # Get all PDF files
    pdf_files = list(directory.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in the directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF files.")
    
    # Upload each file
    for pdf_file in pdf_files:
        try:
            # Use filename without extension as title
            title = pdf_file.stem.replace('_', ' ').title()
            
            print(f"\nUploading {pdf_file.name}...")
            result = upload_document(
                file_path=str(pdf_file),
                title=title,
                description=f"Uploaded from {directory.name}",
                categories=["Regulations"]
            )
            print(f"Success! Document ID: {result.get('id')}")
            
        except Exception as e:
            print(f"Error uploading {pdf_file.name}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Bulk upload PDF documents")
    parser.add_argument("directory", help="Directory containing PDF files")
    args = parser.parse_args()
    
    try:
        bulk_upload_documents(args.directory)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
