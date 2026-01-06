"""
Intent Classifier for PharmaAI Chatbot
Classifies user queries to determine whether RAG should be used.
"""

from enum import Enum
from typing import Tuple
import re
import unicodedata


class Intent(Enum):
    """Intent types for user queries."""
    GREETING = "greeting"
    FAREWELL = "farewell"
    DRUG_QUERY = "drug_query"
    MEDICAL_INFO = "medical_info"
    GENERAL = "general"


class IntentClassifier:
    """
    Rule-based intent classifier for Vietnamese pharmaceutical chatbot.
    Uses pattern matching to classify user intent and determine RAG usage.
    """
    
    # Greeting patterns (Vietnamese + English)
    GREETING_PATTERNS = [
        r'\b(xin )?chào\b',
        r'\bhello\b',
        r'\bhi\b',
        r'\bhey\b',
        r'\bchao\b',
        r'\bkính chào\b',
    ]
    
    # Farewell patterns
    FAREWELL_PATTERNS = [
        r'\btạm biệt\b',
        r'\bbye\b',
        r'\bgoodbye\b',
        r'\bcảm ơn\b',
        r'\bcam on\b',
        r'\bthanks?\b',
        r'\bthank you\b',
        r'\bhẹn gặp lại\b',
    ]
    
    # Drug query patterns (specific product/price queries)
    DRUG_PATTERNS = [
        r'\bthuốc\b',
        r'\bthuoc\b',
        r'\bdùng thuốc\b',
        r'\bgia thuốc\b',
        r'\bgiá thuốc\b',
        r'\bmua ở đâu\b',
        r'\bmua o dau\b',
        r'\bviên nang\b',
        r'\bthuốc bôi\b',
        r'\bthuốc uống\b',
        r'\bsản phẩm\b',
        r'\bsan pham\b',
        r'\bkem bôi\b',
        r'\bkem tri\b',
        r'\bsữa rửa mặt\b',
        r'\bsua rua mat\b',
        r'\bthương hiệu\b',
        r'\bthuong hieu\b',
        r'\bbrand\b',
        r'\bgiá cả\b',
        r'\bgia ca\b',
        r'\bprice\b',
    ]
    
    # Medical info patterns (symptoms, diseases, skin conditions)
    MEDICAL_PATTERNS = [
        r'\bmụn\b',
        r'\bmun\b',
        r'\bacne\b',
        r'\bnổi mẩn\b',
        r'\bnoi man\b',
        r'\bviêm da\b',
        r'\bviem da\b',
        r'\bdermatitis\b',
        r'\bbệnh\b',
        r'\bbenh\b',
        r'\btriệu chứng\b',
        r'\btrieu chung\b',
        r'\bsymptom\b',
        r'\bchữa\b',
        r'\bchua\b',
        r'\bđiều trị\b',
        r'\bdieu tri\b',
        r'\btreatment\b',
        r'\beczema\b',
        r'\bpsoriasis\b',
        r'\bvảy nến\b',
        r'\bvay nen\b',
        r'\bngứa\b',
        r'\bngua\b',
        r'\bitch\b',
        r'\bsẹo\b',
        r'\bseo\b',
        r'\bscar\b',
        r'\btàn nhang\b',
        r'\btan nhang\b',
        r'\bnám\b',
        r'\bmelasma\b',
        r'\bthâm\b',
        r'\btham\b',
        r'\bhyperpigmentation\b',
        r'\brụng tóc\b',
        r'\brung toc\b',
        r'\bhair loss\b',
        r'\bgàu\b',
        r'\bgau\b',
        r'\bdandruff\b',
    ]
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize intent classifier.
        
        Args:
            confidence_threshold: Minimum confidence score for intent classification
        """
        self.confidence_threshold = confidence_threshold
        
        # Compile regex patterns for better performance
        self.greeting_regex = [re.compile(p, re.IGNORECASE) for p in self.GREETING_PATTERNS]
        self.farewell_regex = [re.compile(p, re.IGNORECASE) for p in self.FAREWELL_PATTERNS]
        self.drug_regex = [re.compile(p, re.IGNORECASE) for p in self.DRUG_PATTERNS]
        self.medical_regex = [re.compile(p, re.IGNORECASE) for p in self.MEDICAL_PATTERNS]
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize Vietnamese text by removing extra whitespace.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip().lower()
    
    def _match_patterns(self, text: str, patterns: list) -> Tuple[bool, float]:
        """
        Match text against a list of regex patterns.
        
        Args:
            text: Normalized text
            patterns: List of compiled regex patterns
            
        Returns:
            Tuple of (matched, confidence_score)
        """
        matches = 0
        for pattern in patterns:
            if pattern.search(text):
                matches += 1
        
        if matches > 0:
            # Confidence increases with number of matches
            confidence = min(0.5 + (matches * 0.3), 1.0)
            return True, confidence
        
        return False, 0.0
    
    def classify(self, message: str) -> Tuple[Intent, float]:
        """
        Classify user message intent using rule-based pattern matching.
        
        Args:
            message: User's message
            
        Returns:
            Tuple of (Intent, confidence_score)
        """
        # Normalize message
        normalized = self._normalize_text(message)
        
        # Check patterns in order of priority
        # 1. Greeting (highest priority for short messages)
        if len(normalized.split()) <= 5:  # Short messages more likely to be greetings
            matched, confidence = self._match_patterns(normalized, self.greeting_regex)
            if matched:
                return Intent.GREETING, min(confidence + 0.2, 1.0)  # Boost confidence for short greetings
        
        # 2. Farewell
        matched, confidence = self._match_patterns(normalized, self.farewell_regex)
        if matched and confidence >= self.confidence_threshold:
            return Intent.FAREWELL, confidence
        
        # 3. Drug Query (specific product questions)
        matched, confidence = self._match_patterns(normalized, self.drug_regex)
        if matched and confidence >= self.confidence_threshold:
            return Intent.DRUG_QUERY, confidence
        
        # 4. Medical Info (symptoms, diseases, conditions)
        matched, confidence = self._match_patterns(normalized, self.medical_regex)
        if matched and confidence >= self.confidence_threshold:
            return Intent.MEDICAL_INFO, confidence
        
        # 5. General (fallback)
        # For general queries, confidence is lower since we're not sure
        return Intent.GENERAL, 0.5
    
    def should_use_rag(self, intent: Intent) -> bool:
        """
        Determine if RAG should be used based on intent.
        
        Args:
            intent: Classified intent
            
        Returns:
            True if RAG should be used, False otherwise
        """
        # Use RAG for drug queries, medical info, and general questions
        # Skip RAG for greetings and farewells
        return intent in [Intent.DRUG_QUERY, Intent.MEDICAL_INFO, Intent.GENERAL]
