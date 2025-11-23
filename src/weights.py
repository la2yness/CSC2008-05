"""
가중치 계산 함수들
- 이동 비용과 대기 시간을 고려한 가중치 수식 구현
"""

from typing import Dict


class WeightCalculator:

    def __init__(self, alpha: float = 1.0, beta: float = 1.0):
        """
        Args:
            alpha: 이동 시간 가중치 계수
            beta: 대기 시간 가중치 계수
        """
        self.alpha = alpha
        self.beta = beta

    def edge_cost(self, move_time: float, wait_time: float) -> float:
        """
        단일 구간(u → v)의 비용 계산

        cost(u → v) = α * move_time(u, v) + β * wait_time(v)

        Args:
            move_time: u에서 v로의 이동 시간
            wait_time: v에서의 대기 시간

        Returns:
            구간 비용
        """
        return self.alpha * move_time + self.beta * wait_time

    def leg_cost(self, travel_cost: float, wait_time: float) -> float:
        """
        두 어트랙션 간의 구간 비용 계산
        (미리 계산된 최단 이동 시간 사용)

        leg_cost(i, j) = α * travel_cost[i][j] + β * wait_time[j]

        Args:
            travel_cost: i에서 j로의 최소 이동 시간
            wait_time: j에서의 대기 시간

        Returns:
            구간 비용
        """
        return self.alpha * travel_cost + self.beta * wait_time

    def path_cost(self, path: list, travel_costs: Dict, wait_times: Dict) -> float:
        """
        전체 경로의 총 비용 계산

        total_cost(P) = Σ cost(vi → v{i+1})

        Args:
            path: 노드 ID들의 순서 리스트
            travel_costs: travel_costs[i][j] = i에서 j로의 최소 이동 시간
            wait_times: wait_times[node_id] = 노드의 대기 시간

        Returns:
            경로의 총 비용
        """
        if len(path) <= 1:
            return 0.0

        total = 0.0
        for i in range(len(path) - 1):
            curr = path[i]
            next_node = path[i + 1]

            # 이동 시간 가져오기
            if curr in travel_costs and next_node in travel_costs[curr]:
                move_time = travel_costs[curr][next_node]
            else:
                # 경로가 없는 경우 무한대 비용
                return float('inf')

            # 대기 시간 가져오기
            wait_time = wait_times.get(next_node, 0.0)

            # 구간 비용 누적
            total += self.leg_cost(move_time, wait_time)

        return total

    def calculate_metrics(
        self,
        path: list,
        travel_costs: Dict,
        wait_times: Dict
    ) -> Dict[str, float]:
        """
        경로의 상세 메트릭 계산

        Args:
            path: 노드 ID들의 순서 리스트
            travel_costs: 이동 시간 딕셔너리
            wait_times: 대기 시간 딕셔너리

        Returns:
            메트릭 딕셔너리 (total_cost, total_move_time, total_wait_time)
        """
        if len(path) <= 1:
            return {
                "total_cost": 0.0,
                "total_move_time": 0.0,
                "total_wait_time": 0.0
            }

        total_move = 0.0
        total_wait = 0.0

        for i in range(len(path) - 1):
            curr = path[i]
            next_node = path[i + 1]

            if curr in travel_costs and next_node in travel_costs[curr]:
                move_time = travel_costs[curr][next_node]
            else:
                return {
                    "total_cost": float('inf'),
                    "total_move_time": float('inf'),
                    "total_wait_time": float('inf')
                }

            wait_time = wait_times.get(next_node, 0.0)

            total_move += move_time
            total_wait += wait_time

        total_cost = self.alpha * total_move + self.beta * total_wait

        return {
            "total_cost": total_cost,
            "total_move_time": total_move,
            "total_wait_time": total_wait
        }

    def __repr__(self):
        return f"WeightCalculator(alpha={self.alpha}, beta={self.beta})"
