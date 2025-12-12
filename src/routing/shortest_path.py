"""
구간 최단 경로 계산
- Dijkstra 알고리즘을 사용하여 모든 노드 쌍 간의 최소 이동 시간을 미리 계산
"""

import heapq
from typing import Dict, List, Tuple


def dijkstra(graph, source: int) -> Tuple[Dict[int, float], Dict[int, int]]:
    """
    Dijkstra 알고리즘을 사용한 단일 출발점 최단 경로

    Args:
        graph: Graph 객체
        source: 출발 노드 ID

    Returns:
        dist: dist[node_id] = source에서 node_id까지의 최소 이동 시간
        pred: pred[node_id] = node_id로 가는 최단 경로의 이전 노드
    """
    dist = {i: float('inf') for i in range(graph.num_nodes)}
    pred = {i: None for i in range(graph.num_nodes)}
    dist[source] = 0.0

    # 우선순위 큐: (거리, 노드)
    pq = [(0.0, source)]

    while pq:
        current_dist, u = heapq.heappop(pq)

        # 이미 처리된 노드는 스킵
        if current_dist > dist[u]:
            continue

        # 이웃 노드 탐색
        for v, move_time in graph.get_neighbors(u):
            new_dist = current_dist + move_time

            if new_dist < dist[v]:
                dist[v] = new_dist
                pred[v] = u
                heapq.heappush(pq, (new_dist, v))

    return dist, pred


def reconstruct_path(pred: Dict[int, int], source: int, target: int) -> List[int]:
    """
    predecessor 정보로부터 실제 경로 재구성

    Args:
        pred: predecessor 딕셔너리 (dijkstra 결과)
        source: 출발 노드 ID
        target: 도착 노드 ID

    Returns:
        source에서 target까지의 전체 경로 (중간 노드 포함)
        경로가 없으면 빈 리스트 반환
    """
    if pred[target] is None and target != source:
        return []  # 경로 없음

    path = []
    current = target

    while current is not None:
        path.append(current)
        if current == source:
            break
        current = pred[current]

    path.reverse()
    return path


def compute_all_pairs_shortest_paths(graph, usable_nodes: List[int] = None) -> Tuple[Dict[int, Dict[int, float]], Dict[int, Dict[int, int]]]:
    """
    모든 노드 쌍 간의 최단 경로 계산

    각 노드에 대해 Dijkstra를 실행하여 모든 쌍의 최소 이동 시간과 경로를 계산

    Args:
        graph: Graph 객체
        usable_nodes: 사용 가능한 노드 ID 리스트 (None이면 모든 노드)

    Returns:
        travel_costs: travel_costs[i][j] = i에서 j로의 최소 이동 시간
        predecessors: predecessors[i][j] = i에서 j로 가는 최단 경로의 j 이전 노드
    """
    travel_costs = {}
    predecessors = {}

    # 모든 노드에 대해 계산 (중간 경유 노드 포함을 위해)
    all_nodes = [i for i in range(graph.num_nodes)
                 if i < len(graph.nodes) and graph.nodes[i] is not None]

    for node_id in all_nodes:
        dist, pred = dijkstra(graph, node_id)
        travel_costs[node_id] = dist
        predecessors[node_id] = pred

    return travel_costs, predecessors


def get_travel_cost(travel_costs: Dict[int, Dict[int, float]], i: int, j: int) -> float:
    """
    두 노드 간의 미리 계산된 이동 시간 가져오기

    Args:
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        i: 출발 노드 ID
        j: 도착 노드 ID

    Returns:
        i에서 j로의 최소 이동 시간 (경로가 없으면 inf)
    """
    if i not in travel_costs:
        return float('inf')
    return travel_costs[i].get(j, float('inf'))
