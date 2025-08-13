"""
RAG (Retrieval-Augmented Generation) System using Milvus
This module handles vector storage, retrieval, and reranking for ML concepts
"""

import os
import json
import openai
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import numpy as np
from sentence_transformers import SentenceTransformer
from ml_concepts_data import ML_CONCEPTS_DATABASE
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RAGSystem:
    def __init__(self):
        """Initialize the RAG system with Milvus and OpenAI"""
        self.openai_client = None
        self.milvus_connection = None
        self.collection = None
        self.sentence_transformer = None
        self.collection_name = "ml_concepts"
        self.dimension = 384  # sentence-transformers/all-MiniLM-L6-v2 dimension
        
        # Initialize components
        self._init_openai()
        self._init_sentence_transformer()  # Initialize before Milvus to avoid population issues
        self._init_milvus()
        
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("⚠️ OpenAI API key not found in environment variables")
                return
            
            self.openai_client = openai.OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing OpenAI: {e}")
    
    def _init_sentence_transformer(self):
        """Initialize sentence transformer for embeddings"""
        try:
            # Use a lightweight model that works well for concept similarity
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Sentence transformer initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing sentence transformer: {e}")
    
    def _init_milvus(self):
        """Initialize Milvus connection and collection"""
        try:
            # Check for Zilliz Cloud configuration first
            milvus_uri = os.getenv('MILVUS_URI')
            milvus_token = os.getenv('MILVUS_TOKEN')
            
            if milvus_uri and milvus_token:
                # Connect to Zilliz Cloud (managed Milvus)
                connections.connect(
                    alias="default",
                    uri=milvus_uri,
                    token=milvus_token
                )
                self.milvus_connection = True
                print(f"✅ Connected to Zilliz Cloud: {milvus_uri}")
                
            else:
                # Fallback to local Milvus (if URI/token not provided)
                milvus_host = os.getenv('MILVUS_HOST', 'localhost')
                milvus_port = os.getenv('MILVUS_PORT', '19530')
                
                connections.connect(
                    alias="default",
                    host=milvus_host,
                    port=milvus_port
                )
                self.milvus_connection = True
                print(f"✅ Connected to local Milvus at {milvus_host}:{milvus_port}")
            
            # Create or load collection
            self._setup_collection()
            
        except Exception as e:
            print(f"❌ Error connecting to Milvus: {e}")
            if milvus_uri and milvus_token:
                print("💡 Check your MILVUS_URI and MILVUS_TOKEN in .env file")
            else:
                print("💡 Add MILVUS_URI and MILVUS_TOKEN to .env for Zilliz Cloud, or MILVUS_HOST/MILVUS_PORT for local")
    
    def _setup_collection(self):
        """Create or load the ML concepts collection"""
        try:
            # Check if collection exists
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                
                # Verify it has data
                if self.collection.num_entities > 0:
                    print(f"✅ Loaded existing collection: {self.collection_name} ({self.collection.num_entities} concepts)")
                    return
                else:
                    print(f"⚠️ Collection exists but is empty, populating...")
            else:
                # Create new collection
                print(f"🔄 Creating new collection: {self.collection_name}")
                self._create_collection_schema()
            
            # Populate with ML concepts (only if empty or new)
            self._populate_collection()
            
        except Exception as e:
            print(f"❌ Error setting up collection: {e}")
    
    def _create_collection_schema(self):
        """Create the collection schema and collection"""
        # Define collection schema
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="concept", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="definition", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="child_analogy", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="real_world_example", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="difficulty", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="keywords", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension)
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="ML concepts with child-friendly analogies for RAG system"
        )
        
        # Create collection
        self.collection = Collection(
            name=self.collection_name,
            schema=schema,
            using='default'
        )
        
        print(f"✅ Created new collection: {self.collection_name}")
    
    def _populate_collection(self):
        """Populate the collection with ML concepts and their embeddings"""
        if not self.sentence_transformer:
            print("❌ Sentence transformer not available for embedding generation")
            return
        
        try:
            print("🔄 Generating embeddings for ML concepts...")
            print("⏱️ This may take a few minutes on first run...")
            
            # Prepare data for insertion
            concepts = []
            categories = []
            definitions = []
            analogies = []
            examples = []
            difficulties = []
            keywords_list = []
            embeddings = []
            
            # Generate embeddings for each concept
            total_concepts = len(ML_CONCEPTS_DATABASE)
            for i, concept_data in enumerate(ML_CONCEPTS_DATABASE, 1):
                # Combine text for embedding (concept + definition + analogy for better semantic search)
                combined_text = f"{concept_data['concept']} {concept_data['definition']} {concept_data['child_analogy']}"
                
                # Generate embedding
                embedding = self.sentence_transformer.encode(combined_text, normalize_embeddings=True)
                
                concepts.append(concept_data['concept'])
                categories.append(concept_data['category'])
                definitions.append(concept_data['definition'])
                analogies.append(concept_data['child_analogy'])
                examples.append(concept_data['real_world_example'])
                difficulties.append(concept_data['difficulty'])
                keywords_list.append(', '.join(concept_data['keywords']))
                embeddings.append(embedding.tolist())
                
                # Progress indicator
                if i % 5 == 0 or i == total_concepts:
                    print(f"📊 Progress: {i}/{total_concepts} concepts processed")
            
            # Insert data into collection
            data = [
                concepts,
                categories, 
                definitions,
                analogies,
                examples,
                difficulties,
                keywords_list,
                embeddings
            ]
            
            print("💾 Inserting data into Milvus collection...")
            insert_result = self.collection.insert(data)
            print(f"📊 Insert result: {len(insert_result.primary_keys)} records inserted")
            
            # Force flush to ensure data is persisted
            print("💾 Flushing data to storage...")
            self.collection.flush()
            
            # Wait for data to be persisted
            import time
            print("⏳ Waiting for data persistence...")
            time.sleep(3)
            
            # Check entity count after flush
            entity_count_after_insert = self.collection.num_entities
            print(f"📊 Entities after flush: {entity_count_after_insert}")
            
            # Build index for efficient similarity search
            print("🔍 Building search index...")
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            
            try:
                # Check if index already exists
                indexes = self.collection.indexes
                if not indexes:
                    self.collection.create_index(
                        field_name="embedding",
                        index_params=index_params
                    )
                    print("✅ Search index created successfully")
                else:
                    print("✅ Search index already exists")
                
                # Wait for index to be ready
                print("⏳ Waiting for index to be ready...")
                time.sleep(5)  # Longer wait for index
                
                # Load collection into memory
                print("📚 Loading collection into memory...")
                self.collection.load()
                
                # Wait for loading to complete
                print("⏳ Waiting for collection to load...")
                time.sleep(3)
                
                # Verify collection is loaded - check multiple times
                print("🔍 Verifying collection status...")
                for attempt in range(3):
                    entity_count = self.collection.num_entities
                    print(f"📊 Attempt {attempt + 1}: {entity_count} entities")
                    if entity_count > 0:
                        break
                    time.sleep(2)
                
                if entity_count > 0:
                    print(f"✅ Collection successfully loaded with {entity_count} entities")
                else:
                    print("⚠️ Collection shows 0 entities - may be a timing issue")
                    print("🔄 Trying to reload collection...")
                    self.collection.load()
                    time.sleep(5)
                    final_count = self.collection.num_entities
                    print(f"📊 Final entity count: {final_count}")
                
            except Exception as index_error:
                print(f"⚠️ Index creation warning: {index_error}")
                # Try to load without index for basic functionality
                try:
                    self.collection.load()
                    print("✅ Collection loaded without index (degraded search performance)")
                except Exception as load_error:
                    print(f"❌ Failed to load collection: {load_error}")
                    raise
            
            print(f"✅ Successfully populated collection with {len(ML_CONCEPTS_DATABASE)} ML concepts")
            print("🎉 RAG system is ready for intelligent ML tutoring!")
            
        except Exception as e:
            print(f"❌ Error populating collection: {e}")
    
    def force_repopulate(self):
        """Force repopulation of the collection (for admin use)"""
        try:
            if self.collection and utility.has_collection(self.collection_name):
                # Drop existing collection
                utility.drop_collection(self.collection_name)
                print(f"🗑️ Dropped existing collection: {self.collection_name}")
            
            # Recreate and populate
            print(f"🔄 Creating new collection: {self.collection_name}")
            self._create_collection_schema()
            self._populate_collection()
            
        except Exception as e:
            print(f"❌ Error in force repopulation: {e}")
            raise
    
    def populate_if_empty(self):
        """Populate collection if it's empty (for scripts)"""
        try:
            if not self.collection:
                print("❌ No collection initialized")
                return False
            
            entity_count = self.collection.num_entities
            if entity_count == 0:
                print("🔄 Collection is empty, starting population...")
                self._populate_collection()
                return True
            else:
                print(f"✅ Collection already has {entity_count} concepts")
                return True
                
        except Exception as e:
            print(f"❌ Error checking/populating collection: {e}")
            return False
    
    def get_all_concepts_summary(self) -> Dict[str, List[Dict]]:
        """Retrieve all concepts from Milvus and group by category"""
        try:
            if not self.collection:
                return {}
            
            # Query all data from collection
            results = self.collection.query(
                expr="id >= 0",  # Get all records
                output_fields=["concept", "category", "difficulty", "definition"]
            )
            
            if not results:
                return {}
            
            # Group by category
            categories = {}
            for result in results:
                category = result.get('category', 'Unknown')
                concept_info = {
                    'name': result.get('concept', 'Unknown'),
                    'difficulty': result.get('difficulty', 'unknown'),
                    'definition': result.get('definition', '')[:100] + '...' if len(result.get('definition', '')) > 100 else result.get('definition', '')
                }
                
                if category not in categories:
                    categories[category] = []
                categories[category].append(concept_info)
            
            # Sort categories and concepts within each category
            sorted_categories = {}
            for category in sorted(categories.keys()):
                sorted_categories[category] = sorted(categories[category], key=lambda x: x['name'])
            
            return sorted_categories
            
        except Exception as e:
            print(f"❌ Error retrieving concepts summary: {e}")
            return {}
    
    def search_concepts(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant ML concepts using vector similarity
        
        Args:
            query: User's question or topic
            top_k: Number of top results to return
            
        Returns:
            List of relevant concept dictionaries
        """
        if not self.sentence_transformer or not self.collection:
            print("❌ RAG system not properly initialized")
            return []
        
        try:
            # Generate embedding for the query
            query_embedding = self.sentence_transformer.encode(query, normalize_embeddings=True)
            
            # Search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # Perform similarity search
            results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["concept", "category", "definition", "child_analogy", "real_world_example", "difficulty", "keywords"]
            )
            
            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    concept_data = {
                        "concept": hit.entity.get("concept"),
                        "category": hit.entity.get("category"),
                        "definition": hit.entity.get("definition"),
                        "child_analogy": hit.entity.get("child_analogy"),
                        "real_world_example": hit.entity.get("real_world_example"),
                        "difficulty": hit.entity.get("difficulty"),
                        "keywords": hit.entity.get("keywords"),
                        "similarity_score": hit.score
                    }
                    formatted_results.append(concept_data)
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Error searching concepts: {e}")
            return []
    
    def is_ml_ai_related_question(self, question: str) -> bool:
        """
        Pre-screen questions to determine if they're ML/AI related
        Returns True if question is appropriate for ML/AI tutor
        """
        # Convert question to lowercase for matching
        question_lower = question.lower().strip()
        
        # CONVERSATION CONTINUITY - Allow common follow-up responses
        conversation_continuations = [
            'yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'continue', 'go ahead',
            'tell me more', 'more', 'next', 'please', 'that sounds good',
            'i want to learn', 'teach me', 'can you explain', 'show me',
            'what about', 'how about', 'and then', 'what happens next',
            'i don\'t understand', 'can you simplify', 'make it simpler',
            'give me an example', 'example', 'for instance', 'like what',
            'why', 'how', 'when', 'where', 'what'
        ]
        
        # Check for conversation continuations first
        for continuation in conversation_continuations:
            if question_lower == continuation or question_lower.startswith(continuation + ' '):
                return True
        
        # ML/AI related keywords and concepts
        ml_ai_keywords = [
            # Core ML/AI terms
            'machine learning', 'ml', 'artificial intelligence', 'ai', 'deep learning',
            'neural network', 'algorithm', 'model', 'data science', 'prediction',
            'classification', 'regression', 'clustering', 'supervised', 'unsupervised',
            'reinforcement learning', 'natural language processing', 'nlp', 'computer vision',
            'feature', 'training', 'dataset', 'overfitting', 'accuracy', 'precision',
            
            # Technical terms
            'gradient descent', 'backpropagation', 'embedding', 'vector', 'transformer',
            'cnn', 'rnn', 'lstm', 'gpt', 'bert', 'attention', 'convolution',
            'hyperparameter', 'optimization', 'loss function', 'activation',
            
            # Applications and tools
            'chatgpt', 'generative ai', 'llm', 'large language model', 'tensorflow',
            'pytorch', 'scikit-learn', 'pandas', 'numpy', 'jupyter', 'python for ml',
            'data preprocessing', 'feature engineering', 'model deployment',
            
            # Concepts from our database
            'neural', 'learning', 'training data', 'bias', 'variance', 'cross-validation',
            'ensemble', 'random forest', 'support vector', 'decision tree', 'k-means',
            'dimensionality reduction', 'pca', 'recommendation system', 'anomaly detection'
        ]
        
        # Check for ML/AI keywords
        for keyword in ml_ai_keywords:
            if keyword in question_lower:
                return True
        
        # Check for question patterns that might be ML/AI related
        ml_question_patterns = [
            'how does', 'what is', 'explain', 'learn', 'understand', 'teach me',
            'difference between', 'types of', 'examples of', 'applications of',
            'how to', 'why do', 'when to use', 'best practices', 'getting started'
        ]
        
        # If question contains learning-related patterns and no obvious non-ML topics, check more carefully
        contains_learning_pattern = any(pattern in question_lower for pattern in ml_question_patterns)
        
        # Topics that are definitely NOT ML/AI education
        non_ml_topics = [
            'weather', 'cooking', 'recipe', 'sports', 'politics', 'religion',
            'medical', 'health', 'disease', 'symptom', 'legal', 'law', 'lawyer',
            'financial', 'investment', 'stock', 'money', 'personal', 'relationship',
            'dating', 'marriage', 'celebrity', 'gossip', 'news', 'current events',
            'travel', 'vacation', 'restaurant', 'movie', 'music', 'entertainment'
        ]
        
        # If contains non-ML topics, definitely not ML/AI related
        for topic in non_ml_topics:
            if topic in question_lower:
                return False
        
        # If contains learning pattern but no clear ML keywords, be more permissive
        # This catches questions like "how does learning work?" which could be about ML
        if contains_learning_pattern:
            return True
        
        # Short questions (1-3 words) are likely conversation continuations
        # BUT only if they don't contain obvious non-ML topics
        word_count = len(question_lower.split())
        if word_count <= 3:
            # Double-check that short questions aren't obviously non-ML
            for topic in non_ml_topics:
                if topic in question_lower:
                    return False
            return True
        
        # Default to False for safety
        return False
    
    def generate_response(self, user_question: str, user_profile: Dict[str, Any] = None, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Generate a response using RAG: retrieve relevant concepts and generate answer
        
        Args:
            user_question: The user's question
            user_profile: User's learning profile for personalization (includes user_age)
            conversation_history: Previous messages for context
            
        Returns:
            Generated response string
        """
        if not self.openai_client:
            return "I'm sorry, I can't generate responses right now. The OpenAI connection isn't available."
        
        # Step 0: Pre-screen question for ML/AI relevance
        if not self.is_ml_ai_related_question(user_question):
            age_group = user_profile.get('age_group', 'unknown') if user_profile else 'unknown'
            
            if age_group == 'child':
                return "Hi there! I'm your AI and Machine Learning tutor! 🤖 I can only help you learn about artificial intelligence and machine learning. These are super cool topics where we teach computers to be smart! What would you like to learn about AI or machine learning? Maybe how computers learn to recognize pictures or how they understand what we say?"
            elif age_group == 'teenager':
                return "Hey! I'm an AI/ML education tutor and I focus exclusively on teaching artificial intelligence and machine learning concepts. 🧠 I can't help with other topics, but I'd love to explore some fascinating AI concepts with you! Want to learn how recommendation algorithms work on social media, or how AI creates art and music?"
            else:
                return "I'm an AI/ML education tutor and can only help with Machine Learning and Artificial Intelligence topics. Let's explore some fascinating ML concepts instead! What would you like to learn about AI or machine learning? I can explain everything from basic algorithms to advanced deep learning techniques."
        
        try:
            # Step 1: Retrieve relevant concepts
            relevant_concepts = self.search_concepts(user_question, top_k=3)
            
            if not relevant_concepts:
                return "I couldn't find specific information about that topic. Could you try rephrasing your question or asking about ML concepts like supervised learning, neural networks, or data preprocessing?"
            
            # Step 2: Build conversation context
            conversation_context = ""
            if conversation_history:
                recent_messages = conversation_history[-4:]  # Last 4 messages for context
                conversation_context = "\n\nRecent conversation:\n"
                for msg in recent_messages:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if role == 'user':
                        conversation_context += f"Student: {content}\n"
                    elif role == 'assistant':
                        conversation_context += f"Tutor: {content[:200]}...\n"  # Truncate long responses
            
            # Step 3: Build context from retrieved concepts
            context = "Here are some relevant ML concepts that might help answer your question:\n\n"
            
            for i, concept in enumerate(relevant_concepts, 1):
                context += f"{i}. **{concept['concept']}** ({concept['category']})\n"
                context += f"   Definition: {concept['definition']}\n"
                context += f"   Child-friendly explanation: {concept['child_analogy']}\n"
                context += f"   Real example: {concept['real_world_example']}\n\n"
            
            # Step 4: Personalize based on user profile
            user_context = ""
            if user_profile:
                study_level = user_profile.get('study_level', 'beginner')
                interests = user_profile.get('topics_of_interest', [])
                learning_style = user_profile.get('preferred_learning_style', 'study only')
                user_age = user_profile.get('user_age', None)
                age_group = user_profile.get('age_group', 'unknown')
                
                user_context = f"""
User Profile:
- Study Level: {study_level}
- User Age: {user_age} years old ({age_group})
- Interests: {', '.join(interests) if interests else 'General ML'}
- Learning Style: {learning_style}
"""
            
            # Step 4: Generate response using OpenAI
            age_guidance = ""
            if user_profile and user_profile.get('user_age'):
                age = user_profile.get('user_age')
                age_group = user_profile.get('age_group', 'unknown')
                
                if age_group == "child":
                    age_guidance = f"The user is {age} years old (child). Use very simple language, fun analogies with toys/games/animals, and keep explanations short and engaging."
                elif age_group == "teenager":
                    age_guidance = f"The user is {age} years old (teenager). Use relatable analogies with social media, gaming, sports, and school experiences. Be encouraging about their learning journey."
                elif age_group == "young_adult":
                    age_guidance = f"The user is {age} years old (young adult). Use practical analogies with college, career, technology they use daily. Focus on real-world applications."
                else:
                    age_guidance = f"The user is {age} years old ({age_group}). Adjust complexity and examples accordingly."
            
            system_prompt = f"""You are an AI ML Education Tutor - a specialized, safe, and focused educational assistant dedicated exclusively to teaching Machine Learning and Artificial Intelligence concepts to students of all ages.

{user_context}

{age_guidance}

🎯 CORE MISSION: Make AI/ML education accessible, safe, and high-quality for everyone

🔄 CONVERSATION CONTINUITY RULES:
1. If user says "yes", "tell me more", "continue", etc., CONTINUE the educational topic from previous context
2. If user asks simple follow-up questions (why, how, what, etc.), ELABORATE on the current topic
3. NEVER give generic responses like "How can I help you today?" - always provide specific ML/AI educational content
4. For conversation continuations, build upon the previous topic with deeper explanations or related concepts
5. Maintain educational momentum - every response should teach something new about ML/AI

🛡️ STRICT CONTENT GUARDRAILS:
1. ONLY answer questions related to Machine Learning, Artificial Intelligence, Data Science, and related technical concepts
2. For ANY non-ML/AI questions, respond with age-appropriate redirects to ML/AI topics
3. Never provide information on: politics, religion, personal advice, medical diagnosis, legal advice, financial advice, or any non-educational content
4. If asked about harmful uses of AI/ML, redirect to ethical applications and responsible AI practices
5. Always maintain educational focus - even casual conversations should redirect to ML/AI learning

📚 EDUCATIONAL EXCELLENCE STANDARDS:
1. Use the provided ML concept database as your primary knowledge source
2. Provide accurate, age-appropriate explanations using proven analogies
3. Build knowledge progressively - start simple, add complexity gradually
4. Use encouraging, positive language that builds confidence
5. Include real-world applications that inspire interest
6. Always fact-check against the provided concept definitions
7. If uncertain about advanced topics, acknowledge limitations and focus on fundamentals

🎨 AGE-APPROPRIATE TEACHING:
- For children: Use simple analogies with toys, games, animals, everyday objects
- For teenagers: Reference technology they use, games, social media, school projects
- For adults: Focus on practical applications, career relevance, problem-solving

🔄 ENGAGEMENT STRATEGIES:
1. End responses with specific, curiosity-building questions about related ML/AI topics
2. Suggest hands-on activities or thought experiments when appropriate
3. Connect concepts to the user's stated interests when possible
4. Celebrate learning progress and encourage exploration
5. For follow-up questions, provide progressively deeper explanations

⚖️ ETHICAL AI EMPHASIS:
- Always mention responsible AI practices when relevant
- Emphasize positive applications of ML/AI technology
- Discuss fairness, bias prevention, and ethical considerations age-appropriately
- Promote inclusive, beneficial uses of AI technology

🎓 CONTEXT-AWARE RESPONSES:
- For simple "yes/continue" responses: Elaborate on the most recent ML/AI topic discussed
- For "why/how/what" questions: Provide deeper explanations of the current concept
- For completely new questions: Use the concept database to provide comprehensive answers
- Always assume the user wants to LEARN more about ML/AI concepts

Context from our ML concept database:
{context}

{conversation_context}

Current user question: "{user_question}"

IMPORTANT: 
- If this is a continuation (yes, tell me more, etc.), build upon the previous conversation context
- Never give generic greetings. Always provide specific, educational ML/AI content that builds knowledge
- Use the conversation history to provide contextually relevant follow-up information"""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return "I'm having trouble generating a response right now. Please try again or ask about a specific ML concept like 'What is machine learning?' or 'How do neural networks work?'"
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get the status of all RAG system components"""
        status = {
            "milvus_connected": self.milvus_connection is not None,
            "openai_available": self.openai_client is not None,
            "sentence_transformer_loaded": self.sentence_transformer is not None,
            "collection_exists": False,
            "concepts_count": 0
        }
        
        if self.collection:
            try:
                status["collection_exists"] = True
                status["concepts_count"] = self.collection.num_entities
            except:
                pass
        
        return status
    
    def rerank_results(self, query: str, concepts: List[Dict], top_k: int = 3) -> List[Dict]:
        """
        Use OpenAI to rerank search results for better relevance
        
        Args:
            query: User's original question
            concepts: List of concept dictionaries from similarity search
            top_k: Number of top results to return after reranking
            
        Returns:
            Reranked list of concepts
        """
        if not self.openai_client or not concepts:
            return concepts[:top_k]
        
        try:
            # Prepare concepts for reranking
            concept_summaries = []
            for i, concept in enumerate(concepts):
                summary = f"{i+1}. {concept['concept']}: {concept['definition'][:100]}..."
                concept_summaries.append(summary)
            
            rerank_prompt = f"""Given this user question: "{query}"

Rank these ML concepts from most relevant (1) to least relevant based on how well they answer the user's question:

{chr(10).join(concept_summaries)}

Respond with only the numbers in order of relevance, separated by commas (e.g., "3,1,5,2,4"):"""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": rerank_prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            # Parse reranking results
            ranking_text = response.choices[0].message.content.strip()
            rankings = [int(x.strip()) - 1 for x in ranking_text.split(',') if x.strip().isdigit()]
            
            # Reorder concepts based on ranking
            reranked = []
            for rank_idx in rankings[:top_k]:
                if 0 <= rank_idx < len(concepts):
                    reranked.append(concepts[rank_idx])
            
            # Fill remaining slots if needed
            for i, concept in enumerate(concepts):
                if len(reranked) >= top_k:
                    break
                if i not in rankings[:top_k]:
                    reranked.append(concept)
            
            return reranked[:top_k]
            
        except Exception as e:
            print(f"❌ Error in reranking: {e}")
            return concepts[:top_k]

# Global RAG system instance
rag_system = None

def get_rag_system() -> RAGSystem:
    """Get or create the global RAG system instance"""
    global rag_system
    if rag_system is None:
        rag_system = RAGSystem()
    return rag_system
