"""
Advanced Prompt Engineering and Template Management for RAG
Handles dynamic prompt generation, context optimization, and response formatting.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging
from datetime import datetime

from .query_processor import ProcessedQuery, QueryIntent, Message
from .context_manager import ContextWindow, RankedChunk
# DocumentChunk will be imported where needed to avoid circular imports

logger = logging.getLogger(__name__)


class PromptScenario(Enum):
    """Different prompt scenarios for various use cases"""
    GENERAL_QA = "general_qa"               # General question answering
    TECHNICAL_DOCS = "technical_docs"       # Technical documentation queries
    PROCEDURAL = "procedural"               # How-to and step-by-step instructions
    ANALYTICAL = "analytical"               # Analysis and comparison requests
    EXPLORATORY = "exploratory"             # Open-ended exploration
    CLARIFICATION = "clarification"         # Follow-up clarifications
    SUMMARIZATION = "summarization"         # Document summarization
    TROUBLESHOOTING = "troubleshooting"     # Problem-solving assistance


@dataclass
class PromptTemplate:
    """Template for building prompts"""
    name: str
    scenario: PromptScenario
    system_prompt: str
    user_prompt_template: str
    context_format: str
    max_context_chunks: int = 5
    include_citations: bool = True
    include_history: bool = True
    temperature_hint: float = 0.7


class PromptManager:
    """Advanced prompt engineering and template management"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        
    def _initialize_templates(self) -> Dict[PromptScenario, PromptTemplate]:
        """Initialize all prompt templates"""
        
        templates = {}
        
        # General Q&A Template
        templates[PromptScenario.GENERAL_QA] = PromptTemplate(
            name="General Question Answering",
            scenario=PromptScenario.GENERAL_QA,
            system_prompt="""You are a knowledgeable AI assistant that helps users find information from their uploaded documents. Your role is to:

1. Provide accurate, helpful answers based on the provided context
2. Clearly indicate when information is not available in the context
3. Offer to help find additional information when needed
4. Maintain a friendly, professional tone

Guidelines:
- Always base your answers on the provided context
- If the context is insufficient, suggest what additional information might be helpful
- Use clear, concise language
- When appropriate, provide step-by-step explanations""",
            user_prompt_template="""Based on the following context from the user's documents, please answer their question:

{context}

{history}

User Question: {query}

Please provide a comprehensive answer based on the available information.""",
            context_format="standard",
            include_citations=True,
            include_history=True,
            temperature_hint=0.7
        )
        
        # Technical Documentation Template
        templates[PromptScenario.TECHNICAL_DOCS] = PromptTemplate(
            name="Technical Documentation Assistant",
            scenario=PromptScenario.TECHNICAL_DOCS,
            system_prompt="""You are a technical documentation expert that helps developers and engineers understand complex technical information. Your expertise includes:

1. API documentation and integration guides
2. Software architecture and design patterns
3. Configuration and setup procedures
4. Troubleshooting technical issues
5. Code examples and best practices

Guidelines:
- Provide precise, technical answers with specific details
- Include code examples when relevant
- Explain technical concepts clearly
- Reference specific sections, parameters, or configurations when available
- Highlight important warnings or requirements""",
            user_prompt_template="""Technical Documentation Context:
{context}

{history}

Technical Question: {query}

Please provide a detailed technical answer, including:
- Specific implementation details
- Code examples if applicable
- Configuration requirements
- Any important warnings or considerations""",
            context_format="technical",
            max_context_chunks=7,
            include_citations=True,
            include_history=True,
            temperature_hint=0.3
        )
        
        # Procedural/How-to Template
        templates[PromptScenario.PROCEDURAL] = PromptTemplate(
            name="Step-by-Step Instructions",
            scenario=PromptScenario.PROCEDURAL,
            system_prompt="""You are an expert at creating clear, step-by-step instructions and procedures. You excel at:

1. Breaking down complex processes into manageable steps
2. Providing clear, actionable instructions
3. Anticipating common issues and providing solutions
4. Organizing information in logical sequence
5. Including necessary prerequisites and requirements

Guidelines:
- Always provide numbered, sequential steps
- Include prerequisites and preparation steps
- Mention potential pitfalls or common mistakes
- Provide verification steps when appropriate
- Use clear, action-oriented language""",
            user_prompt_template="""Procedural Documentation:
{context}

{history}

How-to Request: {query}

Please provide clear, step-by-step instructions including:
1. Prerequisites and requirements
2. Detailed procedural steps
3. Verification or testing steps
4. Common issues and solutions""",
            context_format="procedural",
            max_context_chunks=6,
            include_citations=True,
            include_history=True,
            temperature_hint=0.4
        )
        
        # Analytical Template
        templates[PromptScenario.ANALYTICAL] = PromptTemplate(
            name="Analysis and Comparison",
            scenario=PromptScenario.ANALYTICAL,
            system_prompt="""You are an analytical expert who helps users understand complex information through comparison, analysis, and synthesis. Your strengths include:

1. Comparing different approaches or solutions
2. Identifying pros and cons of various options
3. Analyzing relationships and dependencies
4. Synthesizing information from multiple sources
5. Providing strategic insights and recommendations

Guidelines:
- Present information in structured, comparative formats
- Highlight key similarities and differences
- Provide balanced analysis of advantages and disadvantages
- Use clear headings and bullet points for complex comparisons
- Offer actionable insights and recommendations""",
            user_prompt_template="""Information for Analysis:
{context}

{history}

Analysis Request: {query}

Please provide a comprehensive analysis including:
- Key points and findings
- Comparisons where relevant
- Advantages and disadvantages
- Recommendations or insights""",
            context_format="analytical",
            max_context_chunks=8,
            include_citations=True,
            include_history=True,
            temperature_hint=0.5
        )
        
        # Troubleshooting Template
        templates[PromptScenario.TROUBLESHOOTING] = PromptTemplate(
            name="Problem Solving Assistant",
            scenario=PromptScenario.TROUBLESHOOTING,
            system_prompt="""You are a troubleshooting expert who helps users diagnose and solve problems systematically. Your approach includes:

1. Identifying potential root causes
2. Suggesting diagnostic steps
3. Providing multiple solution approaches
4. Prioritizing solutions by likelihood and ease
5. Helping prevent similar issues in the future

Guidelines:
- Start with the most common and likely causes
- Provide systematic diagnostic approaches
- Offer multiple solution paths
- Include prevention strategies
- Clearly explain the reasoning behind suggestions""",
            user_prompt_template="""Troubleshooting Context:
{context}

{history}

Problem Description: {query}

Please provide troubleshooting assistance including:
1. Potential root causes (most likely first)
2. Diagnostic steps to identify the issue
3. Step-by-step solutions
4. Prevention recommendations""",
            context_format="troubleshooting",
            max_context_chunks=6,
            include_citations=True,
            include_history=True,
            temperature_hint=0.4
        )
        
        return templates
    
    async def build_rag_prompt(
        self,
        query: str,
        processed_query: ProcessedQuery,
        context_window: ContextWindow,
        chat_history: Optional[List[Message]] = None,
        scenario: Optional[PromptScenario] = None
    ) -> str:
        """
        Build optimized RAG prompt based on query intent and context
        
        Args:
            query: Original user query
            processed_query: Processed query with intent and metadata
            context_window: Retrieved and ranked document context
            chat_history: Recent conversation history
            scenario: Override automatic scenario detection
            
        Returns:
            Optimized prompt string for LLM
        """
        
        try:
            # Determine best prompt scenario
            if scenario is None:
                scenario = await self._determine_scenario(processed_query, context_window)
            
            template = self.templates.get(scenario, self.templates[PromptScenario.GENERAL_QA])
            
            # Format context based on template requirements
            formatted_context = await self._format_context_for_template(
                context_window, template
            )
            
            # Format conversation history if needed
            history_text = ""
            if template.include_history and chat_history:
                history_text = await self._format_conversation_history(
                    chat_history, template
                )
            
            # Build the complete prompt
            user_prompt = template.user_prompt_template.format(
                context=formatted_context,
                history=history_text,
                query=query
            )
            
            logger.info(f"Built {scenario.value} prompt for query: {query[:50]}...")
            
            return user_prompt
            
        except Exception as e:
            logger.error(f"Prompt building failed: {str(e)}")
            # Fallback to simple prompt
            return await self._build_fallback_prompt(query, context_window)
    
    async def get_system_prompt(self, scenario: PromptScenario) -> str:
        """Get system prompt for specific scenario"""
        
        template = self.templates.get(scenario, self.templates[PromptScenario.GENERAL_QA])
        return template.system_prompt
    
    async def get_temperature_hint(self, scenario: PromptScenario) -> float:
        """Get recommended temperature for scenario"""
        
        template = self.templates.get(scenario, self.templates[PromptScenario.GENERAL_QA])
        return template.temperature_hint
    
    async def format_context_for_model(
        self, 
        chunks: List[RankedChunk],
        scenario: PromptScenario = PromptScenario.GENERAL_QA
    ) -> str:
        """Format document chunks optimally for specific scenario and model"""
        
        template = self.templates[scenario]
        
        if not chunks:
            return "No relevant context found in the uploaded documents."
        
        # Limit chunks based on template preferences
        selected_chunks = chunks[:template.max_context_chunks]
        
        if template.context_format == "technical":
            return await self._format_technical_context(selected_chunks)
        elif template.context_format == "procedural":
            return await self._format_procedural_context(selected_chunks)
        elif template.context_format == "analytical":
            return await self._format_analytical_context(selected_chunks)
        elif template.context_format == "troubleshooting":
            return await self._format_troubleshooting_context(selected_chunks)
        else:
            return await self._format_standard_context(selected_chunks)
    
    async def _determine_scenario(
        self, 
        processed_query: ProcessedQuery, 
        context_window: ContextWindow
    ) -> PromptScenario:
        """Automatically determine the best prompt scenario"""
        
        intent = processed_query.intent
        query_lower = processed_query.original_query.lower()
        
        # Check for troubleshooting keywords
        troubleshooting_keywords = [
            'error', 'problem', 'issue', 'not working', 'broken', 'fix', 'debug',
            'troubleshoot', 'solve', 'resolve', 'help with', 'wrong'
        ]
        
        if any(keyword in query_lower for keyword in troubleshooting_keywords):
            return PromptScenario.TROUBLESHOOTING
        
        # Map query intents to scenarios
        intent_mapping = {
            QueryIntent.PROCEDURAL: PromptScenario.PROCEDURAL,
            QueryIntent.ANALYTICAL: PromptScenario.ANALYTICAL,
            QueryIntent.CLARIFICATION: PromptScenario.CLARIFICATION,
            QueryIntent.FACTUAL: PromptScenario.GENERAL_QA,
            QueryIntent.EXPLORATORY: PromptScenario.EXPLORATORY
        }
        
        scenario = intent_mapping.get(intent, PromptScenario.GENERAL_QA)
        
        # Check for technical documentation based on context
        if context_window.chunks_used:
            tech_indicators = ['api', 'config', 'setup', 'install', 'code', 'function', 'class']
            chunk_content = ' '.join([chunk.chunk.content.lower() for chunk in context_window.chunks_used[:2]])
            
            if sum(1 for indicator in tech_indicators if indicator in chunk_content) >= 2:
                return PromptScenario.TECHNICAL_DOCS
        
        return scenario
    
    async def _format_context_for_template(
        self, 
        context_window: ContextWindow, 
        template: PromptTemplate
    ) -> str:
        """Format context based on template requirements"""
        
        if not context_window.chunks_used:
            return "No relevant information found in the uploaded documents."
        
        return await self.format_context_for_model(
            context_window.chunks_used, 
            template.scenario
        )
    
    async def _format_conversation_history(
        self, 
        chat_history: List[Message], 
        template: PromptTemplate
    ) -> str:
        """Format conversation history for inclusion in prompt"""
        
        if not chat_history:
            return ""
        
        # Get recent messages (limit based on context)
        recent_messages = chat_history[-4:] if len(chat_history) > 4 else chat_history
        
        history_parts = []
        for msg in recent_messages:
            role = "Human" if msg.role == "user" else "Assistant"
            history_parts.append(f"{role}: {msg.content[:200]}...")  # Truncate long messages
        
        if history_parts:
            return f"\nConversation History:\n" + "\n".join(history_parts) + "\n"
        
        return ""
    
    async def _format_standard_context(self, chunks: List[RankedChunk]) -> str:
        """Standard context formatting"""
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.chunk.document.filename
            content = chunk.chunk.content.strip()
            
            context_part = f"""## Document {i}: {doc_name}

{content}"""
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    async def _format_technical_context(self, chunks: List[RankedChunk]) -> str:
        """Technical documentation context formatting"""
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.chunk.document.filename
            content = chunk.chunk.content.strip()
            relevance = chunk.final_score
            
            context_part = f"""### Technical Reference {i}: {doc_name} (Relevance: {relevance:.2f})

```
{content}
```"""
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    async def _format_procedural_context(self, chunks: List[RankedChunk]) -> str:
        """Procedural/how-to context formatting"""
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.chunk.document.filename
            content = chunk.chunk.content.strip()
            
            context_part = f"""### Procedure Source {i}: {doc_name}

{content}

---"""
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    async def _format_analytical_context(self, chunks: List[RankedChunk]) -> str:
        """Analytical context formatting with focus on relationships"""
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.chunk.document.filename
            content = chunk.chunk.content.strip()
            
            context_part = f"""#### Analysis Source {i}: {doc_name}

**Content:**
{content}

**Relevance Score:** {chunk.final_score:.2f}
**Document:** {doc_name}"""
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    async def _format_troubleshooting_context(self, chunks: List[RankedChunk]) -> str:
        """Troubleshooting-focused context formatting"""
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.chunk.document.filename
            content = chunk.chunk.content.strip()
            
            context_part = f"""### Troubleshooting Resource {i}: {doc_name}

{content}

*Source: {doc_name}*"""
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    async def _build_fallback_prompt(self, query: str, context_window: ContextWindow) -> str:
        """Build simple fallback prompt if template processing fails"""
        
        context_text = "No context available."
        if context_window and context_window.context_text:
            context_text = context_window.context_text
        
        return f"""Please answer the following question based on the provided context:

Context:
{context_text}

Question: {query}

Answer:"""


# Global prompt manager instance
prompt_manager = PromptManager()