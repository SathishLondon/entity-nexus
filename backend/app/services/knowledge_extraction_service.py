"""
Knowledge Extraction Service
Orchestrates the full knowledge extraction pipeline
"""

import os
import uuid
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.sql import DocumentUpload, KnowledgeRecommendation
from app.services.document_parser_service import DocumentParserService
from app.services.entity_extractor_service import EntityExtractorService
from app.services.nuance_detector_service import NuanceDetectorService
from app.services.recommendation_generator_service import RecommendationGeneratorService
from app.services.knowledge_enrichment_service import KnowledgeEnrichmentService
from app.services.knowledge_base_builder import KnowledgeBaseBuilder
from app.services.reference_service import ReferenceService

logger = logging.getLogger(__name__)

class KnowledgeExtractionService:
    """
    Orchestrates the full knowledge extraction pipeline:
    Document → Parse → Extract Entities → Detect Nuances → Generate Recommendations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.parser = DocumentParserService()
        
        # Build knowledge base for entity extraction
        reference_service = ReferenceService()
        kb_builder = KnowledgeBaseBuilder(reference_service)
        knowledge_base = kb_builder.build()
        
        self.entity_extractor = EntityExtractorService(knowledge_base)
        self.nuance_detector = NuanceDetectorService()
        self.enrichment_service = KnowledgeEnrichmentService(db)
        self.recommendation_generator = RecommendationGeneratorService(self.enrichment_service)

    
    def process_document(self, file_path: str, filename: str, uploaded_by: str = "user") -> Dict:
        """
        Process a document through the full extraction pipeline.
        Returns document_id and processing status.
        """
        try:
            # Create document upload record
            doc_upload = DocumentUpload(
                filename=filename,
                file_type=filename.split('.')[-1].lower(),
                file_path=file_path,
                uploaded_by=uploaded_by,
                status="processing"
            )
            self.db.add(doc_upload)
            self.db.commit()
            self.db.refresh(doc_upload)
            
            logger.info(f"Processing document: {filename} (ID: {doc_upload.id})")
            
            # Step 1: Parse document
            parsed_doc = self.parser.parse_file(file_path)
            logger.info(f"Parsed document: {len(parsed_doc.content)} chars, {len(parsed_doc.segments)} segments")
            
            # Step 2: Extract entities
            entities = self.entity_extractor.extract_entities(parsed_doc.content)
            logger.info(f"Extracted {len(entities)} entities")
            
            # Step 3: Detect nuances
            nuances = self.nuance_detector.detect_nuances(parsed_doc.content, entities)
            logger.info(f"Detected {len(nuances)} nuances")
            
            # Step 4: Generate recommendations
            recommendations = self.recommendation_generator.generate_recommendations(
                nuances=nuances,
                source_document=filename,
                entities=entities
            )
            logger.info(f"Generated {len(recommendations)} recommendations")
            
            # Step 5: Save recommendations to database
            saved_count = 0
            for rec in recommendations:
                try:
                    db_rec = KnowledgeRecommendation(
                        document_id=doc_upload.id,
                        note_type=rec.note_type,
                        title=rec.title,
                        content=rec.content,
                        severity=rec.severity,
                        tags=rec.tags,
                        module_id=rec.module_id,
                        field_path=rec.field_path,
                        confidence=rec.confidence,
                        source_excerpt=rec.source_excerpt,
                        reasoning=rec.reasoning,
                        status="pending"
                    )
                    self.db.add(db_rec)
                    saved_count += 1
                except Exception as e:
                    logger.error(f"Failed to save recommendation: {e}")
            
            self.db.commit()
            
            # Update document status
            doc_upload.status = "completed"
            doc_upload.extra_data = {
                "entities_count": len(entities),
                "nuances_count": len(nuances),
                "recommendations_count": saved_count
            }
            self.db.commit()
            
            logger.info(f"Document processing completed: {saved_count} recommendations saved")
            
            return {
                "document_id": str(doc_upload.id),
                "status": "completed",
                "entities_count": len(entities),
                "nuances_count": len(nuances),
                "recommendations_count": saved_count
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}", exc_info=True)
            
            # Update document status to failed
            if 'doc_upload' in locals():
                doc_upload.status = "failed"
                doc_upload.extra_data = {"error": str(e)}
                self.db.commit()
            
            raise
    
    def get_document(self, document_id: str) -> DocumentUpload:
        """Get document upload by ID"""
        return self.db.query(DocumentUpload).filter(
            DocumentUpload.id == uuid.UUID(document_id)
        ).first()
    
    def get_all_documents(self) -> List[DocumentUpload]:
        """Get all document uploads"""
        return self.db.query(DocumentUpload).order_by(
            DocumentUpload.uploaded_at.desc()
        ).all()
    
    def get_recommendations(self, document_id: str) -> List[KnowledgeRecommendation]:
        """Get all recommendations for a document"""
        return self.db.query(KnowledgeRecommendation).filter(
            KnowledgeRecommendation.document_id == uuid.UUID(document_id)
        ).order_by(
            KnowledgeRecommendation.confidence.desc()
        ).all()
    
    def get_recommendation(self, rec_id: str) -> KnowledgeRecommendation:
        """Get a specific recommendation"""
        return self.db.query(KnowledgeRecommendation).filter(
            KnowledgeRecommendation.id == uuid.UUID(rec_id)
        ).first()
    
    def approve_recommendation(self, rec_id: str, reviewed_by: str = "user") -> Dict:
        """Approve a recommendation and create knowledge note"""
        rec = self.get_recommendation(rec_id)
        if not rec:
            raise ValueError(f"Recommendation not found: {rec_id}")
        
        if rec.status == "approved":
            return {"status": "already_approved", "note_id": rec.created_note_id}
        
        # Create knowledge note
        note = self.enrichment_service.add_note(
            title=rec.title,
            content=rec.content,
            note_type=rec.note_type,
            module_id=rec.module_id,
            field_path=rec.field_path,
            tags=rec.tags,
            severity=rec.severity,
            created_by=reviewed_by,
            metadata={
                "source_document": str(rec.document_id),
                "source_excerpt": rec.source_excerpt,
                "confidence": rec.confidence,
                "reasoning": rec.reasoning
            }
        )
        
        # Update recommendation status
        rec.status = "approved"
        rec.reviewed_by = reviewed_by
        rec.created_note_id = note.id
        from datetime import datetime
        rec.reviewed_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Approved recommendation {rec_id}, created note {note.id}")
        
        return {
            "status": "approved",
            "note_id": note.id,
            "recommendation_id": str(rec.id)
        }
    
    def reject_recommendation(self, rec_id: str, reason: str, reviewed_by: str = "user") -> Dict:
        """Reject a recommendation with feedback"""
        rec = self.get_recommendation(rec_id)
        if not rec:
            raise ValueError(f"Recommendation not found: {rec_id}")
        
        rec.status = "rejected"
        rec.reviewed_by = reviewed_by
        from datetime import datetime
        rec.reviewed_at = datetime.utcnow()
        
        # Store rejection reason in extra metadata
        if not rec.extra_data:
            rec.extra_data = {}
        rec.extra_data["rejection_reason"] = reason
        
        self.db.commit()
        
        logger.info(f"Rejected recommendation {rec_id}: {reason}")
        
        return {
            "status": "rejected",
            "recommendation_id": str(rec.id)
        }
    
    def edit_recommendation(self, rec_id: str, updates: Dict) -> KnowledgeRecommendation:
        """Edit a recommendation before approval"""
        rec = self.get_recommendation(rec_id)
        if not rec:
            raise ValueError(f"Recommendation not found: {rec_id}")
        
        # Update allowed fields
        if "title" in updates:
            rec.title = updates["title"]
        if "content" in updates:
            rec.content = updates["content"]
        if "tags" in updates:
            rec.tags = updates["tags"]
        if "severity" in updates:
            rec.severity = updates["severity"]
        if "module_id" in updates:
            rec.module_id = updates["module_id"]
        if "field_path" in updates:
            rec.field_path = updates["field_path"]
        
        rec.status = "edited"
        self.db.commit()
        self.db.refresh(rec)
        
        logger.info(f"Edited recommendation {rec_id}")
        
        return rec
