"""
Context Window Management for RAG System
Handles intelligent context construction, chunk ranking, and token optimization.
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import tiktoken

from ..database.models import DocumentChunk
from .query_processor import ProcessedQuery
from ...shared.exceptions import ProcessingError

logger = logging.getLogger(__name__)


@dataclass
class RankedChunk:
    """Document chunk with relevance scoring"""
    chunk: DocumentChunk
    relevance_score: float
    similarity_score: float
    recency_score: float
    final_score: float
    reasoning: str = ""


@dataclass
class ContextWindow:
    """Optimized context window for LLM processing"""
    context_text: str
    chunks_used: List[RankedChunk]
    total_tokens: int
    truncated: bool
    context_strategy: str
    metadata: Dict = field(default_factory=dict)


class ContextManager:
    """Manages context window construction and optimization for RAG"""
    
    def __init__(self):
        # Model token limits (with safety margins) - Based on your AI config
        self.model_limits = {
            # Google Gemini Models (Primary)
            'gemini-pro': 7500,                    # 8K limit with 500 token safety margin
            'gemini-pro-vision': 7500,            # 8K limit with 500 token safety margin
            'gemini-1.5-pro': 950000,             # 1M limit with 50K safety margin
            'gemini-1.5-flash': 950000,           # 1M limit with 50K safety margin
            'gemini-2.0-flash': 950000,           # 1M limit with 50K safety margin (your default)
            
            # Anthropic Models (Fallback)
            'claude-3-5-sonnet-20241022': 199000, # 200K limit with 1K safety margin
            'claude-3-opus-20240229': 199000,     # 200K limit with 1K safety margin
            'claude-3-5-haiku-20241022': 199000,  # 200K limit with 1K safety margin
        }
        
        # Initialize tokenizer for token counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Scoring weights for chunk ranking
        self.ranking_weights = {
            'similarity': 0.6,      # Vector similarity score
            'relevance': 0.25,      # Query-specific relevance
            'recency': 0.1,         # Document recency
            'length': 0.05          # Chunk completeness
        }
    
    async def build_context_window(
        self, 
        retrieved_chunks: List[DocumentChunk], 
        query: ProcessedQuery,
        max_tokens: int = 4000,
        model_name: str = 'gpt-3.5-turbo'
    ) -> ContextWindow:
        """
        Build optimized context window from retrieved chunks
        
        Args:
            retrieved_chunks: List of document chunks from vector search
            query: Processed query with metadata
            max_tokens: Maximum tokens for context (overrides model default)
            model_name: Target LLM model name
            
        Returns:
            ContextWindow with optimized context and metadata
        """
        
        if not retrieved_chunks:
            return ContextWindow(
                context_text="",
                chunks_used=[],
                total_tokens=0,
                truncated=False,
                context_strategy="empty"
            )
        
        try:
            # Use provided max_tokens or model default (default to gemini-2.0-flash)
            token_limit = min(max_tokens, self.model_limits.get(model_name, 950000))
            
            # Reserve tokens for prompt template and response (larger reservation for Gemini's long context)
            if 'gemini' in model_name and token_limit > 100000:
                # For large context models, reserve more space for comprehensive responses
                available_tokens = max(token_limit - 5000, 1000)
            else:
                # Standard reservation for smaller models
                available_tokens = max(token_limit - 1000, 500)
            
            # Rank chunks by relevance to query
            ranked_chunks = await self.rank_chunks_by_relevance(retrieved_chunks, query)
            
            # Build context using best strategy
            context_window = await self._build_optimal_context(
                ranked_chunks, 
                available_tokens, 
                query
            )
            
            logger.info(f"Built context window: {len(context_window.chunks_used)} chunks, "
                       f"{context_window.total_tokens} tokens, strategy: {context_window.context_strategy}")
            
            return context_window
            
        except Exception as e:
            logger.error(f"Context window construction failed: {str(e)}")
            raise ProcessingError(f"Failed to build context window: {str(e)}")
    
    async def rank_chunks_by_relevance(
        self, 
        chunks: List[DocumentChunk], 
        query: ProcessedQuery
    ) -> List[RankedChunk]:
        """
        Rank document chunks by relevance to the processed query
        
        Args:
            chunks: List of document chunks to rank
            query: Processed query with intent and keywords
            
        Returns:
            List of chunks ranked by final relevance score
        """
        
        ranked_chunks = []
        
        for chunk in chunks:
            # Calculate component scores
            similarity_score = await self._get_similarity_score(chunk)
            relevance_score = await self._calculate_relevance_score(chunk, query)
            recency_score = await self._calculate_recency_score(chunk)
            length_score = await self._calculate_length_score(chunk)
            
            # Calculate weighted final score
            final_score = (
                similarity_score * self.ranking_weights['similarity'] +
                relevance_score * self.ranking_weights['relevance'] +
                recency_score * self.ranking_weights['recency'] +
                length_score * self.ranking_weights['length']
            )
            
            reasoning = await self._generate_ranking_reasoning(
                chunk, similarity_score, relevance_score, recency_score, length_score
            )
            
            ranked_chunk = RankedChunk(
                chunk=chunk,
                relevance_score=relevance_score,
                similarity_score=similarity_score,
                recency_score=recency_score,
                final_score=final_score,
                reasoning=reasoning
            )
            
            ranked_chunks.append(ranked_chunk)
        
        # Sort by final score (descending)
        ranked_chunks.sort(key=lambda x: x.final_score, reverse=True)
        
        logger.debug(f"Ranked {len(ranked_chunks)} chunks, top score: {ranked_chunks[0].final_score:.3f}")
        
        return ranked_chunks
    
    async def optimize_context_for_model(self, context: str, model_name: str) -> str:
        """
        Optimize context formatting for specific model requirements
        
        Args:
            context: Raw context text
            model_name: Target model name
            
        Returns:
            Optimized context text
        """
        
        if not context:
            return context
        
        try:
            # Model-specific optimizations
            if model_name.startswith('claude'):
                # Claude prefers structured context with clear sections
                return await self._format_context_for_claude(context)
            
            elif model_name.startswith('gemini'):
                # Gemini models work well with structured markdown format
                return await self._format_context_for_gemini(context)
            
            else:
                # Generic formatting for other models
                return await self._format_context_generic(context)
                
        except Exception as e:
            logger.warning(f"Context optimization failed for {model_name}: {str(e)}")
            return context  # Return original on failure
    
    async def _build_optimal_context(
        self, 
        ranked_chunks: List[RankedChunk], 
        available_tokens: int,
        query: ProcessedQuery
    ) -> ContextWindow:
        """Build context using optimal strategy based on available tokens and chunks"""
        
        if not ranked_chunks:
            return ContextWindow(
                context_text="",
                chunks_used=[],
                total_tokens=0,
                truncated=False,
                context_strategy="empty"
            )
        
        # Strategy 1: Try to fit top chunks completely
        selected_chunks, total_tokens, truncated = await self._select_chunks_greedy(
            ranked_chunks, available_tokens
        )
        
        if selected_chunks:
            context_text = await self._format_chunks_to_context(selected_chunks)
            
            return ContextWindow(
                context_text=context_text,
                chunks_used=selected_chunks,
                total_tokens=total_tokens,
                truncated=truncated,
                context_strategy="greedy_selection",
                metadata={
                    'avg_score': sum(c.final_score for c in selected_chunks) / len(selected_chunks),
                    'chunk_count': len(selected_chunks),
                    'utilization': total_tokens / available_tokens
                }
            )
        
        # Fallback: Use single best chunk (truncated if necessary)
        best_chunk = ranked_chunks[0]
        context_text = best_chunk.chunk.content
        
        # Truncate if necessary
        chunk_tokens = len(self.tokenizer.encode(context_text))
        if chunk_tokens > available_tokens:
            truncated_text = await self._truncate_text_smartly(context_text, available_tokens)
            chunk_tokens = len(self.tokenizer.encode(truncated_text))
            context_text = truncated_text
            truncated = True
        else:
            truncated = False
        
        return ContextWindow(
            context_text=context_text,
            chunks_used=[best_chunk],
            total_tokens=chunk_tokens,
            truncated=truncated,
            context_strategy="single_chunk_fallback"
        )
    
    async def _select_chunks_greedy(
        self, 
        ranked_chunks: List[RankedChunk], 
        available_tokens: int
    ) -> Tuple[List[RankedChunk], int, bool]:
        """Select chunks using greedy algorithm to maximize context value"""
        
        selected_chunks = []
        total_tokens = 0
        
        for chunk in ranked_chunks:
            # Estimate tokens for this chunk (with formatting overhead)
            chunk_text = f"\n\n## Document: {chunk.chunk.document.filename}\n{chunk.chunk.content}\n"
            chunk_tokens = len(self.tokenizer.encode(chunk_text))
            
            # Check if chunk fits in remaining space
            if total_tokens + chunk_tokens <= available_tokens:
                selected_chunks.append(chunk)
                total_tokens += chunk_tokens
            else:
                # Try to truncate current chunk to fit remaining space
                remaining_tokens = available_tokens - total_tokens
                if remaining_tokens > 200:  # Minimum useful chunk size
                    truncated_content = await self._truncate_text_smartly(
                        chunk.chunk.content, 
                        remaining_tokens - 50  # Account for formatting
                    )
                    
                    # Create truncated chunk
                    truncated_chunk = RankedChunk(
                        chunk=chunk.chunk,
                        relevance_score=chunk.relevance_score,
                        similarity_score=chunk.similarity_score,
                        recency_score=chunk.recency_score,
                        final_score=chunk.final_score * 0.8,  # Penalty for truncation
                        reasoning=chunk.reasoning + " (truncated)"
                    )
                    
                    # Update content temporarily for context building
                    truncated_chunk.chunk.content = truncated_content
                    
                    selected_chunks.append(truncated_chunk)
                    total_tokens = available_tokens
                    return selected_chunks, total_tokens, True
                
                break
        
        return selected_chunks, total_tokens, False
    
    async def _format_chunks_to_context(self, chunks: List[RankedChunk]) -> str:
        """Format selected chunks into coherent context text"""
        
        if not chunks:
            return ""
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            # Add document source and chunk content
            chunk_text = f"""## Source {i}: {chunk.chunk.document.filename}

{chunk.chunk.content.strip()}"""
            
            context_parts.append(chunk_text)
        
        return "\n\n" + "\n\n".join(context_parts) + "\n\n"
    
    async def _get_similarity_score(self, chunk: DocumentChunk) -> float:
        """Get similarity score from chunk (assumed to be set during retrieval)"""
        # In a real implementation, this would come from the vector search results
        # For now, return a placeholder that would be set by the vector store
        return getattr(chunk, 'similarity_score', 0.8)
    
    async def _calculate_relevance_score(self, chunk: DocumentChunk, query: ProcessedQuery) -> float:
        """Calculate relevance score based on query intent and keywords"""
        
        score = 0.5  # Base score
        content_lower = chunk.content.lower()
        
        # Keyword matching bonus
        keyword_matches = sum(1 for keyword in query.keywords if keyword in content_lower)
        if query.keywords:
            keyword_score = keyword_matches / len(query.keywords)
            score += keyword_score * 0.3
        
        # Intent-specific scoring
        if query.intent.value == 'procedural' and any(
            word in content_lower for word in ['step', 'process', 'method', 'procedure']
        ):
            score += 0.15
        
        elif query.intent.value == 'factual' and any(
            word in content_lower for word in ['definition', 'is', 'are', 'means']
        ):
            score += 0.15
        
        elif query.intent.value == 'analytical' and any(
            word in content_lower for word in ['compare', 'analysis', 'advantage', 'difference']
        ):
            score += 0.15
        
        # Document type relevance
        filename = chunk.document.filename.lower()
        if query.intent.value == 'procedural' and any(
            term in filename for term in ['guide', 'tutorial', 'howto', 'setup']
        ):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def _calculate_recency_score(self, chunk: DocumentChunk) -> float:
        """Calculate recency score based on document upload/modification time"""
        
        # Use document upload time or current time as fallback
        doc_time = chunk.document.created_at if hasattr(chunk.document, 'created_at') else datetime.utcnow()
        
        # Calculate days since document was created
        days_old = (datetime.utcnow() - doc_time).days
        
        # Recency score: 1.0 for new documents, decaying over time
        if days_old <= 7:
            return 1.0
        elif days_old <= 30:
            return 0.8
        elif days_old <= 90:
            return 0.6
        else:
            return 0.4
    
    async def _calculate_length_score(self, chunk: DocumentChunk) -> float:
        """Calculate score based on chunk completeness and length"""
        
        content_length = len(chunk.content)
        
        # Prefer chunks with substantial content but not too long
        if 200 <= content_length <= 1000:
            return 1.0
        elif 100 <= content_length < 200:
            return 0.8
        elif 1000 < content_length <= 2000:
            return 0.9
        elif content_length > 2000:
            return 0.7
        else:
            return 0.5  # Very short chunks
    
    async def _generate_ranking_reasoning(
        self, 
        chunk: DocumentChunk, 
        similarity: float, 
        relevance: float, 
        recency: float, 
        length: float
    ) -> str:
        """Generate human-readable reasoning for chunk ranking"""
        
        reasons = []
        
        if similarity > 0.8:
            reasons.append(f"high similarity ({similarity:.2f})")
        elif similarity > 0.6:
            reasons.append(f"good similarity ({similarity:.2f})")
        
        if relevance > 0.7:
            reasons.append("high relevance to query")
        elif relevance > 0.5:
            reasons.append("moderate relevance")
        
        if recency > 0.8:
            reasons.append("recent document")
        
        if length > 0.8:
            reasons.append("good content length")
        
        return "; ".join(reasons) if reasons else "standard scoring"
    
    async def _truncate_text_smartly(self, text: str, max_tokens: int) -> str:
        """Intelligently truncate text while preserving meaning"""
        
        # Encode full text to get token count
        tokens = self.tokenizer.encode(text)
        
        if len(tokens) <= max_tokens:
            return text
        
        # Try to truncate at sentence boundaries
        sentences = text.split('. ')
        truncated_tokens = 0
        truncated_sentences = []
        
        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence + '. '))
            if truncated_tokens + sentence_tokens <= max_tokens - 10:  # Safety margin
                truncated_sentences.append(sentence)
                truncated_tokens += sentence_tokens
            else:
                break
        
        if truncated_sentences:
            result = '. '.join(truncated_sentences) + '.'
            # Add truncation indicator
            result += "\n\n[Content truncated for length...]"
            return result
        
        # Fallback: character truncation
        char_limit = int(max_tokens * 3.5)  # Rough chars per token estimate
        truncated = text[:char_limit]
        return truncated + "\n\n[Content truncated for length...]"
    
    async def _format_context_for_claude(self, context: str) -> str:
        """Format context optimally for Anthropic Claude models"""
        return f"""<context>
{context.strip()}
</context>"""
    
    async def _format_context_for_gemini(self, context: str) -> str:
        """Format context optimally for Google Gemini models"""
        return f"""## Context Information

{context.strip()}

## Instructions
Based on the provided context information above, please answer the user's question accurately and comprehensively. If the context doesn't contain enough information to fully answer the question, please indicate what information is missing."""
    
    async def _format_context_generic(self, context: str) -> str:
        """Generic context formatting"""
        return f"""Relevant Information:

{context.strip()}

Please use this information to answer the user's question:"""