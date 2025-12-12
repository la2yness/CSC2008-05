"""
Cheapest Insertion Heuristic 알고리즘
- 아직 포함되지 않은 노드를 경로 중 가장 비용 증가가 작은 위치에 삽입
"""

from typing import List, Dict


def cheapest_insertion(
    start_node: int,
    target_nodes: List[int],
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator
) -> List[int]:
    """
    Cheapest Insertion Heuristic 알고리즘

    1. 시작 노드로 초기 경로 구성
    2. 아직 포함되지 않은 노드를 경로 중 가장 비용 증가가 작은 위치에 삽입
    3. 모든 노드가 포함될 때까지 반복

    Args:
        start_node: 시작 노드 ID
        target_nodes: 방문해야 할 노드 ID 리스트
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체

    Returns:
        방문 순서
    """
    if not target_nodes:
        return [start_node]

    # 방문해야 할 노드 집합 (시작 노드 제외)
    unvisited = set(target_nodes)
    if start_node in unvisited:
        unvisited.remove(start_node)

    # 초기 경로는 시작 노드만 포함
    path = [start_node]

    # 모든 노드를 삽입할 때까지 반복
    while unvisited:
        best_node = None
        best_position = None
        best_cost_increase = float('inf')

        # 각 미방문 노드에 대해
        for node in unvisited:
            # 경로의 각 위치에 삽입 시도
            for position in range(1, len(path) + 1):
                # position 위치에 node를 삽입했을 때의 비용 증가 계산
                cost_increase = calculate_insertion_cost(
                    path,
                    node,
                    position,
                    travel_costs,
                    wait_times,
                    weight_calculator
                )

                # 가장 비용 증가가 작은 (node, position) 선택
                if cost_increase < best_cost_increase:
                    best_cost_increase = cost_increase
                    best_node = node
                    best_position = position

        # 선택된 위치에 노드 삽입
        if best_node is not None:
            path.insert(best_position, best_node)
            unvisited.remove(best_node)
        else:
            # 더 이상 삽입할 수 없으면 중단
            print(f"  Warning: Cannot insert {len(unvisited)} node(s) into the path")
            print(f"  Unreachable nodes: {sorted(unvisited)}")
            break

    return path


def calculate_insertion_cost(
    path: List[int],
    node: int,
    position: int,
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator
) -> float:
    """
    특정 위치에 노드를 삽입했을 때의 비용 증가 계산

    Args:
        path: 현재 경로
        node: 삽입할 노드 ID
        position: 삽입 위치 (1-based index)
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체

    Returns:
        비용 증가량
    """
    # 경로가 비어있거나 끝에 추가하는 경우
    if position == 0:
        position = 1
    if position > len(path):
        position = len(path)

    # 삽입 전 비용
    if position == len(path):
        # 경로 끝에 추가
        if len(path) > 0:
            prev_node = path[position - 1]
            # prev -> node 비용
            move_time = travel_costs.get(prev_node, {}).get(node, float('inf'))
            wait_time = wait_times.get(node, 0.0)
            cost_increase = weight_calculator.leg_cost(move_time, wait_time)
        else:
            cost_increase = 0.0
    else:
        # 중간에 삽입
        prev_node = path[position - 1]
        next_node = path[position]

        # 원래 비용: prev -> next
        move_time_old = travel_costs.get(prev_node, {}).get(next_node, float('inf'))
        wait_time_old = wait_times.get(next_node, 0.0)
        cost_old = weight_calculator.leg_cost(move_time_old, wait_time_old)

        # 새 비용: prev -> node -> next
        # prev -> node
        move_time_1 = travel_costs.get(prev_node, {}).get(node, float('inf'))
        wait_time_1 = wait_times.get(node, 0.0)
        cost_1 = weight_calculator.leg_cost(move_time_1, wait_time_1)

        # node -> next
        move_time_2 = travel_costs.get(node, {}).get(next_node, float('inf'))
        wait_time_2 = wait_times.get(next_node, 0.0)
        cost_2 = weight_calculator.leg_cost(move_time_2, wait_time_2)

        cost_new = cost_1 + cost_2

        # 비용 증가량
        cost_increase = cost_new - cost_old

    return cost_increase
