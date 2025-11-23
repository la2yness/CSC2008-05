"""
Greedy Nearest-Next + 2-Opt Local Search 알고리즘
- Greedy Nearest-Next로 초기 경로 생성 후 2-opt 개선 수행
"""

from typing import List, Dict
from .alg_greedy_nearest import greedy_nearest_next


def calculate_edge_cost(
    node1: int,
    node2: int,
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator
) -> float:
    """
    두 노드 간의 간선 비용 계산

    Args:
        node1: 출발 노드
        node2: 도착 노드
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체

    Returns:
        간선 비용
    """
    move_time = travel_costs.get(node1, {}).get(node2, float('inf'))
    wait_time = wait_times.get(node2, 0.0)
    return weight_calculator.leg_cost(move_time, wait_time)


def calculate_swap_cost_delta(
    path: List[int],
    i: int,
    k: int,
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator
) -> float:
    """
    2-opt 스왑 시 비용 변화량을 정확하게 계산

    대기시간이 비대칭이므로 해당 구간의 모든 비용을 재계산해야 함

    Args:
        path: 현재 경로
        i: 첫 번째 구간 시작 인덱스
        k: 두 번째 구간 끝 인덱스
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체

    Returns:
        비용 변화량 (음수면 개선, 양수면 악화)
    """
    # 원래 경로: path[i] -> path[i+1] -> ... -> path[k] -> path[k+1]
    # 새 경로: path[i] -> path[k] -> ... -> path[i+1] -> path[k+1]
    #         (중간 구간 [i+1, k]가 뒤집힘)

    # 원래 구간 [i, k+1]의 비용 계산
    old_cost = 0.0
    for idx in range(i, k):
        old_cost += calculate_edge_cost(
            path[idx], path[idx + 1], travel_costs, wait_times, weight_calculator
        )
    if k + 1 < len(path):
        old_cost += calculate_edge_cost(
            path[k], path[k + 1], travel_costs, wait_times, weight_calculator
        )

    # 새 경로 생성 (임시)
    new_segment = path[:i+1] + path[i+1:k+1][::-1] + path[k+1:]

    # 새 구간 [i, k+1]의 비용 계산
    new_cost = 0.0
    for idx in range(i, k):
        new_cost += calculate_edge_cost(
            new_segment[idx], new_segment[idx + 1], travel_costs, wait_times, weight_calculator
        )
    if k + 1 < len(new_segment):
        new_cost += calculate_edge_cost(
            new_segment[k], new_segment[k + 1], travel_costs, wait_times, weight_calculator
        )

    return new_cost - old_cost


def two_opt_swap(path: List[int], i: int, k: int) -> List[int]:
    """
    2-opt 스왑: 경로의 [i+1, k] 구간을 뒤집기

    Args:
        path: 원본 경로
        i: 첫 번째 구간 시작 인덱스
        k: 두 번째 구간 끝 인덱스

    Returns:
        스왑된 새 경로
    """
    # path[0:i+1] + reversed(path[i+1:k+1]) + path[k+1:]
    new_path = path[:i+1] + path[i+1:k+1][::-1] + path[k+1:]
    return new_path


def two_opt_improve(
    path: List[int],
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator,
    max_iterations: int = 1000
) -> List[int]:
    """
    2-opt 개선 알고리즘

    경로의 두 간선을 선택하여 교차를 제거하면서 비용을 줄이는 방식

    Args:
        path: 초기 경로
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체
        max_iterations: 최대 반복 횟수

    Returns:
        개선된 경로
    """
    if len(path) <= 2:
        return path

    improved = True
    current_path = path[:]
    iteration = 0

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        # 모든 가능한 2-opt 스왑 시도
        for i in range(len(current_path) - 2):
            for k in range(i + 2, len(current_path)):
                # 비용 변화량만 계산
                cost_delta = calculate_swap_cost_delta(
                    current_path, i, k, travel_costs, wait_times, weight_calculator
                )

                # 비용이 개선되면 적용 (부동소수점 오차 고려)
                if cost_delta < -1e-9:
                    current_path = two_opt_swap(current_path, i, k)
                    improved = True
                    break

            if improved:
                break

    return current_path


def greedy_nearest_with_2opt(
    start_node: int,
    target_nodes: List[int],
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator,
    max_iterations: int = 1000
) -> List[int]:
    """
    Greedy Nearest-Next + 2-Opt 알고리즘

    1. Greedy Nearest-Next로 초기 경로 생성
    2. 2-opt 개선 수행

    Args:
        start_node: 시작 노드 ID
        target_nodes: 방문해야 할 노드 ID 리스트
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체
        max_iterations: 2-opt 최대 반복 횟수

    Returns:
        개선된 방문 순서
    """
    # 1. Greedy Nearest-Next로 초기 경로 생성
    initial_path = greedy_nearest_next(
        start_node,
        target_nodes,
        travel_costs,
        wait_times,
        weight_calculator
    )

    # 2. 2-opt 개선
    improved_path = two_opt_improve(
        initial_path,
        travel_costs,
        wait_times,
        weight_calculator,
        max_iterations
    )

    return improved_path
