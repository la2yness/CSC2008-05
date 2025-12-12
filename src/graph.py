"""
그래프 모델 구현
- 노드: 어트랙션 및 편의시설
- 간선: 이동 경로 및 이동 시간
"""

from typing import List, Dict, Tuple, Optional, Union


class Node:

    def __init__(
        self,
        node_id: int,
        node_type: str,
        name: str = "",
        wait_time: float = 0.0,
        min_height: Optional[float] = None,
        max_height: Optional[float] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None
    ):
        """
        Args:
            node_id: 노드 고유 ID (0부터 시작)
            node_type: 노드 타입 (attraction, entrance, restaurant, restroom 등)
            name: 노드 이름
            wait_time: 대기 시간 (분)
            min_height: 최소 키 제한 (cm)
            max_height: 최대 키 제한 (cm)
            min_age: 최소 나이 제한
            max_age: 최대 나이 제한
        """
        self.id = node_id
        self.node_type = node_type
        self.name = name if name else f"Node_{node_id}"
        self.wait_time = wait_time
        self.min_height = min_height
        self.max_height = max_height
        self.min_age = min_age
        self.max_age = max_age

    def is_usable(self, user_profile: Dict) -> bool:
        """
        사용자 프로필에 따라 이 노드를 사용할 수 있는지 확인

        Args:
            user_profile: {"age": int, "height": float} 형태의 딕셔너리

        Returns:
            사용 가능하면 True, 아니면 False
        """
        age = user_profile.get("age")
        height = user_profile.get("height")

        # 나이 제약 체크
        if age is not None:
            if self.min_age is not None and age < self.min_age:
                return False
            if self.max_age is not None and age > self.max_age:
                return False

        # 키 제약 체크
        if height is not None:
            if self.min_height is not None and height < self.min_height:
                return False
            if self.max_height is not None and height > self.max_height:
                return False

        return True

    def __repr__(self):
        return f"Node({self.id}, {self.name}, type={self.node_type})"


class Graph:

    def __init__(self, num_nodes: int):
        """
        Args:
            num_nodes: 노드 개수
        """
        self.num_nodes = num_nodes
        self.nodes: List[Optional[Node]] = []
        # 인접 리스트: adj[u] = [(v, move_time), ...]
        self.adj: List[List[Tuple[int, float]]] = [[] for _ in range(num_nodes)]

    def add_node(self, node: Node):
        """노드 추가"""
        if node.id >= self.num_nodes:
            raise ValueError(f"Node ID {node.id} exceeds graph size {self.num_nodes}")

        # 노드 리스트 확장
        while len(self.nodes) <= node.id:
            self.nodes.append(None)

        self.nodes[node.id] = node

    def add_edge(self, u: int, v: int, move_time: float):
        """
        단방향 간선 추가

        Args:
            u: 시작 노드 ID
            v: 도착 노드 ID
            move_time: 이동 시간 (분)
        """
        if u >= self.num_nodes or v >= self.num_nodes:
            raise ValueError(f"Node ID out of range: {u} or {v}")

        if move_time < 0:
            raise ValueError(f"Move time must be non-negative: {move_time}")

        self.adj[u].append((v, move_time))

    def add_undirected_edge(self, u: int, v: int, move_time: float):
        """
        무방향 간선 추가

        Args:
            u: 노드 ID 1
            v: 노드 ID 2
            move_time: 이동 시간 (분)
        """
        self.add_edge(u, v, move_time)
        self.add_edge(v, u, move_time)

    def get_node(self, node_id: int) -> Node:
        """노드 ID로 노드 객체 가져오기"""
        if node_id >= len(self.nodes) or self.nodes[node_id] is None:
            raise ValueError(f"Node {node_id} not found")
        return self.nodes[node_id]

    def get_neighbors(self, node_id: int) -> List[Tuple[int, float]]:
        """노드의 이웃 노드들과 이동 시간 반환"""
        if node_id >= self.num_nodes:
            raise ValueError(f"Node ID out of range: {node_id}")
        return self.adj[node_id]

    def filter_usable_nodes(
        self,
        user_profile: Dict,
        desired_set: Optional[List[int]] = None
    ) -> List[int]:
        """
        사용자 프로필과 원하는 어트랙션 리스트를 기반으로 사용 가능한 노드 필터링

        Args:
            user_profile: 사용자 프로필
            desired_set: 원하는 노드 ID 리스트 (None이면 모든 노드)

        Returns:
            사용 가능한 노드 ID 리스트
        """
        usable = []

        for node in self.nodes:
            if node is None:
                continue

            # 사용자 제약조건 체크
            if not node.is_usable(user_profile):
                continue

            # desired_set에 포함되어 있는지 체크
            if desired_set is not None and node.id not in desired_set:
                continue

            usable.append(node.id)

        return usable

    def __repr__(self):
        return f"Graph(nodes={self.num_nodes}, edges={sum(len(adj) for adj in self.adj) // 2})"
