import sys
from typing import Optional
from src.services.feedback_collector import FeedbackCollector
from src.models.feedback import TradeFeedback

def print_separator():
    print("=" * 80)

def print_trade_details(trade_data: dict):
    """Display trade analysis details"""
    print_separator()
    print("TRADE ANALYSIS DETAILS")
    print_separator()
    print(f"Trade ID: {trade_data.get('trade_id')}")
    print(f"Timestamp: {trade_data.get('timestamp')}")
    print()

    signal = trade_data.get('signal', {})
    print(f"Asset: {signal.get('asset')} ({signal.get('assetClass')})")
    print(f"Type: {signal.get('type')}")
    print(f"Price: {signal.get('price')}")
    print(f"TP: {signal.get('tp')}")
    print(f"SL: {signal.get('sl')}")
    print(f"Leverage: {signal.get('leverage')}x")
    print()

    print(f"DECISION: {trade_data.get('decision')}")
    print(f"Composite Score: {trade_data.get('composite_score')}")
    print(f"Rationale: {trade_data.get('rationale')}")
    print()

    metrics = trade_data.get('metrics', {})
    print(f"R:R Ratio: {metrics.get('rr_ratio')}")
    print()

    print("Agent Scores:")
    agent_reports = trade_data.get('agent_reports', {})
    for agent, report in agent_reports.items():
        score = report.get('score', 'N/A')
        reasoning = report.get('reasoning', report.get('reason', 'No reasoning'))[:80]
        print(f"  {agent.capitalize()}: {score} - {reasoning}...")
    print_separator()

def get_input(prompt: str, valid_options: Optional[list] = None) -> str:
    """Get user input with validation"""
    while True:
        value = input(prompt).strip()
        if not value:
            print("Input cannot be empty. Please try again.")
            continue
        if valid_options and value not in valid_options:
            print(f"Invalid option. Choose from: {', '.join(valid_options)}")
            continue
        return value

def get_int_input(prompt: str, min_val: int, max_val: int) -> int:
    """Get integer input with validation"""
    while True:
        try:
            value = int(input(prompt).strip())
            if min_val <= value <= max_val:
                return value
            print(f"Value must be between {min_val} and {max_val}")
        except ValueError:
            print("Please enter a valid number")

def get_float_input(prompt: str, min_val: float, max_val: float) -> float:
    """Get float input with validation"""
    while True:
        try:
            value = float(input(prompt).strip())
            if min_val <= value <= max_val:
                return value
            print(f"Value must be between {min_val} and {max_val}")
        except ValueError:
            print("Please enter a valid number")

def get_optional_input(prompt: str) -> Optional[str]:
    """Get optional input (can be empty)"""
    value = input(prompt).strip()
    return value if value else None

def collect_feedback_interactive(trade_id: str, collector: FeedbackCollector):
    """Interactive feedback collection"""
    trade_data = collector.get_trade_details(trade_id)
    if not trade_data:
        print(f"Error: Trade ID {trade_id} not found in audit logs")
        return

    print_trade_details(trade_data)

    print("\nPROVIDE FEEDBACK")
    print_separator()

    print("\n1. What was the actual outcome?")
    print("   1) SUCCESS - Trade executed and achieved target")
    print("   2) FAILURE - Trade executed but hit stop loss or failed")
    print("   3) PARTIAL_SUCCESS - Trade partially successful")
    print("   4) NOT_EXECUTED - Trade was not executed")
    print("   5) PENDING - Trade still in progress")

    outcome_map = {
        "1": "SUCCESS",
        "2": "FAILURE",
        "3": "PARTIAL_SUCCESS",
        "4": "NOT_EXECUTED",
        "5": "PENDING"
    }
    outcome_choice = get_input("Choose (1-5): ", list(outcome_map.keys()))
    actual_outcome = outcome_map[outcome_choice]

    outcome_reason = get_input("\n2. Why did this outcome occur? ")

    print("\n3. Was the system's decision correct?")
    was_correct = get_input("   (yes/no): ", ["yes", "no"]) == "yes"

    decision_quality = get_int_input("\n4. Rate the decision quality (1=Very Poor, 10=Excellent): ", 1, 10)

    what_went_right = get_optional_input("\n5. What went right? (optional, press Enter to skip): ")
    what_went_wrong = get_optional_input("\n6. What went wrong? (optional, press Enter to skip): ")

    print("\n7. Were there any missed factors? (comma-separated, press Enter to skip)")
    missed_input = get_optional_input("   Examples: liquidity, news event, whale activity\n   Factors: ")
    missed_factors = [f.strip() for f in missed_input.split(",")] if missed_input else None

    should_have_been = None
    if not was_correct:
        print("\n8. What should the decision have been?")
        print("   1) APPROVE  2) ADJUST  3) FLAG  4) REJECT")
        should_map = {"1": "APPROVE", "2": "ADJUST", "3": "FLAG", "4": "REJECT"}
        should_choice = get_input("   Choose (1-4): ", list(should_map.keys()))
        should_have_been = should_map[should_choice]

        reasoning_corrections = get_optional_input("\n9. What corrections to the reasoning? ")
    else:
        reasoning_corrections = None

    print("\n10. Rate each agent's accuracy (1-10, or press Enter to skip):")
    technical_score = None
    sentiment_score = None
    metrics_score = None
    volatility_score = None

    tech_input = get_optional_input("    Technical Agent (1-10): ")
    if tech_input:
        technical_score = int(tech_input)

    sent_input = get_optional_input("    Sentiment Agent (1-10): ")
    if sent_input:
        sentiment_score = int(sent_input)

    met_input = get_optional_input("    Metrics Agent (1-10): ")
    if met_input:
        metrics_score = int(met_input)

    vol_input = get_optional_input("    Volatility Agent (1-10): ")
    if vol_input:
        volatility_score = int(vol_input)

    print("\n11. Trade execution details (optional):")
    price_movement_input = get_optional_input("    Actual price movement % (e.g., 5.2 or -3.1): ")
    actual_price_movement = float(price_movement_input) if price_movement_input else None

    tp_hit_input = get_optional_input("    Did TP hit? (yes/no, press Enter to skip): ")
    tp_hit = tp_hit_input == "yes" if tp_hit_input else None

    sl_hit_input = get_optional_input("    Did SL hit? (yes/no, press Enter to skip): ")
    sl_hit = sl_hit_input == "yes" if sl_hit_input else None

    max_dd_input = get_optional_input("    Max drawdown % (e.g., 2.5): ")
    max_drawdown = float(max_dd_input) if max_dd_input else None

    max_profit_input = get_optional_input("    Max profit % (e.g., 8.3): ")
    max_profit = float(max_profit_input) if max_profit_input else None

    reward_signal = get_float_input("\n12. Overall reward signal (-1=Very Bad, 0=Neutral, 1=Very Good): ", -1.0, 1.0)
    confidence = get_float_input("\n13. Your confidence in this feedback (0.0-1.0): ", 0.0, 1.0)

    feedback_provider = get_input("\n14. Your name/ID: ")
    notes = get_optional_input("\n15. Additional notes (optional): ")

    feedback = TradeFeedback(
        trade_id=trade_id,
        actual_outcome=actual_outcome,
        outcome_reason=outcome_reason,
        was_decision_correct=was_correct,
        decision_quality_score=decision_quality,
        what_went_right=what_went_right,
        what_went_wrong=what_went_wrong,
        missed_factors=missed_factors,
        should_have_been=should_have_been,
        reasoning_corrections=reasoning_corrections,
        technical_agent_accuracy=technical_score,
        sentiment_agent_accuracy=sentiment_score,
        metrics_agent_accuracy=metrics_score,
        volatility_agent_accuracy=volatility_score,
        actual_price_movement=actual_price_movement,
        tp_hit=tp_hit,
        sl_hit=sl_hit,
        max_drawdown_percent=max_drawdown,
        max_profit_percent=max_profit,
        reward_signal=reward_signal,
        confidence=confidence,
        feedback_provider=feedback_provider,
        notes=notes
    )

    print("\n" + "=" * 80)
    print("FEEDBACK SUMMARY")
    print("=" * 80)
    print(f"Trade ID: {feedback.trade_id}")
    print(f"Outcome: {feedback.actual_outcome}")
    print(f"Decision Correct: {feedback.was_decision_correct}")
    print(f"Quality Score: {feedback.decision_quality_score}/10")
    print(f"Reward Signal: {feedback.reward_signal}")
    print("=" * 80)

    confirm = get_input("\nSubmit this feedback? (yes/no): ", ["yes", "no"])
    if confirm == "yes":
        result = collector.submit_feedback(feedback)
        print(f"\n✓ Feedback submitted successfully!")
        print(f"  Feedback ID: {result['feedback_id']}")
    else:
        print("\nFeedback cancelled.")

def list_recent_trades(collector: FeedbackCollector):
    """List recent trades for feedback"""
    trades = collector.list_recent_trades(20)
    if not trades:
        print("No trades found in audit logs.")
        return

    print_separator()
    print("RECENT TRADES (Last 20)")
    print_separator()
    print(f"{'Trade ID':<40} {'Asset':<10} {'Type':<6} {'Decision':<8} {'Score':<6} {'Time':<20}")
    print("-" * 80)

    for trade in trades:
        trade_id_short = trade['trade_id'][:36]
        asset = trade['asset'] or 'N/A'
        trade_type = trade['type'] or 'N/A'
        decision = trade['decision']
        score = trade['composite_score'] if trade['composite_score'] else 'N/A'
        timestamp = trade['timestamp'][:19] if trade['timestamp'] else 'N/A'

        print(f"{trade_id_short:<40} {asset:<10} {trade_type:<6} {decision:<8} {score:<6} {timestamp:<20}")

    print_separator()

def main():
    collector = FeedbackCollector()

    if len(sys.argv) > 1:
        trade_id = sys.argv[1]
        collect_feedback_interactive(trade_id, collector)
    else:
        print("\n" + "=" * 80)
        print("ARGUS RISK ANALYSIS - HUMAN FEEDBACK SYSTEM")
        print("=" * 80)
        print("\n1. View recent trades")
        print("2. Submit feedback for a trade")
        print("3. Exit")

        choice = get_input("\nChoose an option (1-3): ", ["1", "2", "3"])

        if choice == "1":
            list_recent_trades(collector)
            print("\nTo submit feedback, run:")
            print("  python feedback_cli.py <trade_id>")

        elif choice == "2":
            trade_id = get_input("Enter Trade ID: ")
            collect_feedback_interactive(trade_id, collector)

        else:
            print("Exiting...")

if __name__ == "__main__":
    main()
