"""
ML Concepts Database with Child-Friendly Analogies
This file contains ML/AI concepts explained through relatable analogies for beginners
"""

ML_CONCEPTS_DATABASE = [
    # ML Foundations
    {
        "concept": "Machine Learning",
        "category": "ML Foundations",
        "definition": "A way for computers to learn patterns from data without being explicitly programmed for every situation.",
        "child_analogy": "Imagine teaching your little brother to recognize different dog breeds. Instead of telling him every single detail about every breed, you show him hundreds of pictures of dogs with their breed names. After seeing enough examples, he starts recognizing breeds on his own. That's how machine learning works - computers learn from examples!",
        "real_world_example": "Netflix recommending movies you might like based on what you've watched before.",
        "difficulty": "beginner",
        "keywords": ["machine learning", "ML", "artificial intelligence", "pattern recognition", "learning from data"]
    },
    {
        "concept": "Algorithm",
        "category": "ML Foundations", 
        "definition": "A set of rules or instructions that tell a computer how to solve a problem step by step.",
        "child_analogy": "An algorithm is like a recipe for baking cookies. The recipe tells you exactly what ingredients to use and what steps to follow: mix flour and sugar, add eggs, bake for 10 minutes. Just like how you follow a recipe to make cookies, computers follow algorithms to solve problems!",
        "real_world_example": "GPS navigation giving you turn-by-turn directions to reach your destination.",
        "difficulty": "beginner",
        "keywords": ["algorithm", "instructions", "steps", "rules", "problem solving"]
    },
    {
        "concept": "Training Data",
        "category": "ML Foundations",
        "definition": "The collection of examples used to teach a machine learning model how to make predictions.",
        "child_analogy": "Think of training data like a big stack of flashcards. If you want to learn Spanish, you'd use flashcards with English words on one side and Spanish on the other. You'd practice with hundreds of these cards until you learn the patterns. Training data is like those flashcards for computers - lots of examples they study to learn patterns!",
        "real_world_example": "Thousands of photos of cats and dogs used to train a computer to tell them apart.",
        "difficulty": "beginner",
        "keywords": ["training data", "dataset", "examples", "learning", "patterns"]
    },

    # Supervised Learning
    {
        "concept": "Supervised Learning",
        "category": "Supervised Learning",
        "definition": "Learning with a teacher - the computer learns from examples where we already know the correct answer.",
        "child_analogy": "Imagine learning math with a teacher who gives you practice problems with the answers in the back of the book. You solve '2 + 3 = ?' and check that the answer is 5. After doing hundreds of these problems, you learn how to add. Supervised learning is the same - we give computers problems with the right answers so they can learn!",
        "real_world_example": "Email spam detection - showing the computer thousands of emails labeled as 'spam' or 'not spam' so it learns to identify spam.",
        "difficulty": "beginner",
        "keywords": ["supervised learning", "teacher", "labeled data", "examples", "correct answers"]
    },
    {
        "concept": "Classification",
        "category": "Supervised Learning",
        "definition": "Sorting things into different categories or groups based on their features.",
        "child_analogy": "Think about sorting your toy box. You put all the Lego blocks in one bin, all the action figures in another, and all the puzzles in a third bin. You look at each toy and decide which group it belongs to based on what it looks like. Classification works the same way - computers look at features of things and sort them into groups!",
        "real_world_example": "A camera app that automatically sorts your photos into 'people', 'animals', 'food', and 'landscapes'.",
        "difficulty": "beginner",
        "keywords": ["classification", "categories", "sorting", "groups", "labeling"]
    },
    {
        "concept": "Regression",
        "category": "Supervised Learning",
        "definition": "Predicting a number or continuous value rather than just categories.",
        "child_analogy": "Imagine you're trying to guess how tall your classmates will be when they grow up. You look at how tall their parents are, what they eat, how much they exercise. Based on these clues, you try to predict their exact height - like 5 feet 8 inches. That's regression - predicting specific numbers instead of just yes/no or categories!",
        "real_world_example": "Predicting house prices based on size, location, number of bedrooms, and age of the house.",
        "difficulty": "intermediate",
        "keywords": ["regression", "prediction", "numbers", "continuous values", "estimating"]
    },

    # Unsupervised Learning
    {
        "concept": "Unsupervised Learning",
        "category": "Unsupervised Learning",
        "definition": "Learning without a teacher - finding hidden patterns in data when we don't know the right answers.",
        "child_analogy": "Imagine you move to a new school and want to understand the different friend groups, but no one tells you who belongs where. You start noticing patterns: some kids always sit together at lunch, others play the same sports, some wear similar clothes. Without anyone teaching you, you figure out the social groups. That's unsupervised learning - finding patterns without being told what to look for!",
        "real_world_example": "A music app discovering that people who like rock music also tend to like certain indie bands, without being told about music genres.",
        "difficulty": "intermediate",
        "keywords": ["unsupervised learning", "patterns", "hidden", "no teacher", "discovery"]
    },
    {
        "concept": "Clustering",
        "category": "Unsupervised Learning",
        "definition": "Grouping similar things together without knowing the groups ahead of time.",
        "child_analogy": "Imagine you have a huge box of mixed candy and want to organize it, but you don't know what types of candy there are. You start putting similar candies together: all the chocolate bars in one pile, all the gummy candies in another, all the hard candies in a third pile. You're clustering - grouping things that are alike without anyone telling you what the groups should be!",
        "real_world_example": "A store analyzing customer buying patterns to discover different types of shoppers (budget shoppers, luxury buyers, health-conscious customers).",
        "difficulty": "intermediate",
        "keywords": ["clustering", "grouping", "similar", "organize", "patterns"]
    },

    # Deep Learning
    {
        "concept": "Neural Network",
        "category": "Deep Learning Basics",
        "definition": "A computer system inspired by how the brain works, with layers of connected nodes that process information.",
        "child_analogy": "Think of a neural network like a team of friends passing along a secret message. The first friend hears the message and whispers it to three other friends, each adding their own understanding. Those friends pass it to more friends, and so on. By the time the message reaches the end, the team has worked together to understand and improve the message. That's how neural networks work - layers of 'computer friends' working together!",
        "real_world_example": "The technology that recognizes your face in photos and suggests who to tag.",
        "difficulty": "intermediate",
        "keywords": ["neural network", "brain", "layers", "connected", "nodes"]
    },
    {
        "concept": "Deep Learning",
        "category": "Deep Learning Basics",
        "definition": "Machine learning using neural networks with many layers, allowing computers to learn complex patterns.",
        "child_analogy": "Imagine learning to recognize animals. First, you notice simple things like 'has fur' or 'has feathers'. Then you notice more complex things like 'has a long trunk' or 'has black and white stripes'. Finally, you put it all together to recognize 'elephant' or 'zebra'. Deep learning works like this - many layers of learning, starting simple and building up to understand complex things!",
        "real_world_example": "Self-driving cars that can recognize pedestrians, traffic lights, other cars, and road signs all at the same time.",
        "difficulty": "intermediate",
        "keywords": ["deep learning", "neural networks", "layers", "complex patterns", "advanced"]
    },

    # LLM & Generative AI
    {
        "concept": "Large Language Model (LLM)",
        "category": "LLM & Generative AI",
        "definition": "A powerful AI system trained on vast amounts of text to understand and generate human-like language.",
        "child_analogy": "Imagine if someone read every book in the world's biggest library, every newspaper, every website, and remembered all of it. Now they can answer almost any question and write stories, poems, or explanations about anything. An LLM is like that super-reader - it has learned from billions of sentences and can help with language tasks!",
        "real_world_example": "ChatGPT, which can answer questions, write essays, explain concepts, and have conversations.",
        "difficulty": "intermediate",
        "keywords": ["LLM", "language model", "text generation", "conversation", "ChatGPT"]
    },
    {
        "concept": "Generative AI", 
        "category": "LLM & Generative AI",
        "definition": "AI that creates new content like text, images, music, or code based on what it has learned.",
        "child_analogy": "Think of the most creative kid in art class who can draw amazing pictures, write cool stories, and make up songs. But imagine if this kid had seen every painting in every museum, read every book ever written, and heard every song ever made. Generative AI is like this super-creative kid - it can make new things by combining ideas from everything it has learned!",
        "real_world_example": "AI that creates artwork like DALL-E, writes code like GitHub Copilot, or composes music.",
        "difficulty": "intermediate",
        "keywords": ["generative AI", "create", "generate", "content", "creative"]
    },

    # Model Evaluation
    {
        "concept": "Accuracy",
        "category": "Model Evaluation",
        "definition": "How often the AI model gets the right answer out of all its guesses.",
        "child_analogy": "Imagine you're playing a guessing game where you try to guess what's in 100 mystery boxes. If you guess correctly 85 times out of 100, your accuracy is 85%. It's like getting 85 questions right on a 100-question test. Accuracy tells us how good our AI is at making correct predictions!",
        "real_world_example": "A medical AI that correctly identifies diseases in 95% of the cases it examines.",
        "difficulty": "beginner",
        "keywords": ["accuracy", "correct", "performance", "evaluation", "percentage"]
    },
    {
        "concept": "Overfitting",
        "category": "Model Evaluation",
        "definition": "When an AI model memorizes training examples too well and can't handle new, unseen data.",
        "child_analogy": "Imagine studying for a test by memorizing only the practice questions and their exact answers. You ace the practice test, but when the real test has slightly different questions, you fail because you only memorized, you didn't truly understand. Overfitting is when AI does the same thing - it memorizes the training data instead of learning general patterns!",
        "real_world_example": "A photo recognition system that works perfectly on training photos but fails on new photos taken with different cameras or lighting.",
        "difficulty": "intermediate",
        "keywords": ["overfitting", "memorizing", "generalization", "new data", "too specific"]
    },

    # Data Prep & Features
    {
        "concept": "Feature Engineering",
        "category": "Data Prep & Features (EDA)",
        "definition": "Selecting and transforming the most important characteristics of data to help AI learn better.",
        "child_analogy": "Imagine you're a detective trying to solve who ate the last cookie. You collect clues: chocolate on someone's face, crumbs on their shirt, sticky fingers. You realize the chocolate on the face is the most important clue. Feature engineering is like being a detective - choosing which clues (features) are most important and sometimes combining clues to solve the mystery better!",
        "real_world_example": "For predicting house prices, combining 'number of bedrooms' and 'square footage' to create a new feature called 'space per bedroom'.",
        "difficulty": "intermediate",
        "keywords": ["features", "characteristics", "data transformation", "selection", "engineering"]
    },
    {
        "concept": "Data Cleaning",
        "category": "Data Prep & Features (EDA)",
        "definition": "Fixing errors, removing duplicates, and handling missing information in datasets.",
        "child_analogy": "Imagine organizing your messy backpack before school. You throw away broken pencils, remove duplicate homework sheets, and replace missing erasers. You also fix torn notebook pages with tape. Data cleaning is like organizing your backpack - fixing, removing, and replacing things so everything is neat and ready to use!",
        "real_world_example": "Removing typos from a customer database and filling in missing phone numbers.",
        "difficulty": "beginner",
        "keywords": ["data cleaning", "errors", "missing data", "duplicates", "preprocessing"]
    },

    # Practical ML Production
    {
        "concept": "Model Deployment",
        "category": "Practical ML Production",
        "definition": "Taking a trained AI model and making it available for real people to use in real applications.",
        "child_analogy": "Imagine you've practiced a magic trick at home until you're really good at it. Now you want to perform it at the school talent show so everyone can see it. Deployment is like taking your perfected magic trick from your bedroom to the stage where everyone can enjoy it. You're taking your AI model from the computer lab to the real world!",
        "real_world_example": "Putting a trained language translation model into Google Translate so millions of people can use it.",
        "difficulty": "advanced",
        "keywords": ["deployment", "production", "real world", "users", "application"]
    },
    {
        "concept": "Model Monitoring",
        "category": "Practical ML Production", 
        "definition": "Keeping track of how well an AI model performs after it's being used in the real world.",
        "child_analogy": "Imagine you have a pet robot that helps with chores. Every day you check: Is it still cleaning properly? Is it moving slower than usual? Is it making mistakes it didn't make before? Model monitoring is like being a caring robot owner - constantly checking that your AI is healthy and working as expected!",
        "real_world_example": "Monitoring a recommendation system to ensure it's still suggesting relevant products to customers.",
        "difficulty": "advanced",
        "keywords": ["monitoring", "performance", "tracking", "maintenance", "health check"]
    },

    # Interpretability & Ethics
    {
        "concept": "AI Ethics",
        "category": "Interpretability & Ethics",
        "definition": "Ensuring AI systems are fair, safe, and beneficial for everyone while avoiding harm or bias.",
        "child_analogy": "Imagine you're the teacher picking teams for dodgeball. AI ethics is like making sure you pick teams fairly - not always choosing your friends first, making sure everyone gets a turn, and ensuring no one gets hurt or feels left out. It's about being fair and kind when AI makes decisions that affect people's lives!",
        "real_world_example": "Ensuring AI hiring systems don't discriminate against certain groups of people.",
        "difficulty": "intermediate",
        "keywords": ["ethics", "fairness", "bias", "safety", "responsibility"]
    },
    {
        "concept": "Explainable AI (XAI)",
        "category": "Interpretability & Ethics",
        "definition": "Making AI decisions understandable to humans so we know why the AI made a particular choice.",
        "child_analogy": "Imagine your math teacher always shows their work when solving problems on the board. They don't just write '2 + 3 = 5', they explain each step so you understand how they got the answer. Explainable AI is like having an AI teacher that shows its work - it tells us WHY it made a decision, not just WHAT decision it made!",
        "real_world_example": "A medical AI explaining why it thinks a patient might have a certain condition by highlighting which symptoms were most important.",
        "difficulty": "advanced",
        "keywords": ["explainable AI", "interpretability", "transparency", "understanding", "reasoning"]
    },

    # Optimization
    {
        "concept": "Hyperparameter Tuning",
        "category": "Optimization",
        "definition": "Adjusting the settings of a machine learning model to make it perform better.",
        "child_analogy": "Think of learning to ride a bike. You need to adjust the seat height, handlebar position, and tire pressure to ride comfortably and safely. If the seat is too high, you can't reach the pedals. If it's too low, your knees hit the handlebars. Hyperparameter tuning is like adjusting all these bike settings - finding the perfect combination that makes your AI model work its best!",
        "real_world_example": "Adjusting how fast an AI learns and how many examples it looks at once to improve its accuracy.",
        "difficulty": "intermediate",
        "keywords": ["hyperparameters", "tuning", "optimization", "settings", "performance"]
    },
    {
        "concept": "Gradient Descent",
        "category": "Optimization",
        "definition": "A method for finding the best solution by gradually adjusting in the direction that reduces errors.",
        "child_analogy": "Imagine you're blindfolded and trying to find the bottom of a hill. You can feel the slope with your feet - if it's going downward to your left, you take a step left. If it's going down to your right, you step right. You keep taking small steps in the downward direction until you reach the bottom. Gradient descent is like this - the AI takes small steps toward better solutions!",
        "real_world_example": "An AI gradually adjusting its internal settings to make fewer mistakes in recognizing handwritten numbers.",
        "difficulty": "advanced",
        "keywords": ["gradient descent", "optimization", "learning", "adjustment", "improvement"]
    }
]

# Categories for easy filtering
CATEGORIES = [
    "ML Foundations",
    "Supervised Learning", 
    "Unsupervised Learning",
    "Model Evaluation",
    "Data Prep & Features (EDA)",
    "Optimization",
    "Interpretability & Ethics",
    "Deep Learning Basics",
    "LLM & Generative AI",
    "Practical ML Production"
]

def get_concepts_by_category(category: str):
    """Get all concepts for a specific category"""
    return [concept for concept in ML_CONCEPTS_DATABASE if concept["category"] == category]

def get_concepts_by_difficulty(difficulty: str):
    """Get all concepts for a specific difficulty level"""
    return [concept for concept in ML_CONCEPTS_DATABASE if concept["difficulty"] == difficulty]

def search_concepts(query: str):
    """Simple text search through concepts"""
    query_lower = query.lower()
    results = []
    
    for concept in ML_CONCEPTS_DATABASE:
        # Search in concept name, definition, analogy, and keywords
        searchable_text = f"{concept['concept']} {concept['definition']} {concept['child_analogy']} {' '.join(concept['keywords'])}".lower()
        
        if query_lower in searchable_text:
            results.append(concept)
    
    return results
