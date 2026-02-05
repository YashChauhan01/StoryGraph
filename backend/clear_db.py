#!/usr/bin/env python3
"""Clear Neo4j database for fresh start"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    # Delete all test-manuscript data
    result = session.run("""
        MATCH (m:Manuscript {id: "test-manuscript"}) 
        DETACH DELETE m
    """)
    print("✓ Cleared test-manuscript data from Neo4j")
    
driver.close()
