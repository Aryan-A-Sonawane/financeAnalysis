"""NebulaGraph schema definitions and queries."""

from typing import Dict, List

# Space creation
CREATE_SPACE = """
CREATE SPACE IF NOT EXISTS finsight (
    partition_num = 10,
    replica_factor = 1,
    vid_type = FIXED_STRING(64)
);
"""

USE_SPACE = "USE finsight;"

# Tag (Node) Definitions
TAG_DEFINITIONS = {
    "User": """
        CREATE TAG IF NOT EXISTS User (
            user_id string NOT NULL,
            name string,
            dob date,
            ssn_hash string,
            created_at timestamp
        );
    """,
    "Policy": """
        CREATE TAG IF NOT EXISTS Policy (
            policy_id string NOT NULL,
            policy_number string NOT NULL,
            policy_type string,
            carrier string,
            effective_date date,
            expiration_date date,
            premium double,
            deductible_individual double,
            deductible_family double,
            oop_max_individual double,
            oop_max_family double,
            coinsurance_rate double,
            network_type string,
            created_at timestamp
        );
    """,
    "Coverage": """
        CREATE TAG IF NOT EXISTS Coverage (
            coverage_id string NOT NULL,
            coverage_type string,
            service_category string,
            is_preventive bool,
            requires_preauth bool,
            copay double,
            coinsurance double,
            annual_limit double,
            visit_limit int
        );
    """,
    "Procedure": """
        CREATE TAG IF NOT EXISTS Procedure (
            procedure_id string NOT NULL,
            cpt_code string,
            hcpcs_code string,
            description string,
            category string,
            avg_cost double
        );
    """,
    "Diagnosis": """
        CREATE TAG IF NOT EXISTS Diagnosis (
            diagnosis_id string NOT NULL,
            icd10_code string NOT NULL,
            description string,
            category string,
            is_chronic bool
        );
    """,
    "Provider": """
        CREATE TAG IF NOT EXISTS Provider (
            provider_id string NOT NULL,
            npi string NOT NULL,
            name string,
            specialty string,
            address string,
            network_status string
        );
    """,
    "Claim": """
        CREATE TAG IF NOT EXISTS Claim (
            claim_id string NOT NULL,
            claim_number string,
            submission_date date,
            service_date date,
            billed_amount double,
            allowed_amount double,
            paid_amount double,
            patient_responsibility double,
            status string,
            denial_reason string,
            created_at timestamp
        );
    """,
    "Exclusion": """
        CREATE TAG IF NOT EXISTS Exclusion (
            exclusion_id string NOT NULL,
            exclusion_type string,
            description string,
            effective_date date,
            expiration_date date
        );
    """,
    "Document": """
        CREATE TAG IF NOT EXISTS Document (
            document_id string NOT NULL,
            doc_type string,
            file_path string,
            upload_date timestamp,
            processed bool
        );
    """,
    "Invoice": """
        CREATE TAG IF NOT EXISTS Invoice (
            invoice_id string NOT NULL,
            invoice_number string,
            vendor string,
            invoice_date date,
            total_amount double,
            tax_amount double,
            status string
        );
    """,
}

# Edge (Relationship) Definitions
EDGE_DEFINITIONS = {
    "HAS_POLICY": """
        CREATE EDGE IF NOT EXISTS HAS_POLICY (
            enrollment_date date,
            status string
        );
    """,
    "PROVIDES_COVERAGE": """
        CREATE EDGE IF NOT EXISTS PROVIDES_COVERAGE (
            priority int,
            conditions string
        );
    """,
    "COVERS_PROCEDURE": """
        CREATE EDGE IF NOT EXISTS COVERS_PROCEDURE (
            coverage_percentage double,
            requires_preauth bool,
            restrictions string
        );
    """,
    "COVERS_DIAGNOSIS": """
        CREATE EDGE IF NOT EXISTS COVERS_DIAGNOSIS (
            coverage_percentage double,
            limitations string
        );
    """,
    "HAS_EXCLUSION": """
        CREATE EDGE IF NOT EXISTS HAS_EXCLUSION (
            applies_to string
        );
    """,
    "EXCLUDES_PROCEDURE": """
        CREATE EDGE IF NOT EXISTS EXCLUDES_PROCEDURE ();
    """,
    "EXCLUDES_DIAGNOSIS": """
        CREATE EDGE IF NOT EXISTS EXCLUDES_DIAGNOSIS ();
    """,
    "CLAIMED_UNDER": """
        CREATE EDGE IF NOT EXISTS CLAIMED_UNDER (
            deductible_applied double,
            coinsurance_applied double
        );
    """,
    "FOR_PROCEDURE": """
        CREATE EDGE IF NOT EXISTS FOR_PROCEDURE (
            quantity int
        );
    """,
    "FOR_DIAGNOSIS": """
        CREATE EDGE IF NOT EXISTS FOR_DIAGNOSIS ();
    """,
    "SERVICED_BY": """
        CREATE EDGE IF NOT EXISTS SERVICED_BY (
            is_network bool
        );
    """,
    "PERFORMS_PROCEDURE": """
        CREATE EDGE IF NOT EXISTS PERFORMS_PROCEDURE (
            frequency int
        );
    """,
    "DESCRIBES_POLICY": """
        CREATE EDGE IF NOT EXISTS DESCRIBES_POLICY ();
    """,
    "DESCRIBES_CLAIM": """
        CREATE EDGE IF NOT EXISTS DESCRIBES_CLAIM ();
    """,
    "BILLED_FOR": """
        CREATE EDGE IF NOT EXISTS BILLED_FOR ();
    """,
    "SIMILAR_TO": """
        CREATE EDGE IF NOT EXISTS SIMILAR_TO (
            similarity_score double
        );
    """,
}

# Index Definitions
INDEX_DEFINITIONS = {
    "user_id_index": "CREATE TAG INDEX IF NOT EXISTS user_id_index ON User(user_id(64));",
    "policy_number_index": "CREATE TAG INDEX IF NOT EXISTS policy_number_index ON Policy(policy_number(64));",
    "cpt_code_index": "CREATE TAG INDEX IF NOT EXISTS cpt_code_index ON Procedure(cpt_code(16));",
    "icd10_code_index": "CREATE TAG INDEX IF NOT EXISTS icd10_code_index ON Diagnosis(icd10_code(16));",
    "npi_index": "CREATE TAG INDEX IF NOT EXISTS npi_index ON Provider(npi(32));",
    "claim_number_index": "CREATE TAG INDEX IF NOT EXISTS claim_number_index ON Claim(claim_number(64));",
}

# Common Queries
QUERIES = {
    "check_procedure_coverage": """
        MATCH (u:User)-[:HAS_POLICY]->(p:Policy)-[:PROVIDES_COVERAGE]->(c:Coverage)-[:COVERS_PROCEDURE]->(pr:Procedure)
        WHERE u.user_id == $user_id AND pr.cpt_code == $cpt_code
        AND NOT EXISTS {
            MATCH (p)-[:HAS_EXCLUSION]->(e:Exclusion)-[:EXCLUDES_PROCEDURE]->(pr)
        }
        RETURN c, pr, p
    """,
    "find_coverage_gaps": """
        MATCH (p:Policy)-[:PROVIDES_COVERAGE]->(c:Coverage)
        WHERE p.policy_id == $policy_id
        WITH COLLECT(c.service_category) AS covered
        MATCH (pr:Procedure)
        WHERE NOT pr.category IN covered
        RETURN pr.category, COUNT(pr) AS uncovered_procedures
    """,
    "detect_fraud_patterns": """
        MATCH (c:Claim)-[:FOR_PROCEDURE]->(pr:Procedure),
              (c)-[:SERVICED_BY]->(prov:Provider)
        WHERE c.submission_date > date($start_date)
        WITH prov, pr, COUNT(c) AS claim_count, AVG(c.billed_amount) AS avg_amount
        WHERE claim_count > $threshold AND avg_amount > $amount_threshold
        RETURN prov.name, pr.description, claim_count, avg_amount
        ORDER BY claim_count DESC
    """,
    "find_similar_claims": """
        MATCH (c1:Claim)-[:SIMILAR_TO]-(c2:Claim)
        WHERE c1.claim_id == $claim_id
        RETURN c2, PROPERTIES(c2)
        ORDER BY c2.similarity_score DESC
        LIMIT $limit
    """,
    "get_policy_details": """
        MATCH (p:Policy)
        WHERE p.policy_id == $policy_id
        OPTIONAL MATCH (p)-[:PROVIDES_COVERAGE]->(c:Coverage)
        OPTIONAL MATCH (p)-[:HAS_EXCLUSION]->(e:Exclusion)
        RETURN p, COLLECT(DISTINCT c) AS coverages, COLLECT(DISTINCT e) AS exclusions
    """,
    "check_exclusions": """
        MATCH (p:Policy)-[:HAS_EXCLUSION]->(e:Exclusion)
        WHERE p.policy_id == $policy_id
        OPTIONAL MATCH (e)-[:EXCLUDES_PROCEDURE]->(pr:Procedure)
        OPTIONAL MATCH (e)-[:EXCLUDES_DIAGNOSIS]->(d:Diagnosis)
        WHERE pr.cpt_code == $procedure_code OR d.icd10_code == $diagnosis_code
        RETURN e, pr, d
    """,
    "get_provider_claim_history": """
        MATCH (prov:Provider)-[:SERVICED_BY]-(c:Claim)
        WHERE prov.npi == $provider_npi
        RETURN c, PROPERTIES(c)
        ORDER BY c.service_date DESC
        LIMIT $limit
    """,
}


def get_all_schema_statements() -> List[str]:
    """Get all schema creation statements in order."""
    statements = [CREATE_SPACE, USE_SPACE]
    
    # Add tag definitions
    statements.extend(TAG_DEFINITIONS.values())
    
    # Add edge definitions
    statements.extend(EDGE_DEFINITIONS.values())
    
    # Add index definitions
    statements.extend(INDEX_DEFINITIONS.values())
    
    return statements
