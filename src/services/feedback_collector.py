import json
import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from src.models.feedback import TradeFeedback, FeedbackQuery, FeedbackSummary

class FeedbackCollector:
    """Service for collecting and managing human feedback on trades"""

    def __init__(self, feedback_file: str = "feedback_log.jsonl", audit_file: str = "audit_log.jsonl"):
        self.feedback_file = Path(feedback_file)
        self.audit_file = Path(audit_file)

        logging.basicConfig(
            filename=str(self.feedback_file),
            level=logging.INFO,
            format='%(message)s'
        )
        self.logger = logging.getLogger("feedback_logger")

    def submit_feedback(self, feedback: TradeFeedback) -> dict:
        """
        Submit human feedback for a specific trade.
        Returns confirmation with feedback_id.
        """
        if not self._validate_trade_exists(feedback.trade_id):
            raise ValueError(f"Trade ID {feedback.trade_id} not found in audit logs")

        try:
            log_entry = feedback.model_dump()
            self.logger.info(json.dumps(log_entry))

            print(f"\n[FeedbackCollector] Feedback {feedback.feedback_id} recorded for trade {feedback.trade_id}")
            print(f"  Outcome: {feedback.actual_outcome}")
            print(f"  Decision Quality: {feedback.decision_quality_score}/10")
            print(f"  Reward Signal: {feedback.reward_signal:.2f}")

            return {
                "status": "success",
                "feedback_id": feedback.feedback_id,
                "trade_id": feedback.trade_id,
                "timestamp": feedback.timestamp
            }
        except Exception as e:
            print(f"[FeedbackCollector] Error recording feedback: {e}")
            raise

    def get_feedback_for_trade(self, trade_id: str) -> List[TradeFeedback]:
        """Retrieve all feedback for a specific trade"""
        if not self.feedback_file.exists():
            return []

        feedbacks = []
        with open(self.feedback_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get("trade_id") == trade_id:
                        feedbacks.append(TradeFeedback(**data))
                except Exception as e:
                    print(f"Error parsing feedback line: {e}")
                    continue

        return feedbacks

    def query_feedback(self, query: FeedbackQuery) -> List[TradeFeedback]:
        """Query feedback based on filters"""
        if not self.feedback_file.exists():
            return []

        feedbacks = []
        with open(self.feedback_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    feedback = TradeFeedback(**data)

                    if query.trade_ids and feedback.trade_id not in query.trade_ids:
                        continue

                    if query.actual_outcome and feedback.actual_outcome != query.actual_outcome:
                        continue

                    if query.min_quality_score and feedback.decision_quality_score < query.min_quality_score:
                        continue

                    if query.date_from:
                        if feedback.timestamp < query.date_from:
                            continue

                    if query.date_to:
                        if feedback.timestamp > query.date_to:
                            continue

                    feedbacks.append(feedback)

                    if len(feedbacks) >= query.limit:
                        break

                except Exception as e:
                    continue

        return feedbacks

    def get_trade_details(self, trade_id: str) -> Optional[dict]:
        """Retrieve the original trade analysis from audit logs"""
        if not self.audit_file.exists():
            return None

        with open(self.audit_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get("trade_id") == trade_id:
                        return data
                except Exception:
                    continue

        return None

    def get_summary_statistics(self, query: Optional[FeedbackQuery] = None) -> FeedbackSummary:
        """Generate aggregate statistics from feedback data"""
        if query is None:
            query = FeedbackQuery()

        feedbacks = self.query_feedback(query)

        if not feedbacks:
            return FeedbackSummary(
                total_feedbacks=0,
                avg_decision_quality=0.0,
                avg_reward_signal=0.0,
                outcome_distribution={},
                decision_accuracy={},
                agent_accuracy_avg={},
                top_missed_factors=[]
            )

        total = len(feedbacks)
        avg_quality = sum(f.decision_quality_score for f in feedbacks) / total
        avg_reward = sum(f.reward_signal for f in feedbacks) / total

        outcome_dist = {}
        for f in feedbacks:
            outcome_dist[f.actual_outcome] = outcome_dist.get(f.actual_outcome, 0) + 1

        decision_accuracy = {
            "correct": sum(1 for f in feedbacks if f.was_decision_correct),
            "incorrect": sum(1 for f in feedbacks if not f.was_decision_correct),
            "accuracy_rate": sum(1 for f in feedbacks if f.was_decision_correct) / total
        }

        agent_scores = {
            "technical": [],
            "sentiment": [],
            "metrics": [],
            "volatility": []
        }
        for f in feedbacks:
            if f.technical_agent_accuracy:
                agent_scores["technical"].append(f.technical_agent_accuracy)
            if f.sentiment_agent_accuracy:
                agent_scores["sentiment"].append(f.sentiment_agent_accuracy)
            if f.metrics_agent_accuracy:
                agent_scores["metrics"].append(f.metrics_agent_accuracy)
            if f.volatility_agent_accuracy:
                agent_scores["volatility"].append(f.volatility_agent_accuracy)

        agent_accuracy_avg = {
            agent: sum(scores) / len(scores) if scores else None
            for agent, scores in agent_scores.items()
        }

        missed_factors_count = {}
        for f in feedbacks:
            if f.missed_factors:
                for factor in f.missed_factors:
                    missed_factors_count[factor] = missed_factors_count.get(factor, 0) + 1

        top_missed = [
            {"factor": factor, "count": count}
            for factor, count in sorted(missed_factors_count.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        return FeedbackSummary(
            total_feedbacks=total,
            avg_decision_quality=round(avg_quality, 2),
            avg_reward_signal=round(avg_reward, 3),
            outcome_distribution=outcome_dist,
            decision_accuracy=decision_accuracy,
            agent_accuracy_avg=agent_accuracy_avg,
            top_missed_factors=top_missed
        )

    def _validate_trade_exists(self, trade_id: str) -> bool:
        """Check if trade exists in audit logs"""
        return self.get_trade_details(trade_id) is not None

    def list_recent_trades(self, limit: int = 20) -> List[dict]:
        """List recent trades that can receive feedback"""
        if not self.audit_file.exists():
            return []

        trades = []
        with open(self.audit_file, 'r') as f:
            lines = f.readlines()
            for line in reversed(lines[-limit:]):
                try:
                    data = json.loads(line.strip())
                    trades.append({
                        "trade_id": data.get("trade_id"),
                        "asset": data.get("signal", {}).get("asset"),
                        "type": data.get("signal", {}).get("type"),
                        "decision": data.get("decision"),
                        "composite_score": data.get("composite_score"),
                        "timestamp": data.get("timestamp")
                    })
                except Exception:
                    continue

        return trades
