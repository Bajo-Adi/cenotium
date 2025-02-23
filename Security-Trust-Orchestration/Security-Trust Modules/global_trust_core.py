from typing import List, Dict
import numpy as np
from datetime import datetime, timedelta
class GlobalTrustCore:
    """
    Manages global trust scores and rankings for the agent network.
    
    Implements modified EigenTrust algorithm with temporal decay and performance metrics
    for calculating trust and rank scores across the agent network.
    
    Attributes:
        storage: Persistent storage instance
        alpha (float): PageRank damping factor
        trust_threshold (float): Minimum trust score threshold
        max_iterations (int): Maximum power iteration steps
        time_decay_factor (float): Decay rate for old transactions
    """
    
    def calculate_trust_score(self, agent_id: str, 
                            transaction_history: List[dict]) -> float:
        """
        Calculates trust score using modified EigenTrust algorithm with temporal decay.
        
        Combines local trust (based on direct interactions) with global trust (based on
        network reputation) using PageRank-like algorithm.
        
        Args:
            agent_id (str): Agent identifier
            transaction_history (List[dict]): List of historical transactions
                Each transaction should have:
                - 'success' (bool): Transaction success
                - 'timestamp' (datetime): When it occurred
                - 'partner_id' (str): Other agent involved
                
        Returns:
            float: Calculated trust score between 0 and 1
            
        Notes:
            Uses temporal decay to give more weight to recent transactions
        """
        if not transaction_history:
            return 0.0

        weighted_transactions = self._apply_time_decay(transaction_history)
        
        # Calculate local and global trust
        successful = sum(t['weight'] for t in weighted_transactions if t['success'])
        total_weight = sum(t['weight'] for t in weighted_transactions)
        
        local_trust = successful / total_weight if total_weight > 0 else 0
        
        neighbor_scores = []
        for transaction in weighted_transactions:
            partner_score = self.storage.get_trust_score(transaction['partner_id'])
            neighbor_scores.append(partner_score * transaction['weight'])
        
        if not neighbor_scores:
            return local_trust
            
        global_trust = sum(neighbor_scores) / total_weight
        
        final_trust = self.alpha * local_trust + (1 - self.alpha) * global_trust
        return max(0.0, min(1.0, final_trust))

    def _apply_time_decay(self, transactions: List[dict]) -> List[dict]:
        """
        Applies temporal decay to transaction weights.
        
        Args:
            transactions (List[dict]): List of transactions with timestamps
            
        Returns:
            List[dict]: Transactions with added weight field based on age
            
        Notes:
            Uses exponential decay based on transaction age
        """
        now = datetime.now()
        weighted_transactions = []
        
        for transaction in transactions:
            age = now - transaction['timestamp']
            weight = self.time_decay_factor ** (age.days + age.seconds/86400)
            weighted_transactions.append({**transaction, 'weight': weight})
            
        return weighted_transactions

    def calculate_rank(self, agent_id: str, trust_score: float, 
                      performance_metrics: dict) -> float:
        """
        Calculates agent ranking based on multiple factors.
        
        Args:
            agent_id (str): Agent identifier
            trust_score (float): Agent's trust score
            performance_metrics (dict): Dictionary containing:
                - 'avg_response_time' (float): Average response time
                - 'success_rate' (float): Success rate of operations
                - 'complexity_score' (float): Optional complexity handling score
                
        Returns:
            float: Calculated rank between 0 and 1
            
        Notes:
            Combines multiple metrics with different weights for final ranking
        """
        weights = {
            'response_time': 0.2,
            'success_rate': 0.3,
            'trust_score': 0.3,
            'complexity_handling': 0.2
        }
        
        normalized_metrics = {
            'response_time': 1.0 / (1.0 + performance_metrics['avg_response_time']),
            'success_rate': performance_metrics['success_rate'],
            'trust_score': trust_score,
            'complexity_handling': performance_metrics.get('complexity_score', 0.5)
        }
        
        rank = sum(weights[k] * normalized_metrics[k] for k in weights)
        return rank

    def update_trust_network(self, agents: Dict[str, float]):
        """
        Updates trust scores for the entire network using power iteration.
        
        Args:
            agents (Dict[str, float]): Current agent trust scores
            
        Returns:
            Dict[str, float]: Updated trust scores for all agents
            
        Notes:
            Implements network-wide trust update using matrix operations
            Continues until convergence or max_iterations reached
        """
        n = len(agents)
        if n == 0:
            return {}

        trust_matrix = np.zeros((n, n))
        agent_ids = list(agents.keys())
        
        # Build and normalize trust matrix
        for i, agent_id in enumerate(agent_ids):
            for j, other_id in enumerate(agent_ids):
                if i != j:
                    trust_matrix[i][j] = self.storage.get_trust_score(other_id)
        
        row_sums = trust_matrix.sum(axis=1)
        trust_matrix = np.divide(trust_matrix, row_sums[:, np.newaxis], 
                               where=row_sums[:, np.newaxis] != 0)
        
        # Power iteration for convergence
        trust_vector = np.ones(n) / n
        for _ in range(self.max_iterations):
            new_trust = trust_matrix.T @ trust_vector
            if np.allclose(trust_vector, new_trust):
                break
            trust_vector = new_trust
        
        return {
            agent_id: float(trust_vector[i])
            for i, agent_id in enumerate
        }