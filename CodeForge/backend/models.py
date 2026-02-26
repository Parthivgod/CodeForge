from sqlalchemy import Column, Integer, String, Float, ARRAY, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class CodeGraph(Base):
    __tablename__ = 'code_graph'
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, index=True)
    file_path = Column(String)
    function_name = Column(String)
    source_code = Column(String)
    loc = Column(Integer)
    # Simplified graph - edges would be separate table in production
    
class NodeEmbeddings(Base):
    __tablename__ = 'node_embeddings'
    id = Column(Integer, primary_key=True)
    job_id = Column(String, index=True)
    node_id = Column(Integer)
    # Using 128 dim for local placeholder, usually 1536 for OpenAI
    embedding = Column(Vector(128)) 

class Clusters(Base):
    __tablename__ = 'clusters'
    id = Column(Integer, primary_key=True)
    job_id = Column(String, index=True)
    cluster_id = Column(Integer)
    name = Column(String) # e.g. "Billing Service"
    node_ids = Column(ARRAY(Integer))
    description = Column(String)
    confidence = Column(Float)
    loc_count = Column(Integer)
