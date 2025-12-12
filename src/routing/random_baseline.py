"""
Random Baseline 알고리즘
- 무작위 순열 기반 경로 생성
- 다른 알고리즘들의 성능 비교를 위한 기준선
"""

import random
from typing import List, Dict


def random_baseline(
    start_node: int,
    target_nodes: List[int],
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator,
    seed: int = None
) -> List[int]:
    """
    Random Baseline 알고리즘

    시작 노드를 제외한 나머지 노드들을 무작위로 섞어서 경로 생성

    Args:
        start_node: 시작 노드 ID
        target_nodes: 방문해야 할 노드 ID 리스트
        travel_costs: 미리 계산된 이동 시간 딕셔너리 (사용하지 않음)
        wait_times: 각 노드의 대기 시간 딕셔너리 (사용하지 않음)
        weight_calculator: WeightCalculator 객체 (사용하지 않음)
        seed: 난수 생성 시드 (재현성을 위해)

    Returns:
        무작위 방문 순서
    """
    if not target_nodes:
        return [start_node]

    # 시드 설정
    if seed is not None:
        random.seed(seed)

    # 방문해야 할 노드 리스트 (시작 노드 제외)
    remaining_nodes = [node for node in target_nodes if node != start_node]

    # 무작위로 섞기
    random.shuffle(remaining_nodes)

    # 시작 노드 + 무작위 순서
    path = [start_node] + remaining_nodes

    return path
