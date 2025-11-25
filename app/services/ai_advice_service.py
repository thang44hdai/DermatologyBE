"""
AI Advice Service

Generates personalized medication advice based on adherence behavior.
Uses AI to analyze user's adherence patterns and provide recommendations.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.services.chat_service import chat_service
from app.models.database import MedicationReminder, AdherenceLog
from app.schemas.reminder import AIAdvice

logger = logging.getLogger(__name__)


class AIAdviceService:
    """Service for generating AI-powered medication advice based on adherence"""
    
    def __init__(self):
        self.initialized = False
    
    def _ensure_initialized(self):
        """Ensure chat service is initialized"""
        if not self.initialized:
            if chat_service.llm is None:
                raise RuntimeError("Chat service not initialized. Cannot generate AI advice.")
            self.initialized = True
    
    async def generate_advice_for_reminder(
        self,
        db: Session,
        reminder_id: int,
        user_id: int
    ) -> AIAdvice:
        """
        Generate personalized advice based on reminder's adherence history
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID
            
        Returns:
            AIAdvice with personalized message
        """
        self._ensure_initialized()
        
        try:
            # Get reminder
            reminder = db.query(MedicationReminder).filter(
                and_(
                    MedicationReminder.id == reminder_id,
                    MedicationReminder.user_id == user_id
                )
            ).first()
            
            if not reminder:
                raise ValueError("Reminder not found")
            
            # Get adherence statistics (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            logs = db.query(AdherenceLog).filter(
                and_(
                    AdherenceLog.reminder_id == reminder_id,
                    AdherenceLog.user_id == user_id,
                    AdherenceLog.created_at >= thirty_days_ago
                )
            ).all()
            
            # Calculate statistics
            total_logs = len(logs)
            taken_count = sum(1 for log in logs if log.action_type == 'taken')
            snoozed_count = sum(1 for log in logs if log.action_type == 'snoozed')
            skipped_count = sum(1 for log in logs if log.action_type == 'skipped')
            
            adherence_rate = (taken_count / total_logs * 100) if total_logs > 0 else 0
            
            # Generate AI advice
            advice_text = await self._generate_advice_text(
                medicine_name=reminder.medicine_name,
                frequency=reminder.frequency,
                total_logs=total_logs,
                taken_count=taken_count,
                snoozed_count=snoozed_count,
                skipped_count=skipped_count,
                adherence_rate=adherence_rate
            )
            
            return AIAdvice(
                medicine_name=reminder.medicine_name,
                advice_text=advice_text,
                adherence_rate=round(adherence_rate, 2),
                total_logs=total_logs
            )
        
        except Exception as e:
            logger.error(f"Error generating AI advice: {e}")
            # Return fallback advice
            return AIAdvice(
                medicine_name="Unknown",
                advice_text="Hãy tiếp tục duy trì thói quen uống thuốc đều đặn và theo dõi tình trạng sức khỏe của bạn.",
                adherence_rate=0.0,
                total_logs=0
            )
    
    async def _generate_advice_text(
        self,
        medicine_name: str,
        frequency: str,
        total_logs: int,
        taken_count: int,
        snoozed_count: int,
        skipped_count: int,
        adherence_rate: float
    ) -> str:
        """
        Generate personalized advice text using LLM
        
        Args:
            medicine_name: Name of medicine
            frequency: Reminder frequency
            total_logs: Total adherence logs
            taken_count: Number of taken actions
            snoozed_count: Number of snoozed actions
            skipped_count: Number of skipped actions
            adherence_rate: Adherence rate percentage
            
        Returns:
            Personalized advice text
        """
        # Build context for LLM
        system_prompt = """Bạn là một dược sĩ chuyên nghiệp và thân thiện. 
Nhiệm vụ của bạn là phân tích thói quen uống thuốc của người dùng và đưa ra lời khuyên ngắn gọn, khích lệ.
Lời khuyên của bạn phải:
- Ngắn gọn (2-3 câu)
- Thân thiện, động viên
- Cụ thể dựa trên số liệu
- Khuyến khích nếu ổn, động viên cải thiện nếu chưa tốt"""
        
        # Analyze behavior
        if total_logs == 0:
            behavior_desc = "chưa có dữ liệu uống thuốc"
        elif adherence_rate >= 80:
            behavior_desc = f"rất tốt với {adherence_rate:.1f}% uống đúng giờ"
        elif adherence_rate >= 60:
            behavior_desc = f"khá ổn với {adherence_rate:.1f}% uống đúng giờ"
        else:
            behavior_desc = f"cần cải thiện ({adherence_rate:.1f}% uống đúng giờ)"
        
        prompt = f"""Phân tích thói quen uống thuốc của người dùng:

Thuốc: {medicine_name}
Tần suất: {frequency}
Trong 30 ngày qua:
- Tổng số lần: {total_logs}
- Uống đúng giờ: {taken_count} lần
- Hoãn lại: {snoozed_count} lần  
- Bỏ qua: {skipped_count} lần
- Tỷ lệ tuân thủ: {adherence_rate:.1f}%

Tình trạng: {behavior_desc}

Hãy viết một đoạn văn ngắn (2-3 câu) động viên và khuyên người dùng. Nếu ổn thì khen ngợi và khuyến khích duy trì. Nếu chưa tốt thì động viên cải thiện một cách nhẹ nhàng."""
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = chat_service.llm.invoke(messages)
            advice_text = response.content.strip()
            
            logger.info(f"Generated advice for {medicine_name}: {advice_text[:50]}...")
            return advice_text
        
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            # Fallback advice based on adherence rate
            if adherence_rate >= 80:
                return f"Tuyệt vời! Bạn đang uống {medicine_name} rất đều đặn với tỷ lệ tuân thủ {adherence_rate:.0f}%. Hãy tiếp tục duy trì thói quen tốt này nhé!"
            elif adherence_rate >= 60:
                return f"Bạn đang uống {medicine_name} khá ổn với {adherence_rate:.0f}% tuân thủ. Hãy cố gắng uống đúng giờ hơn để đạt hiệu quả điều trị tốt nhất nhé!"
            else:
                return f"Tôi thấy bạn hay quên uống {medicine_name}. Hãy đặt nhắc nhở và tạo thói quen uống thuốc cố định để cải thiện hiệu quả điều trị nhé!"


# Create singleton instance
ai_advice_service = AIAdviceService()
