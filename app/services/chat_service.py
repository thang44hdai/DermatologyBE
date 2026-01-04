import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.models import ChatSessions, ChatMessages


class ChatService:
    """
    Service class for handling chatbot interactions with RAG (Retrieval-Augmented Generation).
    """
    
    # Similarity threshold for RAG retrieval (L2 distance)
    # For paraphrase-multilingual-MiniLM-L12-v2 with L2 distance:
    # - Lower scores = more similar (0.0 = identical)
    # - Typical range: 0.0 to 2.0
    # - Threshold 1.2 filters out moderately irrelevant results
    SIMILARITY_THRESHOLD = 14
    
    def __init__(self):
        self.vector_db: Optional[FAISS] = None
        self.embeddings: Optional[HuggingFaceEmbeddings] = None
        self.llm: Optional[ChatOpenAI] = None
        self.initialized = False
        
    def initialize(self):
        """
        Initialize the chat service by loading embeddings, FAISS index, and LLM client.
        This should be called on application startup.
        """
        try:
            print("Initializing ChatService...")
            
            # Load HuggingFace Embeddings
            print("Loading HuggingFace embeddings...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            
            # Load FAISS Vector Database
            print("Loading FAISS index from local storage...")
            self.vector_db = FAISS.load_local(
                "faiss_index_store",
                self.embeddings,
                allow_dangerous_deserialization=True  # Required for loading pickled data
            )
            
            # Initialize ChatOpenAI (pointing to local llama-server)
            print("Initializing LLM client...")
            from app.config import settings
            self.llm = ChatOpenAI(
                base_url=settings.LLM_SERVER_URL,  # Use from environment
                api_key="not-needed",  
                model="PharmaAI-4B",  # Correct model name
                temperature=0.7,
                max_tokens=512
            )
            
            self.initialized = True
            print("ChatService initialized successfully!")
            
        except Exception as e:
            print(f"Failed to initialize ChatService: {e}")
            raise RuntimeError(f"ChatService initialization failed: {e}")
    
    def _ensure_initialized(self):
        """Ensure the service is initialized before processing requests."""
        if not self.initialized:
            raise RuntimeError("ChatService is not initialized. Call initialize() first.")
    
    def _get_or_create_session(self, db: Session, session_id: Optional[str] = None, user_id: int = None) -> ChatSessions:
        """
        Get existing session or create a new one.
        
        Args:
            db: Database session
            session_id: Optional session ID (UUID string)
            user_id: User ID from authentication
            
        Returns:
            ChatSessions object
            
        Raises:
            ValueError: If session_id is provided but not found in database
        """
        if session_id:
            # Fetch existing session
            chat_session = db.query(ChatSessions).filter(
                ChatSessions.id == session_id,
                ChatSessions.deleted_at.is_(None)
            ).first()
            
            if not chat_session:
                raise ValueError(f"Chat session with ID '{session_id}' not found or has been deleted.")
            
            # Verify session belongs to the user
            if chat_session.user_id != user_id:
                raise ValueError(f"Chat session '{session_id}' does not belong to the current user.")
            
            return chat_session
        else:
            # Create new session with default title (will be updated after first message)
            new_session = ChatSessions(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title="New Chat",  # Will be updated from first message
                created_at=datetime.now()
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            
            print(f"Created new chat session: {new_session.id}")
            return new_session
    
    def _generate_session_title(self, message: str, max_length: int = 50) -> str:
        """
        Generate a concise session title from the first user message.
        
        Args:
            message: User's first message
            max_length: Maximum title length
            
        Returns:
            Generated title string
        """
        # Clean and truncate message
        title = message.strip()
        
        # Remove excess whitespace
        title = ' '.join(title.split())
        
        # Truncate if too long
        if len(title) > max_length:
            title = title[:max_length].rsplit(' ', 1)[0] + '...'
        
        return title if title else "New Chat"
    
    def _update_session_title(self, db: Session, session_id: str, message: str):
        """
        Update session title if it's still the default "New Chat".
        
        Args:
            db: Database session
            session_id: Chat session ID
            message: User's message to generate title from
        """
        session = db.query(ChatSessions).filter(
            ChatSessions.id == session_id
        ).first()
        
        if session and session.title == "New Chat":
            new_title = self._generate_session_title(message)
            session.title = new_title
            session.updated_at = datetime.now()
            db.commit()
            print(f"Updated session title to: '{new_title}'")
    
    def _get_chat_history(self, db: Session, session_id: str, limit: int = 5) -> List[Dict[str, str]]:
        """
        Fetch recent chat messages for context.
        
        Args:
            db: Database session
            session_id: Chat session ID
            limit: Number of recent messages to fetch
            
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        messages = db.query(ChatMessages).filter(
            ChatMessages.session_id == session_id,
            ChatMessages.deleted_at.is_(None)
        ).order_by(ChatMessages.created_at.desc()).limit(limit).all()
        
        # Reverse to get chronological order
        messages = list(reversed(messages))
        
        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return history
    
    def _perform_rag_retrieval(self, query: str, k: int = 3) -> tuple[str, List[Dict[str, Any]]]:
        """
        Perform similarity search on vector database with score thresholding.
        
        Args:
            query: User's question
            k: Number of similar documents to retrieve
            
        Returns:
            Tuple of (context_text, sources_metadata)
            Returns empty context and sources if no documents pass the threshold
        """
        if not self.vector_db:
            raise RuntimeError("Vector database is not loaded.")
        
        # Perform similarity search with scores
        docs_with_scores = self.vector_db.similarity_search_with_score(query, k=k)
        
        # Filter documents based on similarity threshold
        # Lower L2 distance = more similar (0.0 = identical)
        filtered_docs = []
        for doc, score in docs_with_scores:
            if score < self.SIMILARITY_THRESHOLD:
                filtered_docs.append((doc, score))
                print(f"Relevant document (score: {score:.4f}): {doc.metadata.get('name', 'Unknown')[:50]}...")
            else:
                print(f"Filtered out (score: {score:.4f}): {doc.metadata.get('name', 'Unknown')[:50]}...")
        
        # Extract context and metadata from filtered documents
        context_parts = []
        sources = []
        
        if filtered_docs:
            for i, (doc, score) in enumerate(filtered_docs, 1):
                context_parts.append(f"[Nguồn {i}] {doc.page_content}")
                sources.append(doc.metadata)
            
            context_text = "\n\n".join(context_parts)
        else:
            # No relevant documents found
            context_text = ""
            print("No relevant documents found (all filtered by threshold)")
        
        return context_text, sources
    
    def _build_prompt(self, user_message: str, context: str, chat_history: List[Dict[str, str]]) -> List:
        """
        Build the prompt for the LLM with system instructions, context, and history.
        
        Args:
            user_message: Current user question
            context: Retrieved context from RAG (can be empty for greetings/general questions)
            chat_history: Previous conversation messages
            
        Returns:
            List of LangChain message objects
        """
        system_prompt = """Bạn là PharmaAI, một trợ lý AI chuyên nghiệp và tận tâm về lĩnh vực y tế, dược phẩm và chăm sóc sức khỏe da liễu của ứng dụng PharmaAI.

Nhiệm vụ của bạn:
- Giải đáp các thắc mắc về sức khỏe, thuốc, bệnh lý và các vấn đề về da liễu cho người dùng một cách chính xác, dễ hiểu và dựa trên bằng chứng khoa học.
- Khi có thông tin từ cơ sở dữ liệu, hãy sử dụng nó để đưa ra câu trả lời chính xác và đề cập đến tên thuốc, thương hiệu, giá cả.
- Khi KHÔNG có thông tin cụ thể từ cơ sở dữ liệu (ví dụ: câu chào hỏi, câu hỏi chung), hãy trả lời một cách tự nhiên và thân thiện.
- Trả lời bằng tiếng Việt, ngắn gọn, dễ hiểu và thân thiện.

Lưu ý quan trọng:
- KHÔNG tự bịa đặt thông tin về thuốc hoặc sản phẩm cụ thể.
- Luôn khuyên người dùng đi khám bác sĩ hoặc dược sĩ nếu triệu chứng nghiêm trọng hoặc kéo dài.
- Với câu hỏi chung về định nghĩa bệnh lý, bạn có thể giải thích dựa trên kiến thức y học phổ thông."""

        messages = [SystemMessage(content=system_prompt)]
        
        # Add chat history
        for msg in chat_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current query with or without context
        if context:
            # We have relevant product/medicine information from database
            current_prompt = f"""Ngữ cảnh từ cơ sở dữ liệu:
{context}

Câu hỏi của người dùng: {user_message}

Hãy trả lời dựa trên ngữ cảnh trên."""
        else:
            # No relevant products found - handle as general conversation or definition
            current_prompt = f"""Câu hỏi của người dùng: {user_message}

Lưu ý: Không có sản phẩm cụ thể nào từ cơ sở dữ liệu phù hợp với câu hỏi này. Hãy trả lời một cách tự nhiên và hữu ích."""

        messages.append(HumanMessage(content=current_prompt))
        
        return messages
    
    def _save_messages(
        self,
        db: Session,
        session_id: str,
        user_message: str,
        ai_response: str,
        sources: List[Dict[str, Any]]
    ):
        """
        Save user and AI messages to the database.
        
        Args:
            db: Database session
            session_id: Chat session ID
            user_message: User's message
            ai_response: AI's response
            sources: RAG sources metadata
        """
        # Save user message
        user_msg = ChatMessages(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=user_message,
            created_at=datetime.now()
        )
        db.add(user_msg)
        
        # Save AI response with sources
        # Convert sources to JSON string since column type is TEXT
        sources_json = json.dumps(sources, ensure_ascii=False) if sources else None
        
        ai_msg = ChatMessages(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=ai_response,
            sources=sources_json,
            created_at=datetime.now() + timedelta(seconds=1)
        )
        db.add(ai_msg)
        
        db.commit()
    
    async def process_chat_streaming(
        self,
        db: Session,
        message: str,
        session_id: Optional[str] = None,
        user_id: int = None
    ):
        """
        Process a chat message with RAG and LLM in streaming mode.
        Yields progress updates and response chunks in realtime.
        
        Args:
            db: Database session
            message: User's message
            session_id: Optional chat session ID
            user_id: User ID from authentication
            
        Yields:
            Dictionary with type and data for each streaming event:
            - {'type': 'status', 'status': 'message'} for progress updates
            - {'type': 'start', 'session_id': '...'} when starting generation
            - {'type': 'chunk', 'content': '...'} for each response chunk
            - {'type': 'end', 'sources': [...]} when complete
            
        Raises:
            RuntimeError: If service is not initialized
            ValueError: If session_id is invalid or doesn't belong to user
        """
        self._ensure_initialized()
        
        try:
            # Step 1: Session Management
            yield {'type': 'status', 'status': 'Đang khởi tạo phiên chat...'}
            chat_session = self._get_or_create_session(db, session_id, user_id)
            current_session_id = chat_session.id
            
            # Step 2: Chat History
            yield {'type': 'status', 'status': 'Đang tải lịch sử hội thoại...'}
            chat_history = self._get_chat_history(db, current_session_id, limit=5)
            print(f"📜 Loaded {len(chat_history)} previous messages from history")
            
            # Step 3: RAG Retrieval
            yield {'type': 'status', 'status': 'Đang tìm kiếm thông tin liên quan...'}
            print(f"🔍 Performing RAG retrieval for: '{message[:50]}...'")
            context, sources = self._perform_rag_retrieval(message, k=3)
            print(f"✅ Retrieved {len(sources)} relevant sources")
            
            # Step 4: LLM Streaming Generation
            yield {'type': 'status', 'status': 'Đang tạo câu trả lời...'}
            yield {'type': 'start', 'session_id': current_session_id}
            
            print("🤖 Generating streaming response from LLM...")
            prompt_messages = self._build_prompt(message, context, chat_history)
            
            # Stream the response
            full_response = ""
            async for chunk in self.llm.astream(prompt_messages):
                if chunk.content:
                    full_response += chunk.content
                    yield {'type': 'chunk', 'content': chunk.content}
            
            print(f"✅ Generated response: '{full_response[:100]}...'")
            
            # Step 5: Update session title if it's a new session
            if not session_id:  # New session - update title from first message
                self._update_session_title(db, current_session_id, message)
            
            # Step 6: Persistence
            print("💾 Saving messages to database...")
            self._save_messages(db, current_session_id, message, full_response, sources)
            
            # Step 7: Send completion with sources
            yield {
                'type': 'end',
                'sources': sources,
                'created_at': datetime.now()
            }
            
        except ValueError as ve:
            # Re-raise validation errors
            raise ve
        except SQLAlchemyError as db_error:
            db.rollback()
            print(f"❌ Database error: {db_error}")
            raise RuntimeError(f"Database error occurred: {db_error}")
        except Exception as e:
            db.rollback()
            print(f"❌ Error processing chat: {e}")
            raise RuntimeError(f"Failed to process chat: {e}")
    
    def process_chat(
        self,
        db: Session,
        message: str,
        session_id: Optional[str] = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """
        Process a chat message with RAG and LLM.
        
        Args:
            db: Database session
            message: User's message
            session_id: Optional chat session ID
            user_id: User ID from authentication
            
        Returns:
            Dictionary containing session_id, answer, sources, and created_at
            
        Raises:
            RuntimeError: If service is not initialized
            ValueError: If session_id is invalid or doesn't belong to user
            Exception: For other processing errors
        """
        self._ensure_initialized()
        
        try:
            # Step 1: Session Management
            chat_session = self._get_or_create_session(db, session_id, user_id)
            current_session_id = chat_session.id
            
            # Step 2: Chat History
            chat_history = self._get_chat_history(db, current_session_id, limit=5)
            print(f"📜 Loaded {len(chat_history)} previous messages from history")
            
            # Step 3: RAG Retrieval
            print(f"🔍 Performing RAG retrieval for: '{message[:50]}...'")
            context, sources = self._perform_rag_retrieval(message, k=3)
            print(f"✅ Retrieved {len(sources)} relevant sources")
            
            # Step 4: LLM Generation
            print("🤖 Generating response from LLM...")
            prompt_messages = self._build_prompt(message, context, chat_history)
            
            response = self.llm.invoke(prompt_messages)
            ai_answer = response.content
            print(f"✅ Generated response: '{ai_answer[:100]}...'")
            
            # Step 5: Persistence
            print("💾 Saving messages to database...")
            self._save_messages(db, current_session_id, message, ai_answer, sources)
            
            # Step 6: Return
            return {
                "session_id": current_session_id,
                "answer": ai_answer,
                "sources": sources,
                "created_at": datetime.now()
            }
            
        except ValueError as ve:
            # Re-raise validation errors
            raise ve
        except SQLAlchemyError as db_error:
            db.rollback()
            print(f"❌ Database error: {db_error}")
            raise RuntimeError(f"Database error occurred: {db_error}")
        except Exception as e:
            db.rollback()
            print(f"❌ Error processing chat: {e}")
            raise RuntimeError(f"Failed to process chat: {e}")


# Singleton instance
chat_service = ChatService()
