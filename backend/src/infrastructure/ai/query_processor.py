"""
Advanced Query Processing for RAG Retrieval System
Handles query preprocessing, enhancement, and optimization for document retrieval.
"""

import re
import asyncio
from typing import List, Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import logging

from ...shared.exceptions import ValidationError, ProcessingError

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Types of query intents for different processing strategies"""
    FACTUAL = "factual"           # Direct factual questions
    ANALYTICAL = "analytical"      # Analysis and comparison requests  
    PROCEDURAL = "procedural"     # How-to and step-by-step questions
    EXPLORATORY = "exploratory"   # Open-ended exploration
    CLARIFICATION = "clarification" # Follow-up questions


@dataclass
class ProcessedQuery:
    """Processed query with enhanced metadata for retrieval"""
    original_query: str
    processed_query: str
    intent: QueryIntent
    keywords: List[str]
    semantic_variants: List[str] = field(default_factory=list)
    context_keywords: List[str] = field(default_factory=list)
    relevance_boost: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Message:
    """Chat message for conversation context"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    message_id: Optional[str] = None


class QueryProcessor:
    """Advanced query processor for RAG retrieval enhancement"""
    
    def __init__(self):
        # Common question patterns for intent detection
        self.intent_patterns = {
            QueryIntent.FACTUAL: [
                r'\b(what is|what are|define|definition|meaning of)\b',
                r'\b(who is|who are|when is|when was|where is|where are)\b',
                r'\b(how much|how many|which)\b'
            ],
            QueryIntent.ANALYTICAL: [
                r'\b(compare|contrast|difference|similar|analyze|analysis)\b',
                r'\b(advantage|disadvantage|pros|cons|versus|vs)\b',
                r'\b(impact|effect|influence|consequence|result)\b'
            ],
            QueryIntent.PROCEDURAL: [
                r'\b(how to|how do|how can|step|steps|process|procedure)\b',
                r'\b(install|setup|configure|create|build|implement)\b',
                r'\b(tutorial|guide|instructions|method|way)\b'
            ],
            QueryIntent.EXPLORATORY: [
                r'\b(explore|investigate|discover|learn about|tell me about)\b',
                r'\b(overview|summary|introduction|explain)\b',
                r'\b(possibilities|options|alternatives|approaches)\b'
            ],
            QueryIntent.CLARIFICATION: [
                r'\b(clarify|explain more|elaborate|expand on|details)\b',
                r'\b(what do you mean|can you explain|more about)\b',
                r'^(why|how|what)(?=.*previous|earlier|above|mentioned)\b'
            ]
        }
        
        # Keywords that boost document relevance
        self.technical_indicators = [
            'api', 'database', 'authentication', 'security', 'configuration',
            'implementation', 'architecture', 'design', 'deployment', 'testing'
        ]
    
    async def process_query(self, query: str, user_id: int) -> ProcessedQuery:
        """
        Process a user query for optimized document retrieval
        
        Args:
            query: The original user query
            user_id: User ID for personalization
            
        Returns:
            ProcessedQuery with enhanced metadata
        """
        
        if not query or not query.strip():
            raise ValidationError("Query cannot be empty")
        
        original_query = query.strip()
        
        try:
            # Basic query cleaning and normalization
            processed_query = await self._normalize_query(original_query)
            
            # Extract intent from query patterns
            intent = await self._extract_query_intent(processed_query)
            
            # Extract keywords and key phrases
            keywords = await self._extract_keywords(processed_query)
            
            # Generate semantic variants for broader matching
            semantic_variants = await self._generate_semantic_variants(processed_query, intent)
            
            # Calculate relevance boosters
            relevance_boost = await self._calculate_relevance_boosters(processed_query, keywords)
            
            processed = ProcessedQuery(
                original_query=original_query,
                processed_query=processed_query,
                intent=intent,
                keywords=keywords,
                semantic_variants=semantic_variants,
                relevance_boost=relevance_boost
            )
            
            logger.info(f"Processed query: {original_query[:50]}... -> Intent: {intent.value}")
            
            return processed
            
        except Exception as e:
            logger.error(f"Query processing failed for user {user_id}: {str(e)}")
            raise ProcessingError(f"Failed to process query: {str(e)}")
    
    async def enhance_query_context(self, query: str, chat_history: List[Message]) -> str:
        """
        Enhance query with conversational context from chat history
        
        Args:
            query: Current user query
            chat_history: Previous messages in conversation
            
        Returns:
            Enhanced query with contextual information
        """
        
        if not chat_history:
            return query
        
        try:
            # Get recent context (last 3 messages)
            recent_messages = chat_history[-6:] if len(chat_history) > 6 else chat_history
            
            # Extract context keywords from recent conversation
            context_keywords = []
            for message in recent_messages:
                if message.role == 'user':
                    msg_keywords = await self._extract_keywords(message.content)
                    context_keywords.extend(msg_keywords[:3])  # Top 3 keywords per message
            
            # Remove duplicates and limit context
            unique_context = list(dict.fromkeys(context_keywords))[:5]
            
            # Check for reference patterns in current query
            reference_patterns = [
                r'\b(this|that|it|they|them)\b',
                r'\b(above|previous|earlier|mentioned)\b',
                r'\b(same|similar|like that)\b'
            ]
            
            has_references = any(re.search(pattern, query.lower()) for pattern in reference_patterns)
            
            if has_references and unique_context:
                # Enhance query with context
                context_str = " ".join(unique_context)
                enhanced_query = f"{query} [Context: {context_str}]"
                
                logger.debug(f"Enhanced query with context: {query} -> {enhanced_query}")
                return enhanced_query
            
            return query
            
        except Exception as e:
            logger.warning(f"Context enhancement failed: {str(e)}")
            return query  # Return original query on failure
    
    async def _normalize_query(self, query: str) -> str:
        """Normalize query text for better processing"""
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', query).strip()
        
        # Expand common contractions
        contractions = {
            "can't": "cannot",
            "won't": "will not", 
            "don't": "do not",
            "didn't": "did not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "wouldn't": "would not",
            "shouldn't": "should not",
            "couldn't": "could not"
        }
        
        for contraction, expansion in contractions.items():
            normalized = normalized.replace(contraction, expansion)
        
        return normalized
    
    async def _extract_query_intent(self, query: str) -> QueryIntent:
        """Extract the primary intent from the query"""
        
        query_lower = query.lower()
        
        # Score each intent based on pattern matches
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower))
                score += matches
            intent_scores[intent] = score
        
        # Return intent with highest score, default to exploratory
        if intent_scores and max(intent_scores.values()) > 0:
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        
        return QueryIntent.EXPLORATORY  # Default intent
    
    async def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        
        # Simple keyword extraction (can be enhanced with NLP libraries)
        query_lower = query.lower()
        
        # Remove common stop words
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with', 'you', 'your', 'this', 'can',
            'could', 'should', 'would', 'do', 'does', 'did', 'have', 'had', 'me', 'my'
        }
        
        # Extract words (alphanumeric, minimum 3 characters)
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]{2,}\b', query_lower)
        
        # Filter out stop words and get unique keywords
        keywords = []
        for word in words:
            if word not in stop_words and len(word) >= 3:
                keywords.append(word)
        
        # Remove duplicates while preserving order
        unique_keywords = list(dict.fromkeys(keywords))
        
        # Limit to most relevant keywords
        return unique_keywords[:8]
    
    async def _generate_semantic_variants(self, query: str, intent: QueryIntent) -> List[str]:
        """Generate semantic variants of the query for broader matching"""
        
        variants = []
        
        # Intent-specific query variants
        if intent == QueryIntent.PROCEDURAL:
            # For how-to questions, add method/process variants
            if "how to" in query.lower():
                base = query.lower().replace("how to", "").strip()
                variants.extend([
                    f"method to {base}",
                    f"process of {base}",
                    f"steps for {base}",
                    f"procedure to {base}"
                ])
        
        elif intent == QueryIntent.FACTUAL:
            # For what/who questions, add definition variants
            if query.lower().startswith(("what is", "what are")):
                base = query[7:].strip() if query.lower().startswith("what is") else query[8:].strip()
                variants.extend([
                    f"definition of {base}",
                    f"meaning of {base}",
                    f"{base} explained"
                ])
        
        elif intent == QueryIntent.ANALYTICAL:
            # For comparison questions, add analysis variants
            if any(word in query.lower() for word in ["compare", "difference", "versus"]):
                variants.extend([
                    query.replace("compare", "analyze"),
                    query.replace("difference", "comparison"),
                    query.replace("versus", "compared to")
                ])
        
        # Limit variants to avoid overwhelming the search
        return variants[:3]
    
    async def _calculate_relevance_boosters(self, query: str, keywords: List[str]) -> Dict[str, float]:
        """Calculate relevance boost factors for different document types"""
        
        boost_factors = {}
        query_lower = query.lower()
        
        # Technical content boost
        tech_score = sum(1 for indicator in self.technical_indicators if indicator in query_lower)
        if tech_score > 0:
            boost_factors['technical_documents'] = min(1.5, 1.0 + tech_score * 0.1)
        
        # API documentation boost
        if any(term in query_lower for term in ['api', 'endpoint', 'request', 'response']):
            boost_factors['api_documentation'] = 1.3
        
        # Configuration boost
        if any(term in query_lower for term in ['config', 'setup', 'install', 'configure']):
            boost_factors['configuration_guides'] = 1.2
        
        # Recent documents boost (prefer newer content for current questions)
        if any(term in query_lower for term in ['latest', 'new', 'current', 'recent', 'updated']):
            boost_factors['recent_documents'] = 1.2
        
        return boost_factors