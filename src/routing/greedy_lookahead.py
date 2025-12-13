"""
Greedy Nearest-Next + Lookahead 알고리즘
- 현재 선택의 즉각적인 비용뿐만 아니라 다음 단계의 예상 비용까지 고려하는 그리디 알고리즘
"""

from typing import List, Dict, Set


def calculate_lookahead_score(
    current: int,
    candidate: int,
    remaining: Set[int],
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator,
    lookahead_depth: int = 2
) -> float:
    """
    Lookahead 점수 계산

    현재 노드에서 candidate 노드를 선택했을 때의 비용 +
    candidate에서 남은 노드들까지의 평균 비용을 lookahead_depth만큼 고려

    Args:
        current: 현재 노드 ID
        candidate: 평가할 후보 노드 ID
        remaining: 남은 미방문 노드 집합
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체
        lookahead_depth: 몇 단계 앞까지 볼 것인지

    Returns:
        총 예상 비용 (현재 비용 + lookahead 평균 비용)
    """
    # 현재 -> candidate 비용
    move_time = travel_costs.get(current, {}).get(candidate, float('inf'))
    wait_time = wait_times.get(candidate, 0.0)
    immediate_cost = weight_calculator.leg_cost(move_time, wait_time)

    if immediate_cost == float('inf'):
        return float('inf')

    # Lookahead: candidate를 선택한 후 남은 노드들로의 평균 비용
    lookahead_cost = 0.0
    remaining_after_candidate = remaining - {candidate}

    if not remaining_after_candidate or lookahead_depth <= 0:
        return immediate_cost

    # candidate에서 남은 노드들까지의 비용 계산
    costs_from_candidate = []
    for next_node in remaining_after_candidate:
        next_move_time = travel_costs.get(candidate, {}).get(next_node, float('inf'))
        next_wait_time = wait_times.get(next_node, 0.0)
        next_cost = weight_calculator.leg_cost(next_move_time, next_wait_time)

        if next_cost != float('inf'):
            costs_from_candidate.append(next_cost)

    # 평균 비용 계산
    if costs_from_candidate:
        avg_cost = sum(costs_from_candidate) / len(costs_from_candidate)
        # lookahead depth만큼 가중치 감소
        lookahead_weight = 0.5 ** lookahead_depth
        lookahead_cost = avg_cost * lookahead_weight

    return immediate_cost + lookahead_cost


def greedy_lookahead(
    start_node: int,
    target_nodes: List[int],
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator,
    lookahead_depth: int = 2
) -> List[int]:
    """
    Greedy Nearest-Next + Lookahead 알고리즘

    현재 위치에서 아직 방문하지 않은 노드 중
    즉각적인 비용 + lookahead 예상 비용이 최소인 노드를 다음 방문지로 선택

    Args:
        start_node: 시작 노드 ID
        target_nodes: 방문해야 할 노드 ID 리스트
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체
        lookahead_depth: 몇 단계 앞까지 볼 것인지 (기본값: 2)

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
        best_score = float('inf')

        # 미방문 노드 중 lookahead 점수가 가장 낮은 노드 찾기
        for candidate in unvisited:
            score = calculate_lookahead_score(
                current,
                candidate,
                unvisited,
                travel_costs,
                wait_times,
                weight_calculator,
                lookahead_depth
            )

            if score < best_score:
                best_score = score
                best_next = candidate

        # 다음 노드가 없으면 (도달 불가능한 경우) 중단
        if best_next is None:
            print(f"  Warning: Cannot reach {len(unvisited)} node(s) from current position")
            print(f"  Unreachable nodes: {sorted(unvisited)}")
            break

        # 다음 노드 방문
        path.append(best_next)
        unvisited.remove(best_next)
        current = best_next

    return path
