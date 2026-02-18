"""
Phase 0B: Knowledge Extraction Agent - Test Suite
Tests the full pipeline: parse → extract → detect → recommend → approve
"""

import pytest
import os
import tempfile
from app.core.database import get_db
from app.models.sql import Base, DocumentUpload, KnowledgeRecommendation, KnowledgeNote
from app.services.document_parser_service import DocumentParserService
from app.services.entity_extractor_service import EntityExtractorService
from app.services.nuance_detector_service import NuanceDetectorService
from app.services.recommendation_generator_service import RecommendationGeneratorService
from app.services.knowledge_extraction_service import KnowledgeExtractionService
from app.services.knowledge_enrichment_service import KnowledgeEnrichmentService

# ── Test DB (real Postgres — same as app, isolated by cleanup) ────────────────
@pytest.fixture(scope="module")
def db():
    """Use real Postgres DB; clean up test data after."""
    session = next(get_db())
    yield session
    # Clean up: delete child rows first (FK constraint)
    test_docs = session.query(DocumentUpload).filter(
        DocumentUpload.filename.like("meeting%.txt")
    ).all()
    for doc in test_docs:
        session.query(KnowledgeRecommendation).filter(
            KnowledgeRecommendation.document_id == doc.id
        ).delete(synchronize_session=False)
    session.query(DocumentUpload).filter(
        DocumentUpload.filename.like("meeting%.txt")
    ).delete(synchronize_session=False)
    session.commit()
    session.close()


@pytest.fixture(scope="module")
def sample_txt(tmp_path_factory):
    content = """Meeting Notes - D&B Data Discussion

Attendees: Alice, Bob

Alice: The key difference between cmpbol and cmpbos is important.
cmpbol shows cumulative ownership percentages but cmpbos shows pairwise relationships.

Bob: Watch out for DUNS numbers - they can have leading zeros, so always store them as strings.

Alice: Best practice is to always check the reliability code before using financial data.
A code of 9 means the data is estimated, not actual.

Bob: Unlike DUNS, registration numbers vary by jurisdiction. Always include the country code.
"""
    p = tmp_path_factory.mktemp("docs") / "meeting.txt"
    p.write_text(content)
    return str(p)


# ── 1. Document Parser ────────────────────────────────────────────────────────
class TestDocumentParser:
    def test_parse_txt(self, sample_txt):
        parser = DocumentParserService()
        doc = parser.parse_file(sample_txt)
        assert doc.content, "Content should not be empty"
        assert "cmpbol" in doc.content
        # file_type is normalised to mime-style 'text' for .txt files
        assert doc.metadata.file_type in ("txt", "text")

    def test_segments_created(self, sample_txt):
        parser = DocumentParserService()
        doc = parser.parse_file(sample_txt)
        assert len(doc.segments) > 0, "Should produce at least one segment"

    def test_metadata_extracted(self, sample_txt):
        parser = DocumentParserService()
        doc = parser.parse_file(sample_txt)
        assert doc.metadata.filename == "meeting.txt"

    def test_unsupported_format_raises(self, tmp_path):
        bad_file = tmp_path / "file.xyz"
        bad_file.write_text("hello")
        parser = DocumentParserService()
        with pytest.raises(ValueError):
            parser.parse_file(str(bad_file))


# ── 2. Entity Extractor ───────────────────────────────────────────────────────
class TestEntityExtractor:
    TEXT = (
        "The cmpbol module shows cumulative ownership. "
        "Always store organization.duns as a string. "
        "Use the /api/v1/entities endpoint for lookups."
    )

    def test_extracts_modules(self):
        extractor = EntityExtractorService()
        entities = extractor.extract_entities(self.TEXT)
        modules = [e for e in entities if e.type == "module"]
        assert any("cmpbol" in e.value.lower() for e in modules), "Should detect cmpbol"

    def test_extracts_fields(self):
        extractor = EntityExtractorService()
        entities = extractor.extract_entities(self.TEXT)
        fields = [e for e in entities if e.type == "field"]
        assert any("organization.duns" in e.value for e in fields), "Should detect field path"

    def test_extracts_endpoints(self):
        extractor = EntityExtractorService()
        entities = extractor.extract_entities(self.TEXT)
        endpoints = [e for e in entities if e.type == "endpoint"]
        assert any("/api/v1/entities" in e.value for e in endpoints), "Should detect endpoint"

    def test_no_duplicates(self):
        extractor = EntityExtractorService()
        entities = extractor.extract_entities(self.TEXT + " " + self.TEXT)
        values = [(e.type, e.value, e.position) for e in entities]
        assert len(values) == len(set(values)), "No duplicate entities"


# ── 3. Nuance Detector ────────────────────────────────────────────────────────
class TestNuanceDetector:
    TEXT = (
        "The difference between cmpbol and cmpbos is critical. "
        "Watch out for DUNS numbers with leading zeros, this can cause issues. "
        "Make sure to check the reliability code before using financial data. "
        "Best practice is to always use cmpbos for graph visualisations. "
        "Don't forget that registration numbers vary by jurisdiction."
    )

    def test_detects_comparison(self):
        detector = NuanceDetectorService()
        nuances = detector._detect_with_patterns(self.TEXT, [])
        comparisons = [n for n in nuances if n.type == "comparison"]
        assert len(comparisons) > 0, "Should detect at least one comparison"

    def test_detects_gotcha(self):
        detector = NuanceDetectorService()
        nuances = detector._detect_with_patterns(self.TEXT, [])
        gotchas = [n for n in nuances if n.type == "gotcha"]
        assert len(gotchas) > 0, "Should detect at least one gotcha"

    def test_detects_best_practice(self):
        detector = NuanceDetectorService()
        nuances = detector._detect_with_patterns(self.TEXT, [])
        bps = [n for n in nuances if n.type == "best_practice"]
        assert len(bps) > 0, "Should detect at least one best practice"

    def test_confidence_range(self):
        detector = NuanceDetectorService()
        nuances = detector._detect_with_patterns(self.TEXT, [])
        for n in nuances:
            assert 0.0 <= n.confidence <= 1.0, f"Confidence out of range: {n.confidence}"


# ── 4. Recommendation Generator ──────────────────────────────────────────────
class TestRecommendationGenerator:
    def test_generates_from_nuances(self):
        from app.services.nuance_detector_service import Nuance
        nuances = [
            Nuance(
                type="comparison",
                severity="warning",
                entities_involved=["cmpbol", "cmpbos"],
                statement="cmpbol shows cumulative but cmpbos shows pairwise",
                explanation="Different calculation methods",
                confidence=0.8,
            ),
            Nuance(
                type="gotcha",
                severity="warning",
                entities_involved=["duns"],
                statement="Watch out for DUNS leading zeros",
                explanation="Store as string not integer",
                confidence=0.7,
            ),
        ]
        gen = RecommendationGeneratorService()
        recs = gen.generate_recommendations(nuances, "test.txt")
        assert len(recs) == 2

    def test_comparison_title_format(self):
        from app.services.nuance_detector_service import Nuance
        nuance = Nuance(
            type="comparison", severity="warning",
            entities_involved=["A", "B"],
            statement="A differs from B", explanation="Key difference",
            confidence=0.8,
        )
        gen = RecommendationGeneratorService()
        recs = gen.generate_recommendations([nuance], "test.txt")
        assert "A" in recs[0].title and "B" in recs[0].title

    def test_tags_extracted(self):
        from app.services.nuance_detector_service import Nuance
        nuance = Nuance(
            type="gotcha", severity="warning",
            entities_involved=["duns"],
            statement="Watch out for DUNS", explanation="Pitfall",
            confidence=0.7,
        )
        gen = RecommendationGeneratorService()
        recs = gen.generate_recommendations([nuance], "test.txt")
        assert "gotcha" in recs[0].tags or "pitfall" in recs[0].tags

    def test_confidence_boosted_for_comparison(self):
        from app.services.nuance_detector_service import Nuance
        nuance = Nuance(
            type="comparison", severity="warning",
            entities_involved=["X", "Y"],
            statement="X is different from Y in many important ways",
            explanation="Comparison", confidence=0.7,
        )
        gen = RecommendationGeneratorService()
        recs = gen.generate_recommendations([nuance], "test.txt")
        assert recs[0].confidence >= 0.7


# ── 5. Full Orchestration Service ─────────────────────────────────────────────
class TestKnowledgeExtractionService:
    def test_process_document(self, db, sample_txt):
        svc = KnowledgeExtractionService(db)
        result = svc.process_document(sample_txt, "meeting.txt")
        assert result["status"] == "completed"
        assert result["entities_count"] > 0
        assert result["recommendations_count"] > 0

    def test_document_persisted(self, db, sample_txt):
        svc = KnowledgeExtractionService(db)
        result = svc.process_document(sample_txt, "meeting2.txt")
        doc = svc.get_document(result["document_id"])
        assert doc is not None
        assert doc.status == "completed"

    def test_recommendations_persisted(self, db, sample_txt):
        svc = KnowledgeExtractionService(db)
        result = svc.process_document(sample_txt, "meeting3.txt")
        recs = svc.get_recommendations(result["document_id"])
        assert len(recs) > 0

    def test_approve_recommendation(self, db, sample_txt):
        svc = KnowledgeExtractionService(db)
        result = svc.process_document(sample_txt, "meeting4.txt")
        recs = svc.get_recommendations(result["document_id"])
        assert len(recs) > 0

        approval = svc.approve_recommendation(str(recs[0].id))
        assert approval["status"] == "approved"
        assert approval["note_id"] is not None

        # Verify note exists
        enrichment = KnowledgeEnrichmentService(db)
        note = enrichment.get_note(approval["note_id"])
        assert note is not None
        assert note.title == recs[0].title

    def test_reject_recommendation(self, db, sample_txt):
        svc = KnowledgeExtractionService(db)
        result = svc.process_document(sample_txt, "meeting5.txt")
        recs = svc.get_recommendations(result["document_id"])
        assert len(recs) > 0

        rejection = svc.reject_recommendation(str(recs[0].id), "Not accurate enough")
        assert rejection["status"] == "rejected"

        rec = svc.get_recommendation(str(recs[0].id))
        assert rec.status == "rejected"

    def test_edit_recommendation(self, db, sample_txt):
        svc = KnowledgeExtractionService(db)
        result = svc.process_document(sample_txt, "meeting6.txt")
        recs = svc.get_recommendations(result["document_id"])
        assert len(recs) > 0

        updated = svc.edit_recommendation(str(recs[0].id), {
            "title": "Edited Title",
            "severity": "critical"
        })
        assert updated.title == "Edited Title"
        assert updated.severity == "critical"
        assert updated.status == "edited"

    def test_list_all_documents(self, db, sample_txt):
        svc = KnowledgeExtractionService(db)
        docs = svc.get_all_documents()
        assert len(docs) > 0

    def test_invalid_document_id_raises(self, db):
        svc = KnowledgeExtractionService(db)
        with pytest.raises(Exception):
            svc.approve_recommendation("00000000-0000-0000-0000-000000000000")
