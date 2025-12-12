"""
Greedy Nearest-Next 알고리즘
- 현재 위치에서 가장 비용이 적은 미방문 노드를 선택하는 그리디 알고리즘
"""

from typing import List, Dict, Set


def greedy_nearest_next(
    start_node: int,
    target_nodes: List[int],
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator
) -> List[int]:
    """
    Greedy Nearest-Next 알고리즘

    현재 위치에서 아직 방문하지 않은 노드 중
    leg_cost(current, candidate)가 최소인 노드를 다음 방문지로 선택

    Args:
        start_node: 시작 노드 ID
        target_nodes: 방문해야 할 노드 ID 리스트
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체

    Returns:
        방문 순서 (시작 노드 포함)
    """
    if not target_nodes:
        return [start_node]

    # 방문해야 할 노드 집합 (시작 노드 제외)
    unvisited = set(target_nodes)
    if start_node in unvisited:
        unvisited.remove(start_node)

    # 경로 초기화
    path = [start_node]
    current = start_node

    # 모든 노드를 방문할 때까지 반복
    while unvisited:
        best_next = None
        best_cost = float('inf')

        # 미방문 노드 중 가장 비용이 적은 노드 찾기
        for candidate in unvisited:
            # 이동 시간
            if current in travel_costs and candidate in travel_costs[current]:
                move_time = travel_costs[current][candidate]
            else:
                move_time = float('inf')

            # 대기 시간
            wait_time = wait_times.get(candidate, 0.0)

            # 구간 비용 계산
            cost = weight_calculator.leg_cost(move_time, wait_time)

            if cost < best_cost:
                best_cost = cost
                best_next = candidate

        # 다음 노드가 없으면 (도달 불가능한 경우) 중단
        if best_next is None:
            # 방문하지 못한 노드가 있음을 경고
            print(f"  Warning: Cannot reach {len(unvisited)} node(s) from current position")
            print(f"  Unreachable nodes: {sorted(unvisited)}")
            break

        # 다음 노드 방문
        path.append(best_next)
        unvisited.remove(best_next)
        current = best_next

    return path
