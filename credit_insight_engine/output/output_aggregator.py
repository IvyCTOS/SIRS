from datetime import datetime
from typing import Dict, List, Any
import logging
from collections import defaultdict

class ConsoleOutputAggregator:
    def __init__(self):
        """Initialize aggregator with configuration"""
        self.insights = []
        
        # Set up logging
        logging.basicConfig(
            filename=f'logs/aggregator_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

    def add_insight(self, insight: Dict[str, Any]) -> None:
        """Add a single insight to the collection"""
        if not isinstance(insight, dict):
            raise ValueError("Insight must be a dictionary")
        
        # Add metadata
        insight['timestamp'] = datetime.now().isoformat()
        if 'severity' not in insight:
            insight['severity'] = 'medium'
            
        self.insights.append(insight)
        self.logger.info(f"Added insight: {insight['label']}")

    def group_insights(self, grouping_key: str = 'label') -> Dict[str, List[Dict]]:
        """Group insights by specified key"""
        grouped = defaultdict(list)
        for insight in self.insights:
            key = insight.get(grouping_key, 'other')
            grouped[key].append(insight)
        return grouped

    def _sort_insights(self, insights: List[Dict]) -> List[Dict]:
        """Sort insights by severity and timestamp"""
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        return sorted(
            insights,
            key=lambda x: (severity_order.get(x.get('severity', 'low'), 3), x.get('timestamp', ''))
        )

    def print_report(self) -> None:
        """Print formatted report to console"""
        if not self.insights:
            print("No insights to display")
            return

        print("\n=== Credit Behavior Insight Report ===")
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Insights: {len(self.insights)}\n")

        grouped_insights = self.group_insights()
        for label, insights in grouped_insights.items():
            print(f"\n{label}")
            print("=" * len(label))
            
            sorted_insights = self._sort_insights(insights)
            for insight in sorted_insights:
                print(f"\n▶ {insight['type']}")
                print(f"  {insight['message']}")
                if 'recommendation' in insight:
                    print(f"  📝 {insight['recommendation']}")
                print(f"  Severity: {insight['severity']}")

def main():
    # Example usage
    aggregator = ConsoleOutputAggregator()

    # Add sample insights
    sample_insights = [
        {
            'label': '🔴 High Utilization',
            'type': 'Revolving Credit Overuse',
            'message': 'Credit card utilization at 85%',
            'recommendation': 'Consider paying down balance to improve credit score',
            'severity': 'high'
        },
        {
            'label': '🟠 Missed Payments',
            'type': 'Payment Delinquency',
            'message': 'Missed payment on personal loan',
            'recommendation': 'Contact lender to arrange payment plan',
            'severity': 'high'
        },
        {
            'label': '🟡 Frequent Applications',
            'type': 'Multiple Credit Inquiries',
            'message': '3 credit applications in the last 30 days',
            'recommendation': 'Limit new credit applications to avoid score impact',
            'severity': 'medium'
        }
    ]

    for insight in sample_insights:
        aggregator.add_insight(insight)

    # Print report to console
    aggregator.print_report()

if __name__ == "__main__":
    main()