import json
import requests
import os
from graph import Graph, Node

# API 이름 매핑 (영문 -> ID)
NAME_MAPPING = {
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

def load_json_file(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 파일이 없을 경우 조용히 빈 리스트 반환 (메인에서 처리)
        return []
    except Exception:
        return []

def fetch_realtime_wait_times():
    url = "https://queue-times.com/parks/125/queue_times.json"
    wait_map = {}
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            all_rides = []
            for land in data.get('lands', []):
                all_rides.extend(land.get('rides', []))
            all_rides.extend(data.get('rides', []))
            
            for ride in all_rides:
                if ride.get('is_open'):
                    wait_map[ride.get('name')] = ride.get('wait_time')
                else:
                    wait_map[ride.get('name')] = 999
    except Exception:
        pass 
    return wait_map

def add_missing_connections(graph):
    """끊어진 구역(Cluster)들을 강제로 연결하는 가상의 다리(Bridge) 추가"""
    bridges = [
        (0, 53, 5.0),   # 정문 -> 허리케인
        (0, 118, 8.0),  # 정문 -> 범퍼카
        (58, 107, 6.0), # 콜럼버스 -> 썬더폴스
        (54, 156, 5.0), # 더블락스핀 -> 스페이스투어
        (151, 206, 5.0),# 회전목마 -> 아마존
        (158, 180, 4.0),# 알파인 -> 차이나문
        (206, 112, 7.0) # 아마존 -> 스카이댄싱
    ]
    
    for u, v, time in bridges:
        if graph.get_node(u) and graph.get_node(v):
            graph.add_edge(u, v, time)
            graph.add_edge(v, u, time)

def create_everland_graph(node_file='everland_nodes.json', 
                          edge_file='everland_edges.json', 
                          coord_file='everland_coords.json'):
    
    raw_nodes = load_json_file(node_file)
    raw_edges = load_json_file(edge_file)
    raw_coords = load_json_file(coord_file)

    if not raw_nodes: return None

    max_id = max(n['id'] for n in raw_nodes)
    graph = Graph(max_id + 1)
    live_wait_times = fetch_realtime_wait_times()

    # 1. 노드 추가
    for data in raw_nodes:
        node_id = data['id']
        n_type = data['type']
        n_name = data['name']
        
        base_wait = 0
        mapped_eng_name = None
        for eng, pid in NAME_MAPPING.items():
            if pid == node_id:
                mapped_eng_name = eng
                break
        
        if n_type == 'attraction':
            if mapped_eng_name and mapped_eng_name in live_wait_times:
                base_wait = live_wait_times[mapped_eng_name]
            else:
                base_wait = 20
        elif n_type == 'restaurant':
            base_wait = 40 
        elif n_type == 'show':
            base_wait = 20
        
        try:
            node = Node(node_id)
        except:
            try:
                node = Node(node_id, 0, 0)
            except:
                node = Node(node_id=node_id)

        node.id = node_id
        node.name = n_name
        node.wait_time = base_wait
        node.node_type = n_type
        node.min_height = data.get('min_height')
        node.min_age = data.get('min_age')
        node.max_height = data.get('max_height')

        str_id = str(node_id)
        if str_id in raw_coords:
            node.x = raw_coords[str_id]['x']
            node.y = raw_coords[str_id]['y']
        
        graph.add_node(node)

    # 2. 간선 추가
    for edge in raw_edges:
        u, v = edge['u'], edge['v']
        time = edge['move_time']
        graph.add_edge(u, v, time)
        graph.add_edge(v, u, time)

    # 3. 연결성 보강
    add_missing_connections(graph)

    return graph