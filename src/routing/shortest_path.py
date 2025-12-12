"""
구간 최단 경로 계산
- Dijkstra 알고리즘을 사용하여 모든 노드 쌍 간의 최소 이동 시간을 미리 계산
"""

import heapq
from typing import Dict, List, Tuple


def dijkstra(graph, source: int) -> Dict[int, float]:
    """
    Dijkstra 알고리즘을 사용한 단일 출발점 최단 경로

    Args:
        graph: Graph 객체
        source: 출발 노드 ID

    Returns:
        dist: dist[node_id] = source에서 node_id까지의 최소 이동 시간
    """
    dist = {i: float('inf') for i in range(graph.num_nodes)}
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
                heapq.heappush(pq, (new_dist, v))

    return dist


def compute_all_pairs_shortest_paths(graph, usable_nodes: List[int] = None) -> Dict[int, Dict[int, float]]:
    """
    모든 노드 쌍 간의 최단 경로 계산

    각 노드에 대해 Dijkstra를 실행하여 모든 쌍의 최소 이동 시간을 계산

    Args:
        graph: Graph 객체
        usable_nodes: 사용 가능한 노드 ID 리스트 (None이면 모든 노드)

    Returns:
        travel_costs: travel_costs[i][j] = i에서 j로의 최소 이동 시간
    """
    travel_costs = {}

    # usable_nodes가 지정되지 않으면 모든 노드에 대해 계산
    if usable_nodes is None:
        nodes_to_compute = [i for i in range(graph.num_nodes)
                           if i < len(graph.nodes) and graph.nodes[i] is not None]
    else:
        # usable_nodes만 계산
        nodes_to_compute = usable_nodes

    for node_id in nodes_to_compute:
        # 노드가 존재하지 않으면 스킵
        if node_id >= len(graph.nodes) or graph.nodes[node_id] is None:
            continue

        dist = dijkstra(graph, node_id)
        travel_costs[node_id] = dist

    return travel_costs


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
