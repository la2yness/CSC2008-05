"""
MILP (Mixed Integer Linear Programming) 최적화 알고리즘
- TSP를 정수 계획법으로 정확하게 해결하는 알고리즘
"""

from typing import List, Dict
import pulp


def milp_tsp(
    start_node: int,
    target_nodes: List[int],
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator,
    time_limit: int = 60
) -> List[int]:
    """
    MILP를 사용한 TSP 최적 경로 탐색

    MTZ (Miller-Tucker-Zemlin) formulation을 사용하여 subtour elimination 수행

    Args:
        start_node: 시작 노드 ID
        target_nodes: 방문해야 할 노드 ID 리스트
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체
        time_limit: 최적화 시간 제한 (초)

    Returns:
        최적 방문 순서 (시작 노드 포함)
    """
    if not target_nodes:
        return [start_node]

    # 모든 노드 리스트 (시작 노드 포함)
    all_nodes = [start_node] + [n for n in target_nodes if n != start_node]
    n = len(all_nodes)

    if n == 1:
        return [start_node]

    # 노드 인덱스 매핑
    node_to_idx = {node: idx for idx, node in enumerate(all_nodes)}
    idx_to_node = {idx: node for idx, node in enumerate(all_nodes)}

    # 비용 행렬 생성
    cost_matrix = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                cost_matrix[(i, j)] = float('inf')
            else:
                node_i = idx_to_node[i]
                node_j = idx_to_node[j]
                move_time = travel_costs.get(node_i, {}).get(node_j, float('inf'))
                wait_time = wait_times.get(node_j, 0.0)
                cost_matrix[(i, j)] = weight_calculator.leg_cost(move_time, wait_time)

    # MILP 문제 생성
    prob = pulp.LpProblem("TSP", pulp.LpMinimize)

    # 변수 정의
    # x[i][j] = 1 if 간선 (i, j)를 사용, 0 otherwise
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j and cost_matrix[(i, j)] != float('inf'):
                x[(i, j)] = pulp.LpVariable(f"x_{i}_{j}", cat='Binary')

    # u[i] = 노드 i의 방문 순서 (subtour elimination용)
    u = {}
    for i in range(1, n):  # 시작 노드(0)는 제외
        u[i] = pulp.LpVariable(f"u_{i}", lowBound=1, upBound=n-1, cat='Integer')

    # 목적 함수: 총 비용 최소화
    prob += pulp.lpSum(cost_matrix[(i, j)] * x[(i, j)] for (i, j) in x.keys())

    # 제약조건 1: 각 노드에서 정확히 하나의 간선이 나감
    for i in range(n):
        outgoing_edges = [x[(i, j)] for j in range(n) if (i, j) in x]
        if outgoing_edges:
            prob += pulp.lpSum(outgoing_edges) == 1

    # 제약조건 2: 각 노드로 정확히 하나의 간선이 들어옴
    for j in range(n):
        incoming_edges = [x[(i, j)] for i in range(n) if (i, j) in x]
        if incoming_edges:
            prob += pulp.lpSum(incoming_edges) == 1

    # 제약조건 3: Subtour elimination (MTZ formulation)
    for i in range(1, n):
        for j in range(1, n):
            if i != j and (i, j) in x:
                prob += u[i] - u[j] + n * x[(i, j)] <= n - 1

    # 최적화 실행
    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit)
    prob.solve(solver)

    # 결과 확인
    status = pulp.LpStatus[prob.status]
    if status not in ['Optimal', 'Feasible']:
        return [start_node]

    # 경로 복원
    path = [0]  # 시작 노드 인덱스
    current_idx = 0

    for _ in range(n - 1):
        next_idx = None
        for j in range(n):
            if (current_idx, j) in x and pulp.value(x[(current_idx, j)]) > 0.5:
                next_idx = j
                break

        if next_idx is None:
            break

        path.append(next_idx)
        current_idx = next_idx

    # 인덱스를 실제 노드 ID로 변환
    node_path = [idx_to_node[idx] for idx in path]

    return node_path
