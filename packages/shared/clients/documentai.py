"""Document AI client for Project Agent."""

import os
from typing import Dict, Any, List
from google.cloud import documentai


class DocumentAIClient:
    """Client for Document AI operations."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT")
        self.location = os.getenv("REGION", "us")
        self.processor_id = os.getenv("DOC_AI_PROCESSOR")
        self.client = documentai.DocumentProcessorServiceClient()
    
    def process_document(self, file_content: bytes, mime_type: str) -> Dict[str, Any]:
        """
        Process a document using Document AI.
        
        Args:
            file_content: Raw file content as bytes
            mime_type: MIME type of the document
            
        Returns:
            Dictionary containing processed document data
        """
        try:
            # Configure the process request
            name = self.processor_id
            
            # Read the file into memory
            raw_document = documentai.RawDocument(
                content=file_content,
                mime_type=mime_type
            )
            
            # Configure the process request
            request = documentai.ProcessRequest(
                name=name,
                raw_document=raw_document
            )
            
            # Process the document
            result = self.client.process_document(request=request)
            document = result.document
            
            # Extract text and metadata
            extracted_text = self.extract_text(document)
            pages = self.extract_pages(document)
            
            return {
                "text": extracted_text,
                "pages": pages,
                "entities": self.extract_entities(document),
                "tables": self.extract_tables(document),
                "confidence": self.calculate_confidence(document),
                "page_count": len(pages)
            }
            
        except Exception as e:
            print(f"Error processing document: {e}")
            return {
                "text": "",
                "pages": [],
                "entities": [],
                "tables": [],
                "confidence": 0.0,
                "page_count": 0,
                "error": str(e)
            }
    
    def extract_text(self, document: documentai.Document = None, content: bytes = None) -> str:
        """Extract text from document using Document AI."""
        if document:
            return document.text or ""
        
        if content:
            # Fallback for simple text extraction
            try:
                return content.decode('utf-8', errors='ignore')
            except Exception:
                return ""
        
        return ""
    
    def extract_pages(self, document: documentai.Document) -> List[Dict[str, Any]]:
        """Extract page information from a processed document."""
        pages = []
        for i, page in enumerate(document.pages):
            page_text = ""
            if hasattr(page, 'paragraphs'):
                for paragraph in page.paragraphs:
                    if paragraph.layout:
                        page_text += paragraph.layout.text_anchor.content + "\n"
            
            pages.append({
                "page_number": i + 1,
                "text": page_text.strip(),
                "dimension": {
                    "width": page.dimension.width if page.dimension else 0,
                    "height": page.dimension.height if page.dimension else 0
                }
            })
        
        return pages
    
    def extract_entities(self, document: documentai.Document) -> List[Dict[str, Any]]:
        """Extract entities from a processed document."""
        entities = []
        for entity in document.entities:
            entities.append({
                "type": entity.type_,
                "mention_text": entity.mention_text,
                "confidence": entity.confidence
            })
        
        return entities
    
    def extract_tables(self, document: documentai.Document) -> List[Dict[str, Any]]:
        """Extract tables from a processed document."""
        tables = []
        for page in document.pages:
            for table in page.tables:
                table_data = {
                    "rows": len(table.body_rows) + len(table.header_rows),
                    "columns": 0,
                    "cells": []
                }
                
                # Extract cells
                for row in table.body_rows + table.header_rows:
                    for cell in row.cells:
                        if cell.layout:
                            table_data["cells"].append({
                                "text": cell.layout.text_anchor.content,
                                "confidence": cell.layout.confidence
                            })
                
                if table_data["cells"]:
                    tables.append(table_data)
        
        return tables
    
    def calculate_confidence(self, document: documentai.Document) -> float:
        """Calculate overall confidence score for the document."""
        if not document.pages:
            return 0.0
        
        total_confidence = 0.0
        count = 0
        
        for page in document.pages:
            if page.layout and hasattr(page.layout, 'confidence'):
                total_confidence += page.layout.confidence
                count += 1
        
        return total_confidence / count if count > 0 else 0.0
