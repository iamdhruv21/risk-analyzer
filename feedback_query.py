import json
import sys
from typing import Optional
from src.services.feedback_collector import FeedbackCollector
from src.models.feedback import FeedbackQuery

def print_separator():
    print("=" * 100)

def display_summary(collector: FeedbackCollector):
    """Display aggregate feedback statistics"""
    summary = collector.get_summary_statistics()

    print_separator()
    print("FEEDBACK SUMMARY STATISTICS")
    print_separator()

    print(f"\nTotal Feedbacks: {summary.total_feedbacks}")
    print(f"Average Decision Quality: {summary.avg_decision_quality}/10")
    print(f"Average Reward Signal: {summary.avg_reward_signal:.3f}")

    print("\nOutcome Distribution:")
    for outcome, count in summary.outcome_distribution.items():
        percentage = (count / summary.total_feedbacks * 100) if summary.total_feedbacks > 0 else 0
        print(f"  {outcome:<20}: {count:>4} ({percentage:>5.1f}%)")

    print("\nDecision Accuracy:")
    acc = summary.decision_accuracy
    print(f"  Correct Decisions  : {acc.get('correct', 0)}")
    print(f"  Incorrect Decisions: {acc.get('incorrect', 0)}")
    print(f"  Accuracy Rate      : {acc.get('accuracy_rate', 0)*100:.1f}%")

    print("\nAgent Accuracy (Average):")
    for agent, avg_score in summary.agent_accuracy_avg.items():
        if avg_score:
            print(f"  {agent.capitalize():<15}: {avg_score:.2f}/10")
        else:
            print(f"  {agent.capitalize():<15}: No data")

    if summary.top_missed_factors:
        print("\nTop Missed Factors:")
        for item in summary.top_missed_factors:
            print(f"  {item['factor']:<30}: {item['count']} occurrences")

    print_separator()

def query_by_outcome(collector: FeedbackCollector, outcome: str):
    """Query feedbacks by outcome type"""
    query = FeedbackQuery(actual_outcome=outcome, limit=100)
    feedbacks = collector.query_feedback(query)

    print_separator()
    print(f"FEEDBACKS WITH OUTCOME: {outcome}")
    print_separator()

    if not feedbacks:
        print("No feedbacks found for this outcome.")
        return

    print(f"Found {len(feedbacks)} feedback(s)\n")

    for fb in feedbacks:
        trade = collector.get_trade_details(fb.trade_id)
        asset = trade.get('signal', {}).get('asset', 'N/A') if trade else 'N/A'
        decision = trade.get('decision', 'N/A') if trade else 'N/A'

        print(f"Trade ID: {fb.trade_id}")
        print(f"  Asset: {asset} | Decision: {decision}")
        print(f"  Quality: {fb.decision_quality_score}/10 | Reward: {fb.reward_signal:.2f}")
        print(f"  Correct: {fb.was_decision_correct} | Outcome: {fb.actual_outcome}")
        print(f"  Reason: {fb.outcome_reason}")
        if fb.what_went_wrong:
            print(f"  Wrong: {fb.what_went_wrong}")
        if fb.missed_factors:
            print(f"  Missed: {', '.join(fb.missed_factors)}")
        print()

    print_separator()

def query_incorrect_decisions(collector: FeedbackCollector):
    """Find all feedbacks where the decision was incorrect"""
    all_feedbacks = collector.query_feedback(FeedbackQuery(limit=1000))
    incorrect = [fb for fb in all_feedbacks if not fb.was_decision_correct]

    print_separator()
    print("INCORRECT DECISIONS (Learning Opportunities)")
    print_separator()

    if not incorrect:
        print("No incorrect decisions found. All decisions were correct!")
        return

    print(f"Found {len(incorrect)} incorrect decision(s)\n")

    for fb in incorrect:
        trade = collector.get_trade_details(fb.trade_id)
        asset = trade.get('signal', {}).get('asset', 'N/A') if trade else 'N/A'
        actual_decision = trade.get('decision', 'N/A') if trade else 'N/A'

        print(f"Trade ID: {fb.trade_id}")
        print(f"  Asset: {asset}")
        print(f"  System Decision: {actual_decision}")
        print(f"  Should Have Been: {fb.should_have_been}")
        print(f"  Outcome: {fb.actual_outcome}")
        print(f"  Reason: {fb.outcome_reason}")
        if fb.reasoning_corrections:
            print(f"  Corrections: {fb.reasoning_corrections}")
        if fb.missed_factors:
            print(f"  Missed Factors: {', '.join(fb.missed_factors)}")
        print()

    print_separator()

def export_training_data(collector: FeedbackCollector, output_file: str):
    """Export feedback data in format suitable for ML training"""
    all_feedbacks = collector.query_feedback(FeedbackQuery(limit=10000))

    training_data = []
    for fb in all_feedbacks:
        trade = collector.get_trade_details(fb.trade_id)
        if not trade:
            continue

        record = {
            "trade_id": fb.trade_id,
            "signal": trade.get("signal"),
            "context": trade.get("context"),
            "metrics": trade.get("metrics"),
            "agent_reports": trade.get("agent_reports"),
            "system_decision": trade.get("decision"),
            "composite_score": trade.get("composite_score"),
            "feedback": {
                "actual_outcome": fb.actual_outcome,
                "was_correct": fb.was_decision_correct,
                "should_have_been": fb.should_have_been,
                "quality_score": fb.decision_quality_score,
                "reward_signal": fb.reward_signal,
                "agent_accuracy": {
                    "technical": fb.technical_agent_accuracy,
                    "sentiment": fb.sentiment_agent_accuracy,
                    "metrics": fb.metrics_agent_accuracy,
                    "volatility": fb.volatility_agent_accuracy
                },
                "missed_factors": fb.missed_factors,
                "market_results": {
                    "price_movement": fb.actual_price_movement,
                    "tp_hit": fb.tp_hit,
                    "sl_hit": fb.sl_hit,
                    "max_drawdown": fb.max_drawdown_percent,
                    "max_profit": fb.max_profit_percent
                }
            }
        }
        training_data.append(record)

    with open(output_file, 'w') as f:
        json.dump(training_data, f, indent=2)

    print(f"\n✓ Exported {len(training_data)} records to {output_file}")
    print("  This data can be used for:")
    print("    - Fine-tuning agent weights")
    print("    - Training decision thresholds")
    print("    - Identifying systematic biases")
    print("    - Reward model training")

def list_feedback_for_trade(collector: FeedbackCollector, trade_id: str):
    """List all feedback for a specific trade"""
    feedbacks = collector.get_feedback_for_trade(trade_id)

    print_separator()
    print(f"FEEDBACK HISTORY FOR TRADE: {trade_id}")
    print_separator()

    if not feedbacks:
        print("No feedback found for this trade.")
        return

    trade = collector.get_trade_details(trade_id)
    if trade:
        print(f"\nOriginal Decision: {trade.get('decision')}")
        print(f"Composite Score: {trade.get('composite_score')}")
        print(f"Asset: {trade.get('signal', {}).get('asset')}\n")

    for i, fb in enumerate(feedbacks, 1):
        print(f"Feedback #{i} (ID: {fb.feedback_id})")
        print(f"  Timestamp: {fb.timestamp}")
        print(f"  Provider: {fb.feedback_provider}")
        print(f"  Outcome: {fb.actual_outcome}")
        print(f"  Decision Correct: {fb.was_decision_correct}")
        print(f"  Quality: {fb.decision_quality_score}/10")
        print(f"  Reward: {fb.reward_signal:.2f}")
        if fb.what_went_right:
            print(f"  Right: {fb.what_went_right}")
        if fb.what_went_wrong:
            print(f"  Wrong: {fb.what_went_wrong}")
        print()

    print_separator()

def main():
    collector = FeedbackCollector()

    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python feedback_query.py summary                    # Show aggregate statistics")
        print("  python feedback_query.py outcome <OUTCOME>          # Query by outcome (SUCCESS, FAILURE, etc.)")
        print("  python feedback_query.py incorrect                  # Show incorrect decisions")
        print("  python feedback_query.py trade <trade_id>           # Show feedback for specific trade")
        print("  python feedback_query.py export <output_file.json>  # Export training data")
        print()
        sys.exit(1)

    command = sys.argv[1]

    if command == "summary":
        display_summary(collector)

    elif command == "outcome":
        if len(sys.argv) < 3:
            print("Error: Outcome type required (SUCCESS, FAILURE, PARTIAL_SUCCESS, NOT_EXECUTED, PENDING)")
            sys.exit(1)
        outcome = sys.argv[2].upper()
        query_by_outcome(collector, outcome)

    elif command == "incorrect":
        query_incorrect_decisions(collector)

    elif command == "trade":
        if len(sys.argv) < 3:
            print("Error: Trade ID required")
            sys.exit(1)
        trade_id = sys.argv[2]
        list_feedback_for_trade(collector, trade_id)

    elif command == "export":
        if len(sys.argv) < 3:
            print("Error: Output filename required")
            sys.exit(1)
        output_file = sys.argv[2]
        export_training_data(collector, output_file)

    else:
        print(f"Error: Unknown command '{command}'")
        sys.exit(1)

if __name__ == "__main__":
    main()
