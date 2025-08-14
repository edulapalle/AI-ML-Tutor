#!/usr/bin/env python3
"""
Build a comprehensive Neo4j knowledge graph for AI/ML:
- Nodes: (:Concept {slug, name, level}), (:Video {video_id, title, url}), (:Content {type, text})
- Edges: REQUIRES | RELATES_TO | CONTRASTS_WITH | COVERS | HAS_CONTENT
- Integrates StatQuest videos with generated educational content

ENV:
  NEO4J_URI=bolt+s://...  (Neo4j Aura)
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=...

USAGE:
  python build_kg.py --videos_json statquest_videos_export.json
"""

import os, json, argparse
from typing import List, Dict
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix SSL certificates for Neo4j connection
os.environ['SSL_CERT_FILE'] = '/etc/ssl/cert.pem'
os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/cert.pem'

# ----------------------
# Minimal curated concepts (≤ 40)
# ----------------------
CONCEPTS = [
    # slug, name, level
    ("ml-foundations", "Machine Learning Foundations", "beginner"),
    ("linear-regression", "Linear Regression", "beginner"),
    ("logistic-regression", "Logistic Regression", "beginner"),
    ("decision-trees", "Decision Trees", "beginner"),
    ("random-forest", "Random Forest", "beginner"),
    ("svm", "Support Vector Machines", "intermediate"),
    ("knn", "K-Nearest Neighbors", "beginner"),
    ("naive-bayes", "Naive Bayes", "beginner"),
    ("k-means", "K-Means Clustering", "beginner"),
    ("hierarchical-clustering", "Hierarchical Clustering", "intermediate"),
    ("pca", "Principal Component Analysis", "intermediate"),
    ("dim-reduction", "Dimensionality Reduction", "intermediate"),
    ("overfitting", "Overfitting", "beginner"),
    ("bias-variance", "Bias-Variance Tradeoff", "beginner"),
    ("cross-val", "Cross Validation", "beginner"),
    ("grad-descent", "Gradient Descent", "intermediate"),
    ("activation-funcs", "Activation Functions", "intermediate"),
    ("cnn", "Convolutional Neural Networks", "intermediate"),
    ("rnn", "Recurrent Neural Networks", "intermediate"),
    ("transformers", "Transformers", "advanced"),
    ("embeddings", "Embeddings", "intermediate"),
    ("rag", "Retrieval-Augmented Generation", "advanced"),
    ("roc-auc", "ROC and AUC", "intermediate"),
    ("precision-recall", "Precision and Recall", "beginner"),
    ("confusion-matrix", "Confusion Matrix", "beginner"),
    ("feature-engineering", "Feature Engineering", "beginner"),
    ("scaling", "Feature Scaling", "beginner"),
    ("encoding", "Encoding Categorical Data", "beginner"),
    ("xgboost", "XGBoost", "intermediate"),
    ("lime", "LIME", "advanced"),
    ("shap", "SHAP Values", "advanced"),
    ("model-monitoring", "Model Monitoring", "advanced"),
    ("mlops", "MLOps", "advanced"),
]

# Edges: (src_slug, rel, dst_slug)
RELS = [
    ("linear-regression", "REQUIRES", "ml-foundations"),
    ("logistic-regression", "REQUIRES", "ml-foundations"),
    ("decision-trees", "REQUIRES", "ml-foundations"),
    ("random-forest", "REQUIRES", "decision-trees"),
    ("svm", "REQUIRES", "ml-foundations"),
    ("k-means", "REQUIRES", "ml-foundations"),
    ("pca", "REQUIRES", "dim-reduction"),
    ("overfitting", "RELATES_TO", "bias-variance"),
    ("cross-val", "RELATES_TO", "overfitting"),
    ("grad-descent", "REQUIRES", "ml-foundations"),
    ("cnn", "REQUIRES", "activation-funcs"),
    ("rnn", "REQUIRES", "activation-funcs"),
    ("transformers", "REQUIRES", "embeddings"),
    ("rag", "REQUIRES", "embeddings"),
    ("precision-recall", "RELATES_TO", "roc-auc"),
    ("xgboost", "CONTRASTS_WITH", "random-forest"),
    ("lime", "RELATES_TO", "shap"),
    ("mlops", "RELATES_TO", "model-monitoring"),
]

# Simple keyword mapping for video → concept
KEYWORDS = {
    "linear regression": "linear-regression",
    "logistic regression": "logistic-regression",
    "decision tree": "decision-trees",
    "random forest": "random-forest",
    "support vector": "svm",
    "k-means": "k-means",
    "hierarchical": "hierarchical-clustering",
    "pca": "pca",
    "dimensionality": "dim-reduction",
    "overfitting": "overfitting",
    "bias variance": "bias-variance",
    "cross validation": "cross-val",
    "gradient descent": "grad-descent",
    "activation": "activation-funcs",
    "cnn": "cnn",
    "convolution": "cnn",
    "rnn": "rnn",
    "transformer": "transformers",
    "embedding": "embeddings",
    "roc": "roc-auc",
    "precision": "precision-recall",
    "confusion matrix": "confusion-matrix",
    "feature engineering": "feature-engineering",
    "scaling": "scaling",
    "encoding": "encoding",
    "xgboost": "xgboost",
    "lime": "lime",
    "shap": "shap",
    "mlops": "mlops",
    "monitoring": "model-monitoring",
}

def link_concepts_for_title(title: str) -> List[str]:
    t = (title or "").lower()
    hits = []
    for kw, slug in KEYWORDS.items():
        if kw in t:
            hits.append(slug)
    # dedupe, limit to 2 concepts per video
    return list(dict.fromkeys(hits))[:2]

def connect_to_neo4j():
    """Connect to Neo4j Aura Cloud"""
    try:
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER", "neo4j")
        pwd = os.getenv("NEO4J_PASSWORD")
        
        if not uri or not pwd:
            print("❌ NEO4J_URI or NEO4J_PASSWORD not found in environment")
            return None
        
        # Use bolt+s for direct connection (as we learned from SSL issues)
        if uri.startswith("neo4j+s://"):
            uri = uri.replace("neo4j+s://", "bolt+s://")
        
        print(f"🔄 Connecting to Neo4j: {uri}")
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()
        
        print("✅ Neo4j connection established")
        return driver
        
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {e}")
        return None

def create_knowledge_graph(driver, videos_data):
    """Create comprehensive knowledge graph"""
    
    with driver.session() as sess:
        print("🔧 Creating constraints and indexes...")
        
        # Create constraints
        sess.run("CREATE CONSTRAINT concept_slug_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.slug IS UNIQUE")
        sess.run("CREATE CONSTRAINT video_id_unique IF NOT EXISTS FOR (v:Video) REQUIRE v.video_id IS UNIQUE")
        sess.run("CREATE CONSTRAINT content_id_unique IF NOT EXISTS FOR (ct:Content) REQUIRE ct.id IS UNIQUE")
        
        # Create indexes for performance
        sess.run("CREATE INDEX concept_name_index IF NOT EXISTS FOR (c:Concept) ON (c.name)")
        sess.run("CREATE INDEX video_title_index IF NOT EXISTS FOR (v:Video) ON (v.title)")
        sess.run("CREATE INDEX content_type_index IF NOT EXISTS FOR (ct:Content) ON (ct.type)")
        
        print("✅ Constraints and indexes created")
        
        # Clear existing data
        print("🧹 Clearing existing knowledge graph...")
        sess.run("MATCH (n) DETACH DELETE n")
        
        # Create concepts
        print(f"📚 Creating {len(CONCEPTS)} ML concepts...")
        for slug, name, level in CONCEPTS:
            sess.run(
                "CREATE (c:Concept {slug:$slug, name:$name, level:$level})",
                slug=slug, name=name, level=level
            )

        # Create concept relationships
        print(f"🔗 Creating {len(RELS)} concept relationships...")
        for src, rel, dst in RELS:
            sess.run(
                f"MATCH (a:Concept{{slug:$src}}),(b:Concept{{slug:$dst}}) "
                f"CREATE (a)-[r:{rel}]->(b)",
                src=src, dst=dst
            )

        # Process StatQuest videos and content
        print(f"🎥 Processing {len(videos_data)} StatQuest videos...")
        
        video_count = 0
        content_count = 0
        
        for video in videos_data:
            video_id = video.get("video_id")
            title = video.get("title", "")
            url = video.get("source_url", "")
            content = video.get("content", {})
            
            if not video_id:
                continue
            
            # Create video node
            sess.run(
                "CREATE (v:Video {video_id:$vid, title:$title, url:$url, source:$source})",
                vid=video_id, title=title, url=url, source="statquest"
            )
            video_count += 1
            
            # Create content nodes for each type (summary, analogy, quiz)
            for content_type, content_text in content.items():
                if content_text and content_text.strip():
                    content_id = f"{video_id}_{content_type}"
                    
                    # Create content node
                    sess.run(
                        "CREATE (ct:Content {id:$id, type:$type, text:$text})",
                        id=content_id, type=content_type, text=content_text
                    )
                    
                    # Link video to content
                    sess.run(
                        "MATCH (v:Video {video_id:$vid}), (ct:Content {id:$cid}) "
                        "CREATE (v)-[:HAS_CONTENT]->(ct)",
                        vid=video_id, cid=content_id
                    )
                    content_count += 1
            
            # Link video to concepts based on title
            linked_concepts = link_concepts_for_title(title)
            for concept_slug in linked_concepts:
                sess.run(
                    "MATCH (v:Video {video_id:$vid}), (c:Concept {slug:$slug}) "
                    "CREATE (v)-[:COVERS]->(c)",
                    vid=video_id, slug=concept_slug
                )
        
        print(f"✅ Created {video_count} videos, {content_count} content pieces")
        
        # Get final statistics
        stats = get_graph_stats(sess)
        return stats

def get_graph_stats(session):
    """Get knowledge graph statistics"""
    stats = {}
    
    # Count nodes
    result = session.run("MATCH (c:Concept) RETURN count(c) as count")
    stats['concepts'] = result.single()['count']
    
    result = session.run("MATCH (v:Video) RETURN count(v) as count")
    stats['videos'] = result.single()['count']
    
    result = session.run("MATCH (ct:Content) RETURN count(ct) as count")
    stats['content_pieces'] = result.single()['count']
    
    # Count relationships
    result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
    stats['relationships'] = result.single()['count']
    
    # Count by content type
    result = session.run("MATCH (ct:Content) RETURN ct.type as type, count(ct) as count")
    content_types = {record['type']: record['count'] for record in result}
    stats['content_by_type'] = content_types
    
    return stats

def run():
    print("🚀 Building Comprehensive AI/ML Knowledge Graph")
    print("=" * 60)
    
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos_json", type=str, default="statquest_videos_export.json",
                   help="JSON file with StatQuest videos and content")
    args = ap.parse_args()

    # Connect to Neo4j
    driver = connect_to_neo4j()
    if not driver:
        return
    
    # Load videos data
    if not os.path.exists(args.videos_json):
        print(f"❌ Videos JSON file not found: {args.videos_json}")
        return
    
    print(f"📁 Loading data from: {args.videos_json}")
    with open(args.videos_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    videos_data = data.get('videos', [])
    print(f"📊 Loaded {len(videos_data)} videos with content")
    
    # Build knowledge graph
    try:
        stats = create_knowledge_graph(driver, videos_data)
        
        print("\n🎉 Knowledge Graph Built Successfully!")
        print("=" * 50)
        print(f"📚 Concepts: {stats['concepts']}")
        print(f"🎥 Videos: {stats['videos']}")
        print(f"📝 Content Pieces: {stats['content_pieces']}")
        print(f"🔗 Total Relationships: {stats['relationships']}")
        
        print("\n📊 Content Breakdown:")
        for content_type, count in stats['content_by_type'].items():
            print(f"   - {content_type}: {count}")
        
        print("\n💡 Next Steps:")
        print("   1. Open Neo4j Browser to explore the graph")
        print("   2. Query relationships between concepts")
        print("   3. Find videos covering specific topics")
        print("   4. Use for intelligent recommendations")
        
    except Exception as e:
        print(f"❌ Error building knowledge graph: {e}")
    finally:
        driver.close()
        print("\n🔌 Neo4j connection closed")

if __name__ == "__main__":
    run()
