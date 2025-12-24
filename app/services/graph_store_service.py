"""Graph store service for NebulaGraph integration."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from app.db.nebula import get_nebula_client
from app.services.graph_extraction_service import GraphExtraction, Entity, Relationship
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GraphStoreService:
    """Service for managing knowledge graph in NebulaGraph."""
    
    def __init__(self):
        """Initialize graph store service."""
        self.client = get_nebula_client()
        logger.info("Graph store service initialized")
    
    async def store_graph(
        self,
        document_id: str,
        extraction: GraphExtraction,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        Store extracted graph in NebulaGraph.
        
        Args:
            document_id: Document identifier
            extraction: GraphExtraction with entities and relationships
            metadata: Optional document metadata
            
        Returns:
            Dict with counts of stored entities and relationships
        """
        try:
            entity_count = 0
            relationship_count = 0
            
            # Store entities as vertices
            for entity in extraction.entities:
                success = await self._store_entity(entity, document_id, metadata)
                if success:
                    entity_count += 1
            
            # Store relationships as edges
            for relationship in extraction.relationships:
                success = await self._store_relationship(relationship, document_id)
                if success:
                    relationship_count += 1
            
            logger.info(
                "Graph stored in NebulaGraph",
                document_id=document_id,
                entities_stored=entity_count,
                relationships_stored=relationship_count
            )
            
            return {
                "entities": entity_count,
                "relationships": relationship_count
            }
            
        except Exception as e:
            logger.error(
                "Failed to store graph",
                document_id=document_id,
                error=str(e),
                exc_info=True
            )
            return {"entities": 0, "relationships": 0}
    
    async def _store_entity(
        self,
        entity: Entity,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Store an entity as a vertex."""
        try:
            # Determine vertex tag based on entity type
            vertex_tag = self._get_vertex_tag(entity.type)
            
            # Prepare properties
            properties = {
                "name": entity.name,
                "type": entity.type,
                "confidence": entity.confidence,
                "document_id": document_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add entity properties
            for key, value in entity.properties.items():
                properties[key] = value
            
            # Add metadata if provided
            if metadata:
                properties["document_type"] = metadata.get("document_type", "")
                properties["user_id"] = metadata.get("user_id", "")
            
            # Insert vertex
            vertex_id = f"{document_id}:{entity.type}:{entity.name}"
            success = await self.client.insert_vertex(
                tag=vertex_tag,
                vid=vertex_id,
                properties=properties
            )
            
            return success
            
        except Exception as e:
            logger.error(
                "Failed to store entity",
                entity_name=entity.name,
                entity_type=entity.type,
                error=str(e)
            )
            return False
    
    async def _store_relationship(
        self,
        relationship: Relationship,
        document_id: str
    ) -> bool:
        """Store a relationship as an edge."""
        try:
            # Create vertex IDs
            source_id = f"{document_id}:{relationship.source}"
            target_id = f"{document_id}:{relationship.target}"
            
            # Prepare edge properties
            properties = {
                "confidence": relationship.confidence,
                "document_id": document_id,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add relationship properties
            for key, value in relationship.properties.items():
                properties[key] = value
            
            # Insert edge
            success = await self.client.insert_edge(
                edge_type=relationship.type,
                src_id=source_id,
                dst_id=target_id,
                properties=properties
            )
            
            return success
            
        except Exception as e:
            logger.error(
                "Failed to store relationship",
                source=relationship.source,
                target=relationship.target,
                type=relationship.type,
                error=str(e)
            )
            return False
    
    def _get_vertex_tag(self, entity_type: str) -> str:
        """Map entity type to NebulaGraph vertex tag."""
        type_mapping = {
            "person": "Person",
            "patient": "Patient",
            "provider": "Provider",
            "organization": "Organization",
            "insurance_company": "InsuranceCompany",
            "policy": "Policy",
            "claim": "Claim",
            "diagnosis": "Diagnosis",
            "diagnosis_code": "DiagnosisCode",
            "procedure": "Procedure",
            "procedure_code": "ProcedureCode",
            "coverage": "Coverage",
            "service": "Service",
            "document": "Document",
            "amount": "Amount",
            "date": "Date"
        }
        
        return type_mapping.get(entity_type.lower(), "Entity")
    
    async def query_coverage_path(
        self,
        policy_id: str,
        service_code: str,
        max_hops: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Query coverage path from policy to service.
        
        Args:
            policy_id: Policy identifier
            service_code: Service/procedure code
            max_hops: Maximum graph hops
            
        Returns:
            List of paths showing coverage relationships
        """
        try:
            query = f"""
            MATCH p = (policy:Policy {{vid: "{policy_id}"}})-[*1..{max_hops}]->(service:ProcedureCode {{name: "{service_code}"}})
            RETURN p
            LIMIT 10
            """
            
            result = await self.client.execute_query(query)
            
            paths = self._parse_paths(result)
            
            logger.info(
                "Coverage path query completed",
                policy_id=policy_id,
                service_code=service_code,
                paths_found=len(paths)
            )
            
            return paths
            
        except Exception as e:
            logger.error(
                "Coverage path query failed",
                policy_id=policy_id,
                service_code=service_code,
                error=str(e),
                exc_info=True
            )
            return []
    
    async def find_similar_claims(
        self,
        diagnosis_codes: List[str],
        procedure_codes: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar historical claims.
        
        Args:
            diagnosis_codes: List of ICD-10 codes
            procedure_codes: List of CPT codes
            limit: Maximum results
            
        Returns:
            List of similar claims
        """
        try:
            # Build query for similar claims
            diagnosis_filter = " OR ".join([f'd.name == "{code}"' for code in diagnosis_codes])
            procedure_filter = " OR ".join([f'p.name == "{code}"' for code in procedure_codes])
            
            query = f"""
            MATCH (claim:Claim)-[:diagnoses]->(d:DiagnosisCode),
                  (claim)-[:includes]->(p:ProcedureCode)
            WHERE ({diagnosis_filter}) AND ({procedure_filter})
            RETURN claim, collect(DISTINCT d.name) AS diagnoses, collect(DISTINCT p.name) AS procedures
            LIMIT {limit}
            """
            
            result = await self.client.execute_query(query)
            
            claims = self._parse_claims(result)
            
            logger.info(
                "Similar claims query completed",
                diagnosis_codes=diagnosis_codes,
                procedure_codes=procedure_codes,
                claims_found=len(claims)
            )
            
            return claims
            
        except Exception as e:
            logger.error(
                "Similar claims query failed",
                error=str(e),
                exc_info=True
            )
            return []
    
    async def get_entity_relationships(
        self,
        entity_id: str,
        relationship_type: Optional[str] = None,
        direction: str = "both"  # "in", "out", "both"
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships for an entity.
        
        Args:
            entity_id: Entity vertex ID
            relationship_type: Optional filter by relationship type
            direction: Relationship direction
            
        Returns:
            List of relationships
        """
        try:
            # Build query based on direction
            if direction == "out":
                pattern = f'(entity)-[r]->(target)'
            elif direction == "in":
                pattern = f'(source)-[r]->(entity)'
            else:
                pattern = f'(entity)-[r]-(other)'
            
            where_clause = f'entity.vid == "{entity_id}"'
            if relationship_type:
                where_clause += f' AND type(r) == "{relationship_type}"'
            
            query = f"""
            MATCH {pattern}
            WHERE {where_clause}
            RETURN r, entity, 
                   CASE 
                     WHEN id(startNode(r)) == id(entity) THEN endNode(r)
                     ELSE startNode(r)
                   END AS related
            LIMIT 100
            """
            
            result = await self.client.execute_query(query)
            
            relationships = self._parse_relationships(result)
            
            logger.info(
                "Entity relationships retrieved",
                entity_id=entity_id,
                relationship_type=relationship_type,
                direction=direction,
                count=len(relationships)
            )
            
            return relationships
            
        except Exception as e:
            logger.error(
                "Entity relationships query failed",
                entity_id=entity_id,
                error=str(e),
                exc_info=True
            )
            return []
    
    async def calculate_coverage_eligibility(
        self,
        patient_id: str,
        policy_id: str,
        service_codes: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate eligibility using graph traversal.
        
        Args:
            patient_id: Patient identifier
            policy_id: Policy identifier
            service_codes: List of service/procedure codes
            
        Returns:
            Eligibility analysis with coverage details
        """
        try:
            results = {
                "eligible_services": [],
                "ineligible_services": [],
                "coverage_details": []
            }
            
            for service_code in service_codes:
                # Query coverage path
                paths = await self.query_coverage_path(
                    policy_id=policy_id,
                    service_code=service_code
                )
                
                if paths:
                    results["eligible_services"].append(service_code)
                    results["coverage_details"].append({
                        "service_code": service_code,
                        "covered": True,
                        "paths": paths
                    })
                else:
                    results["ineligible_services"].append(service_code)
                    results["coverage_details"].append({
                        "service_code": service_code,
                        "covered": False,
                        "reason": "No coverage path found"
                    })
            
            logger.info(
                "Coverage eligibility calculated",
                patient_id=patient_id,
                policy_id=policy_id,
                total_services=len(service_codes),
                eligible_count=len(results["eligible_services"])
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Coverage eligibility calculation failed",
                patient_id=patient_id,
                policy_id=policy_id,
                error=str(e),
                exc_info=True
            )
            return {
                "eligible_services": [],
                "ineligible_services": service_codes,
                "coverage_details": [],
                "error": str(e)
            }
    
    def _parse_paths(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse path query results."""
        paths = []
        for row in result:
            if "p" in row:
                paths.append({
                    "path": row["p"],
                    "length": len(row["p"].get("edges", []))
                })
        return paths
    
    def _parse_claims(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse claim query results."""
        claims = []
        for row in result:
            claims.append({
                "claim": row.get("claim", {}),
                "diagnoses": row.get("diagnoses", []),
                "procedures": row.get("procedures", [])
            })
        return claims
    
    def _parse_relationships(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse relationship query results."""
        relationships = []
        for row in result:
            relationships.append({
                "relationship": row.get("r", {}),
                "entity": row.get("entity", {}),
                "related": row.get("related", {})
            })
        return relationships


# Singleton instance
_graph_store_service: Optional[GraphStoreService] = None


def get_graph_store_service() -> GraphStoreService:
    """
    Get or create graph store service instance.
    
    Returns:
        GraphStoreService instance
    """
    global _graph_store_service
    
    if _graph_store_service is None:
        _graph_store_service = GraphStoreService()
    
    return _graph_store_service
