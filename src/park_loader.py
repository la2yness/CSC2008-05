"""
테마파크 그래프 로더
- JSON 데이터로부터 그래프 생성
- 실시간 대기시간 API 연동
"""

import json
import requests
import os
from typing import Dict, List, Optional, Tuple
from graph import Graph, Node

# 상수 정의
CLOSED_RIDE_WAIT_TIME = 999   # 운영 중단된 놀이기구 대기시간
DEFAULT_ATTRACTION_WAIT = 20  # 기본 어트랙션 대기시간 (분)
DEFAULT_RESTAURANT_WAIT = 40  # 기본 레스토랑 대기시간 (분)
DEFAULT_SHOW_WAIT = 20        # 기본 공연 대기시간 (분)
API_TIMEOUT = 3               # API 타임아웃 (초)

# API 이름 매핑 (영문 -> ID)
NAME_TO_ID = {
    "T Express": 157,
    "Amazon Express": 206,
    "Lost Valley": 207,
    "Rolling X-Train": 57,
    "Double Rock Spin": 54,
    "Hurricane": 53,
    "Thunder Falls": 107,
    "Columbus Adventure": 58,
    "Let's Twist": 56,
    "Royal Jubilee Carousel": 151,
    "Peter Pan": 113,
    "Shooting Ghost": 154,
    "Space Tour": 156,
    "Magic Swing": 111,
    "Sky Dancing": 112,
    "Racing Coaster": 101,
    "Bumper Car": 118,
    "Flying Elephant": 115,
    "Robot Car": 116,
    "Magic Cookie House": 110,
    "Lily Dance": 104,
    "Flash Bang Bang": 114,
    "Panda World": 216,
}

# 역매핑 생성 (ID -> 영문)
ID_TO_NAME = {node_id: name for name, node_id in NAME_TO_ID.items()}

def load_json_file(filename: str) -> Dict | List:
    """
    JSON 파일 로드

    Args:
        filename: data/everland/ 디렉토리 내의 파일명

    Returns:
        파싱된 JSON 데이터 (딕셔너리 또는 리스트)
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # src의 부모 디렉토리
    file_path = os.path.join(project_root, 'data', 'everland', filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Warning: JSON decode error in {filename}: {e}")
        return []

def fetch_realtime_wait_times() -> Dict[str, int]:
    """
    실시간 대기시간 API 호출

    Returns:
        놀이기구 이름 -> 대기시간(분) 매핑 딕셔너리
        운영 중단된 놀이기구는 CLOSED_RIDE_WAIT_TIME(999)로 설정
    """
    url = "https://queue-times.com/parks/125/queue_times.json"
    wait_map = {}

    try:
        response = requests.get(url, timeout=API_TIMEOUT)
        if response.status_code != 200:
            print(f"Warning: API returned status {response.status_code}")
            return wait_map

        data = response.json()
        all_rides = []

        # lands 내의 rides 수집
        for land in data.get('lands', []):
            all_rides.extend(land.get('rides', []))

        # 최상위 rides 수집
        all_rides.extend(data.get('rides', []))

        # 대기시간 매핑
        for ride in all_rides:
            ride_name = ride.get('name')
            if ride_name:
                if ride.get('is_open'):
                    wait_map[ride_name] = ride.get('wait_time', DEFAULT_ATTRACTION_WAIT)
                else:
                    wait_map[ride_name] = CLOSED_RIDE_WAIT_TIME

    except requests.RequestException as e:
        print(f"Warning: Failed to fetch real-time wait times: {e}")
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse API response: {e}")

    return wait_map

def add_missing_connections(graph: Graph) -> None:
    """
    끊어진 구역들을 연결하는 가상의 다리 추가

    Args:
        graph: 연결을 추가할 그래프
    """
    # 수동으로 추가할 브릿지 (u, v, move_time)
    bridges: List[Tuple[int, int, float]] = [
        (0, 53, 5.0),    # 정문 -> 허리케인
        (0, 118, 8.0),   # 정문 -> 범퍼카
        (58, 107, 6.0),  # 콜럼버스 -> 썬더폴스
        (54, 156, 5.0),  # 더블락스핀 -> 스페이스투어
        (151, 206, 5.0), # 회전목마 -> 아마존
        (158, 180, 4.0), # 알파인 -> 차이나문
        (206, 112, 7.0)  # 아마존 -> 스카이댄싱
    ]

    for u, v, time in bridges:
        try:
            # 두 노드가 모두 존재하는 경우에만 연결
            if graph.get_node(u) and graph.get_node(v):
                graph.add_undirected_edge(u, v, time)
        except ValueError:
            continue

def _calculate_wait_time(
    node_type: str,
    node_id: int,
    live_wait_times: Dict[str, int]
) -> float:
    """
    노드 타입과 실시간 대기시간 정보로부터 대기시간 계산

    Args:
        node_type: 노드 타입 (attraction, restaurant, show 등)
        node_id: 노드 ID
        live_wait_times: 실시간 대기시간 매핑

    Returns:
        계산된 대기시간 (분)
    """
    # ID에 해당하는 영문 이름 찾기
    english_name = ID_TO_NAME.get(node_id)

    if node_type == 'attraction':
        # 실시간 대기시간이 있으면 사용, 없으면 기본값
        if english_name and english_name in live_wait_times:
            return live_wait_times[english_name]
        return DEFAULT_ATTRACTION_WAIT
    elif node_type == 'restaurant':
        return DEFAULT_RESTAURANT_WAIT
    elif node_type == 'show':
        return DEFAULT_SHOW_WAIT
    else:
        return 0.0


def _create_node_from_data(
    data: Dict,
    coords: Dict,
    live_wait_times: Dict[str, int]
) -> Node:
    """
    JSON 데이터로부터 Node 객체 생성

    Args:
        data: 노드 데이터 딕셔너리
        coords: 좌표 데이터 딕셔너리
        live_wait_times: 실시간 대기시간 딕셔너리

    Returns:
        생성된 Node 객체
    """
    node_id = data['id']
    node_type = data['type']
    node_name = data['name']

    # 대기시간 계산
    wait_time = _calculate_wait_time(node_type, node_id, live_wait_times)

    # Node 객체 생성
    node = Node(
        node_id=node_id,
        node_type=node_type,
        name=node_name,
        wait_time=wait_time,
        min_height=data.get('min_height'),
        max_height=data.get('max_height'),
        min_age=data.get('min_age'),
        max_age=data.get('max_age')
    )

    # 좌표 설정
    str_id = str(node_id)
    if str_id in coords:
        node.x = coords[str_id]['x']
        node.y = coords[str_id]['y']

    return node


def create_park_graph(
    node_file: str = 'nodes.json',
    edge_file: str = 'edges.json',
    coord_file: str = 'coords.json'
) -> Optional[Graph]:
    """
    테마파크 그래프 생성

    Args:
        node_file: 노드 데이터 JSON 파일명
        edge_file: 간선 데이터 JSON 파일명
        coord_file: 좌표 데이터 JSON 파일명

    Returns:
        생성된 Graph 객체 (실패 시 None)
    """
    # 1. 데이터 로드
    raw_nodes = load_json_file(node_file)
    raw_edges = load_json_file(edge_file)
    raw_coords = load_json_file(coord_file)

    if not raw_nodes:
        print("Error: No node data loaded")
        return None

    # 2. 그래프 초기화
    max_id = max(n['id'] for n in raw_nodes)
    graph = Graph(max_id + 1)

    # 3. 실시간 대기시간 가져오기
    live_wait_times = fetch_realtime_wait_times()

    # 4. 노드 추가
    for data in raw_nodes:
        try:
            node = _create_node_from_data(data, raw_coords, live_wait_times)
            graph.add_node(node)
        except Exception as e:
            print(f"Warning: Failed to create node {data.get('id')}: {e}")
            continue

    # 5. 간선 추가
    for edge in raw_edges:
        try:
            u, v = edge['u'], edge['v']
            time = edge['move_time']
            graph.add_undirected_edge(u, v, time)
        except Exception as e:
            print(f"Warning: Failed to add edge {edge}: {e}")
            continue

    # 6. 연결성 보강
    add_missing_connections(graph)

    return graph