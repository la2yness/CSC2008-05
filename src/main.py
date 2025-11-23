"""
메인 실행 파일
- 테마파크 그래프 생성
- 알고리즘 실행 및 성능 비교
"""

from graph import Graph, Node
from user import UserProfile
from weights import WeightCalculator
from routing.leg_shortest_path import compute_all_pairs_shortest_paths
from routing.alg_greedy_nearest import greedy_nearest_next
from routing.alg_greedy_2opt import greedy_nearest_with_2opt
from routing.alg_cheapest_insertion import cheapest_insertion
from routing.alg_random_baseline import random_baseline
from evaluation import evaluate_algorithm, compare_algorithms

# Todo: 임의의 데이터를 생성해 넣어뒀습니다. 실제 테마파크 데이터로 교체해야 합니다.
# Todo: 대기시간을 얻기 위한 API 연동이 필요할수 있습니다.
def create_sample_theme_park() -> Graph:
    """
    15개 노드로 구성된 기본 테스트용 테마파크

    Returns:
        Graph 객체
    """
    # 15개 노드로 구성된 테마파크
    num_nodes = 15
    graph = Graph(num_nodes)

    # 노드 추가
    # 0: 입구
    graph.add_node(Node(0, "entrance", "Main Entrance", wait_time=0))

    # 1-10: 어트랙션
    graph.add_node(Node(1, "attraction", "Roller Coaster", wait_time=45, min_height=140, min_age=12))
    graph.add_node(Node(2, "attraction", "Carousel", wait_time=10, min_height=90))
    graph.add_node(Node(3, "attraction", "Ferris Wheel", wait_time=20, min_height=100))
    graph.add_node(Node(4, "attraction", "Water Slide", wait_time=35, min_height=120, min_age=8))
    graph.add_node(Node(5, "attraction", "Haunted House", wait_time=25, min_age=10))
    graph.add_node(Node(6, "attraction", "Bumper Cars", wait_time=15, min_height=110))
    graph.add_node(Node(7, "attraction", "Swing Ride", wait_time=18, min_height=130, min_age=7))
    graph.add_node(Node(8, "attraction", "Log Flume", wait_time=30, min_height=120, min_age=6))
    graph.add_node(Node(9, "attraction", "Free Fall", wait_time=40, min_height=150, min_age=14, max_height=200))
    graph.add_node(Node(10, "attraction", "Train Ride", wait_time=12))

    # 11-14: 편의시설
    graph.add_node(Node(11, "restaurant", "Food Court", wait_time=15))
    graph.add_node(Node(12, "restaurant", "Ice Cream Shop", wait_time=5))
    graph.add_node(Node(13, "restroom", "Restroom A", wait_time=3))
    graph.add_node(Node(14, "restroom", "Restroom B", wait_time=3))

    # 간선 추가 (무방향 그래프)
    edges = [
        (0, 1, 5),   # Entrance - Roller Coaster
        (0, 2, 3),   # Entrance - Carousel
        (0, 10, 4),  # Entrance - Train Ride
        (1, 3, 7),   # Roller Coaster - Ferris Wheel
        (1, 9, 6),   # Roller Coaster - Free Fall
        (2, 3, 4),   # Carousel - Ferris Wheel
        (2, 10, 3),  # Carousel - Train Ride
        (3, 4, 5),   # Ferris Wheel - Water Slide
        (3, 11, 6),  # Ferris Wheel - Food Court
        (4, 5, 4),   # Water Slide - Haunted House
        (4, 8, 5),   # Water Slide - Log Flume
        (5, 6, 3),   # Haunted House - Bumper Cars
        (5, 11, 7),  # Haunted House - Food Court
        (6, 7, 4),   # Bumper Cars - Swing Ride
        (6, 13, 2),  # Bumper Cars - Restroom A
        (7, 8, 5),   # Swing Ride - Log Flume
        (7, 9, 6),   # Swing Ride - Free Fall
        (8, 9, 7),   # Log Flume - Free Fall
        (8, 14, 3),  # Log Flume - Restroom B
        (9, 14, 4),  # Free Fall - Restroom B
        (10, 11, 5), # Train Ride - Food Court
        (10, 12, 4), # Train Ride - Ice Cream Shop
        (11, 12, 3), # Food Court - Ice Cream Shop
        (12, 13, 5), # Ice Cream Shop - Restroom A
        (13, 14, 6), # Restroom A - Restroom B
    ]

    for u, v, time in edges:
        graph.add_edge(u, v, time)

    return graph


def create_complex_theme_park() -> Graph:
    """
    30개 노드로 구성된 대규모 테스트용 테마파크

    Returns:
        Graph 객체
    """
    # 30개 노드로 구성된 대규모 테마파크
    num_nodes = 30
    graph = Graph(num_nodes)

    # 노드 추가
    # 0: 입구
    graph.add_node(Node(0, "entrance", "Main Entrance", wait_time=0))

    # 1-20: 어트랙션
    graph.add_node(Node(1, "attraction", "Mega Roller Coaster", wait_time=60, min_height=140, min_age=12))
    graph.add_node(Node(2, "attraction", "Carousel", wait_time=10, min_height=90))
    graph.add_node(Node(3, "attraction", "Giant Ferris Wheel", wait_time=25, min_height=100))
    graph.add_node(Node(4, "attraction", "Water Slide", wait_time=35, min_height=120, min_age=8))
    graph.add_node(Node(5, "attraction", "Haunted Mansion", wait_time=30, min_age=10))
    graph.add_node(Node(6, "attraction", "Bumper Cars", wait_time=15, min_height=110))
    graph.add_node(Node(7, "attraction", "Swing Ride", wait_time=18, min_height=130, min_age=7))
    graph.add_node(Node(8, "attraction", "Log Flume", wait_time=30, min_height=120, min_age=6))
    graph.add_node(Node(9, "attraction", "Free Fall Tower", wait_time=50, min_height=150, min_age=14, max_height=200))
    graph.add_node(Node(10, "attraction", "Train Ride", wait_time=12))
    graph.add_node(Node(11, "attraction", "Pirate Ship", wait_time=22, min_height=125, min_age=8))
    graph.add_node(Node(12, "attraction", "Spinning Cups", wait_time=8, min_height=95))
    graph.add_node(Node(13, "attraction", "Sky Drop", wait_time=45, min_height=145, min_age=13))
    graph.add_node(Node(14, "attraction", "Dark Ride", wait_time=20, min_age=5))
    graph.add_node(Node(15, "attraction", "Racing Coaster", wait_time=55, min_height=135, min_age=11))
    graph.add_node(Node(16, "attraction", "3D Theater", wait_time=15))
    graph.add_node(Node(17, "attraction", "Water Rapids", wait_time=40, min_height=115, min_age=7))
    graph.add_node(Node(18, "attraction", "Mini Coaster", wait_time=18, min_height=100, min_age=5))
    graph.add_node(Node(19, "attraction", "Flying Chairs", wait_time=12, min_height=105))
    graph.add_node(Node(20, "attraction", "Observation Tower", wait_time=10))

    # 21-25: 식당
    graph.add_node(Node(21, "restaurant", "Food Court", wait_time=15))
    graph.add_node(Node(22, "restaurant", "Pizza Place", wait_time=12))
    graph.add_node(Node(23, "restaurant", "Ice Cream Shop", wait_time=5))
    graph.add_node(Node(24, "restaurant", "Burger Joint", wait_time=10))
    graph.add_node(Node(25, "restaurant", "Cafe", wait_time=8))

    # 26-29: 편의시설
    graph.add_node(Node(26, "restroom", "Restroom A", wait_time=3))
    graph.add_node(Node(27, "restroom", "Restroom B", wait_time=3))
    graph.add_node(Node(28, "restroom", "Restroom C", wait_time=3))
    graph.add_node(Node(29, "shop", "Gift Shop", wait_time=5))

    # 간선 추가 (무방향 그래프, 네트워크 구조)
    edges = [
        # 입구에서 주요 구역으로
        (0, 1, 5),   # Entrance - Mega Roller Coaster
        (0, 2, 3),   # Entrance - Carousel
        (0, 10, 4),  # Entrance - Train Ride
        (0, 21, 6),  # Entrance - Food Court

        # 스릴 존 (1, 9, 13, 15)
        (1, 9, 6),   # Mega Roller Coaster - Free Fall Tower
        (1, 15, 8),  # Mega Roller Coaster - Racing Coaster
        (9, 13, 5),  # Free Fall Tower - Sky Drop
        (13, 15, 7), # Sky Drop - Racing Coaster
        (15, 11, 6), # Racing Coaster - Pirate Ship

        # 패밀리 존 (2, 10, 12, 18, 19)
        (2, 10, 3),  # Carousel - Train Ride
        (2, 12, 4),  # Carousel - Spinning Cups
        (10, 18, 5), # Train Ride - Mini Coaster
        (12, 19, 3), # Spinning Cups - Flying Chairs
        (18, 19, 4), # Mini Coaster - Flying Chairs

        # 워터 존 (4, 8, 17)
        (4, 8, 4),   # Water Slide - Log Flume
        (4, 17, 6),  # Water Slide - Water Rapids
        (8, 17, 5),  # Log Flume - Water Rapids

        # 어드벤처 존 (5, 14, 16, 20)
        (5, 14, 5),  # Haunted Mansion - Dark Ride
        (14, 16, 4), # Dark Ride - 3D Theater
        (16, 20, 6), # 3D Theater - Observation Tower
        (20, 5, 7),  # Observation Tower - Haunted Mansion

        # 중앙 연결 (6, 7, 11)
        (6, 7, 4),   # Bumper Cars - Swing Ride
        (7, 11, 5),  # Swing Ride - Pirate Ship
        (6, 11, 6),  # Bumper Cars - Pirate Ship

        # 구역 간 연결
        (1, 3, 7),   # Mega Roller Coaster - Giant Ferris Wheel
        (3, 4, 5),   # Giant Ferris Wheel - Water Slide
        (3, 21, 6),  # Giant Ferris Wheel - Food Court
        (5, 6, 3),   # Haunted Mansion - Bumper Cars
        (7, 8, 5),   # Swing Ride - Log Flume
        (11, 17, 7), # Pirate Ship - Water Rapids

        # 식당 네트워크
        (21, 22, 3), # Food Court - Pizza Place
        (21, 23, 4), # Food Court - Ice Cream Shop
        (22, 24, 3), # Pizza Place - Burger Joint
        (24, 25, 2), # Burger Joint - Cafe
        (23, 25, 3), # Ice Cream Shop - Cafe

        # 편의시설 연결
        (6, 26, 2),  # Bumper Cars - Restroom A
        (17, 27, 3), # Water Rapids - Restroom B
        (20, 28, 2), # Observation Tower - Restroom C
        (21, 29, 4), # Food Court - Gift Shop

        # 추가 크로스 연결 (그래프 연결성 강화)
        (2, 6, 5),   # Carousel - Bumper Cars
        (10, 21, 5), # Train Ride - Food Court
        (12, 23, 5), # Spinning Cups - Ice Cream Shop
        (13, 27, 4), # Sky Drop - Restroom B
        (14, 22, 6), # Dark Ride - Pizza Place
        (15, 26, 5), # Racing Coaster - Restroom A
        (16, 25, 4), # 3D Theater - Cafe
        (18, 24, 6), # Mini Coaster - Burger Joint
        (19, 20, 5), # Flying Chairs - Observation Tower
        (5, 21, 7),  # Haunted Mansion - Food Court
        (9, 27, 4),  # Free Fall Tower - Restroom B
        (11, 26, 5), # Pirate Ship - Restroom A
        (3, 20, 8),  # Giant Ferris Wheel - Observation Tower
        (4, 26, 6),  # Water Slide - Restroom A
        (7, 24, 7),  # Swing Ride - Burger Joint
    ]

    for u, v, time in edges:
        graph.add_edge(u, v, time)

    return graph


def create_extreme_theme_park() -> Graph:
    """
    100개 노드로 구성된 극단적인 대규모 테스트용 테마파크

    Returns:
        Graph 객체
    """
    num_nodes = 100
    graph = Graph(num_nodes)

    # 0: 메인 입구
    graph.add_node(Node(0, "entrance", "Main Entrance", wait_time=0))

    # 1-4: 서브 입구/광장
    graph.add_node(Node(1, "entrance", "North Plaza", wait_time=0))
    graph.add_node(Node(2, "entrance", "South Plaza", wait_time=0))
    graph.add_node(Node(3, "entrance", "East Plaza", wait_time=0))
    graph.add_node(Node(4, "entrance", "West Plaza", wait_time=0))

    # 5-60: 어트랙션 (56개)
    attractions = [
        # 스릴 존 (5-19)
        (5, "Mega Coaster X", 65, 145, 14),
        (6, "Sky Screamer", 58, 150, 15),
        (7, "Tornado Spin", 52, 140, 13),
        (8, "Free Fall Extreme", 60, 155, 16),
        (9, "Loop Fighter", 55, 145, 14),
        (10, "Thunder Bolt", 62, 150, 15),
        (11, "Vortex Rider", 50, 140, 12),
        (12, "Rocket Launcher", 68, 155, 16),
        (13, "Sky Drop Tower", 48, 145, 13),
        (14, "Twisted Cyclone", 57, 150, 14),
        (15, "Adrenaline Rush", 54, 140, 13),
        (16, "Vertical Velocity", 63, 155, 15),
        (17, "G-Force", 51, 145, 12),
        (18, "Sonic Boom", 59, 150, 14),
        (19, "Gravity Defier", 56, 140, 13),

        # 패밀리 존 (20-34)
        (20, "Happy Carousel", 8, 90, None),
        (21, "Family Coaster", 15, 105, 5),
        (22, "Spinning Teacups", 10, 95, None),
        (23, "Mini Train", 12, None, None),
        (24, "Balloon Race", 14, 100, 4),
        (25, "Boat Ride", 18, 100, 5),
        (26, "Flying Elephants", 11, 95, None),
        (27, "Gentle Dragon", 16, 105, 5),
        (28, "Ladybug Coaster", 13, 100, 4),
        (29, "Frog Hopper", 9, 95, None),
        (30, "Bee Adventure", 17, 105, 5),
        (31, "Caterpillar Train", 10, None, None),
        (32, "Pony Carousel", 8, 90, None),
        (33, "Duck Boats", 15, 100, 4),
        (34, "Bunny Hop", 12, 95, None),

        # 워터 존 (35-44)
        (35, "Splash Mountain", 38, 120, 8),
        (36, "Tidal Wave", 42, 125, 9),
        (37, "River Rapids", 36, 115, 7),
        (38, "Water Coaster", 45, 130, 10),
        (39, "Log Flume Ride", 32, 120, 7),
        (40, "Tsunami", 48, 135, 11),
        (41, "Aqua Loop", 40, 125, 9),
        (42, "Wet'n Wild", 35, 115, 7),
        (43, "Splash Zone", 28, 110, 6),
        (44, "Wave Runner", 43, 130, 10),

        # 어드벤처 존 (45-54)
        (45, "Haunted Castle", 30, None, 10),
        (46, "Jungle Safari", 25, None, 6),
        (47, "Pirate Adventure", 28, 110, 8),
        (48, "Tomb Explorer", 33, None, 11),
        (49, "Lost Temple", 27, None, 9),
        (50, "Mystery Mansion", 31, None, 10),
        (51, "Dark Forest", 26, None, 8),
        (52, "Treasure Hunt", 24, None, 7),
        (53, "Dragon's Lair", 35, 120, 11),
        (54, "Wizard Tower", 29, None, 9),

        # 특별 존 (55-60)
        (55, "4D Cinema", 20, None, None),
        (56, "VR Experience", 25, None, 10),
        (57, "Sky Tram", 15, None, None),
        (58, "Observation Deck", 10, None, None),
        (59, "Musical Fountain", 5, None, None),
        (60, "Laser Show Arena", 18, None, 8),
    ]

    for node_id, name, wait, min_h, min_a in attractions:
        graph.add_node(Node(node_id, "attraction", name, wait_time=wait,
                          min_height=min_h, min_age=min_a))

    # 61-80: 레스토랑 (20개)
    restaurants = [
        "Main Food Court", "Pizza Palace", "Burger House", "Noodle Bar",
        "Steakhouse", "Seafood Grill", "Taco Stand", "Sandwich Shop",
        "Ice Cream Parlor", "Dessert Cafe", "Coffee Shop", "Bakery",
        "Asian Fusion", "Italian Kitchen", "Mexican Cantina", "BBQ Pit",
        "Salad Bar", "Juice Bar", "Snack Station", "Family Restaurant"
    ]
    for i, name in enumerate(restaurants, start=61):
        wait = 8 + (i % 15)  # 8-22분 사이
        graph.add_node(Node(i, "restaurant", name, wait_time=wait))

    # 81-90: 편의시설 (10개)
    facilities = [
        ("Restroom North", 3), ("Restroom South", 3), ("Restroom East", 3),
        ("Restroom West", 3), ("Restroom Central", 3),
        ("Gift Shop Main", 8), ("Gift Shop East", 7), ("Gift Shop West", 6),
        ("Photo Booth A", 5), ("Photo Booth B", 5)
    ]
    for i, (name, wait) in enumerate(facilities, start=81):
        node_type = "restroom" if "Restroom" in name else "shop"
        graph.add_node(Node(i, node_type, name, wait_time=wait))

    # 91-99: 쉼터/정원 (9개)
    rest_areas = [
        "Rose Garden", "Meditation Plaza", "Lake View", "Picnic Area",
        "Shaded Grove", "Butterfly Garden", "Gazebo Park",
        "Children's Playground", "Central Park"
    ]
    for i, name in enumerate(rest_areas, start=91):
        graph.add_node(Node(i, "rest", name, wait_time=0))

    # 간선 추가 - 복잡한 네트워크 구조
    edges = []

    # 1. 메인 입구에서 4개 광장으로
    for plaza in range(1, 5):
        edges.append((0, plaza, 5))

    # 2. 광장 간 연결 (순환)
    edges.extend([
        (1, 2, 8), (2, 3, 8), (3, 4, 8), (4, 1, 8),
        (1, 3, 10), (2, 4, 10)  # 대각선 연결
    ])

    # 3. 각 광장에서 해당 구역 어트랙션으로 연결
    # North Plaza (1) -> 스릴 존
    for node in range(5, 20):
        edges.append((1, node, 4 + (node % 4)))

    # South Plaza (2) -> 패밀리 존
    for node in range(20, 35):
        edges.append((2, node, 3 + (node % 3)))

    # East Plaza (3) -> 워터 존
    for node in range(35, 45):
        edges.append((3, node, 4 + (node % 3)))

    # West Plaza (4) -> 어드벤처 존
    for node in range(45, 55):
        edges.append((4, node, 3 + (node % 4)))

    # 4. 같은 구역 내 어트랙션 간 연결
    # 스릴 존
    for i in range(5, 19):
        for j in range(i+1, min(i+4, 20)):
            edges.append((i, j, 3 + abs(i-j)))

    # 패밀리 존
    for i in range(20, 34):
        for j in range(i+1, min(i+3, 35)):
            edges.append((i, j, 2 + abs(i-j)))

    # 워터 존
    for i in range(35, 44):
        for j in range(i+1, min(i+3, 45)):
            edges.append((i, j, 3 + abs(i-j)))

    # 어드벤처 존
    for i in range(45, 54):
        for j in range(i+1, min(i+3, 55)):
            edges.append((i, j, 2 + abs(i-j)))

    # 5. 특별 존 연결
    for node in [1, 2, 3, 4]:
        for special in range(55, 61):
            edges.append((node, special, 6 + (special % 3)))

    # 6. 레스토랑 네트워크
    # 각 광장에서 레스토랑으로
    for plaza in range(1, 5):
        start = 61 + (plaza - 1) * 5
        for restaurant in range(start, start + 5):
            if restaurant < 81:
                edges.append((plaza, restaurant, 3 + (restaurant % 3)))

    # 레스토랑 간 연결
    for i in range(61, 80):
        for j in range(i+1, min(i+3, 81)):
            edges.append((i, j, 2))

    # 7. 편의시설 배치
    # 각 구역에 편의시설
    facilities_map = [
        (range(5, 20), 81),    # 스릴 존 - Restroom North
        (range(20, 35), 82),   # 패밀리 존 - Restroom South
        (range(35, 45), 83),   # 워터 존 - Restroom East
        (range(45, 55), 84),   # 어드벤처 존 - Restroom West
    ]

    for attraction_range, restroom in facilities_map:
        for attr in list(attraction_range)[::3]:  # 매 3번째 어트랙션마다
            edges.append((attr, restroom, 2))

    # 중앙 화장실
    for plaza in range(1, 5):
        edges.append((plaza, 85, 3))

    # 기프트샵 배치
    for plaza, shop in zip(range(1, 5), range(86, 89)):
        edges.append((plaza, shop, 4))

    # 8. 쉼터 배치
    rest_positions = [
        (1, 91), (1, 92), (2, 93), (2, 94),
        (3, 95), (3, 96), (4, 97), (4, 98), (0, 99)
    ]
    for plaza, rest in rest_positions:
        edges.append((plaza, rest, 3))

    # 9. 추가 크로스 연결 (그래프 연결성 강화)
    # 구역 간 연결
    cross_connections = [
        (10, 25, 10), (15, 30, 12), (8, 37, 11), (12, 42, 13),
        (18, 48, 10), (22, 50, 11), (28, 56, 9), (33, 58, 8),
        (40, 52, 12), (38, 15, 14), (46, 10, 13), (53, 18, 11),
        (7, 61, 7), (14, 65, 8), (26, 68, 6), (31, 72, 7),
        (41, 75, 6), (49, 78, 7), (55, 70, 5), (57, 66, 6),
    ]
    edges.extend(cross_connections)

    # 간선 추가
    for u, v, time in edges:
        if u < num_nodes and v < num_nodes:
            graph.add_edge(u, v, time)

    return graph

# 조건별 알고리즘 비교 분석을 위해 조건의 제어가 가능합니다.
def main():
    """메인 실행 함수"""
    print("\n" + "=" * 100)
    print("Theme Park Route Planner - Algorithm Comparison")
    print("=" * 100 + "\n")

    # 1. 테마파크 그래프 생성
    print("[1] Creating theme park graph...")
    # 기본 그래프 사용 (15 nodes)
    # graph = create_sample_theme_park()

    # 복잡한 그래프 사용 (30 nodes)
    # graph = create_complex_theme_park()

    # 극단적인 그래프 사용 (100 nodes)
    graph = create_extreme_theme_park()

    print(f"    Created: {graph}")
    print(f"    Total nodes: {len([n for n in graph.nodes if n is not None])}")
    print()

    # 2. 사용자 프로필 생성
    # Todo: 사용자 입력 또는 외부 데이터로부터 제약조건을 생성해야 합니다.
    print("[2] Creating user profile...")
    user = UserProfile(age=25, height=170, name="Alice")
    print(f"    User: {user}")
    print()

    # 3. 방문하고 싶은 어트랙션 선택
    # Todo: 사용자 입력 또는 외부 데이터로부터 노드 리스트를 선택해야 합니다.
    print("[3] Selecting desired attractions...")
    # 기본 그래프용 (15 nodes)
    # desired_attractions = [0, 1, 3, 4, 5, 6, 7, 8, 9, 11]

    # 복잡한 그래프용 (30 nodes)
    # desired_attractions = [
    #     0,   # Main Entrance
    #     1,   # Mega Roller Coaster
    #     3,   # Giant Ferris Wheel
    #     5,   # Haunted Mansion
    #     9,   # Free Fall Tower
    #     11,  # Pirate Ship
    #     13,  # Sky Drop
    #     15,  # Racing Coaster
    #     17,  # Water Rapids
    #     20,  # Observation Tower
    #     21,  # Food Court
    # ]

    # 극단적인 그래프용 (100 nodes)
    desired_attractions = [
        0,   # Main Entrance
        # 스릴 존
        5,   # Mega Coaster X
        8,   # Free Fall Extreme
        12,  # Rocket Launcher
        16,  # Vertical Velocity
        # 패밀리 존
        21,  # Family Coaster
        25,  # Boat Ride
        30,  # Bee Adventure
        # 워터 존
        35,  # Splash Mountain
        38,  # Water Coaster
        40,  # Tsunami
        # 어드벤처 존
        45,  # Haunted Castle
        48,  # Tomb Explorer
        53,  # Dragon's Lair
        # 특별 존
        55,  # 4D Cinema
        58,  # Observation Deck
        # 레스토랑
        61,  # Main Food Court
        # 편의시설
        85,  # Restroom Central
    ]
    print(f"    Desired nodes: {desired_attractions}")
    print()

    # 4. 사용 가능한 노드 필터링
    print("[4] Filtering usable nodes based on user constraints...")
    usable_nodes = graph.filter_usable_nodes(user.to_dict(), desired_attractions)
    print(f"    Usable nodes: {usable_nodes}")
    print()

    # 5. 모든 노드 쌍의 최단 경로 계산
    print("[5] Computing all-pairs shortest paths...")
    travel_costs = compute_all_pairs_shortest_paths(graph, usable_nodes)
    print(f"    Computed travel costs for {len(travel_costs)} nodes (optimized for usable nodes only)")
    print()

    # 6. 대기 시간 딕셔너리 생성
    wait_times = {node.id: node.wait_time for node in graph.nodes if node is not None}

    # 7. 가중치 계산기 생성
    # Todo: 사용자 선호도에 따른 가중치 수식을 조정해야 합니다.
    print("[6] Setting up weight calculator...")
    alpha = 1.0  # 이동 시간 가중치
    beta = 1.0   # 대기 시간 가중치
    weight_calc = WeightCalculator(alpha=alpha, beta=beta)
    print(f"    {weight_calc}")
    print()

    # 8. 시작 노드 설정
    start_node = 0  # 입구에서 출발

    # 9. 알고리즘 실행 및 평가
    print("[7] Running algorithms and evaluating performance...")
    print()

    metrics_list = []

    # Greedy Nearest-Next
    print("    Running: Greedy Nearest-Next...")
    m1 = evaluate_algorithm(
        "Greedy Nearest-Next",
        greedy_nearest_next,
        start_node,
        usable_nodes,
        travel_costs,
        wait_times,
        weight_calc
    )
    metrics_list.append(m1)

    # Greedy + 2-Opt
    print("    Running: Greedy + 2-Opt...")
    m2 = evaluate_algorithm(
        "Greedy + 2-Opt",
        greedy_nearest_with_2opt,
        start_node,
        usable_nodes,
        travel_costs,
        wait_times,
        weight_calc,
        max_iterations=1000
    )
    metrics_list.append(m2)

    # Cheapest Insertion
    print("    Running: Cheapest Insertion...")
    m3 = evaluate_algorithm(
        "Cheapest Insertion",
        cheapest_insertion,
        start_node,
        usable_nodes,
        travel_costs,
        wait_times,
        weight_calc
    )
    metrics_list.append(m3)

    # Random Baseline
    print("    Running: Random Baseline...")
    m4 = evaluate_algorithm(
        "Random Baseline",
        random_baseline,
        start_node,
        usable_nodes,
        travel_costs,
        wait_times,
        weight_calc,
        seed=42
    )
    metrics_list.append(m4)

    print()

    # 10. 결과 비교
    compare_algorithms(metrics_list)

    # 11. 경로 상세 정보 출력
    print("\nDetailed Path Information:")
    print("=" * 100)
    for m in metrics_list:
        print(f"\n{m.algorithm_name}:")
        print(f"  Path: {' -> '.join(str(node) for node in m.path)}")
        if len(m.path) > 0:
            path_names = []
            for node_id in m.path:
                try:
                    node = graph.get_node(node_id)
                    path_names.append(node.name)
                except ValueError as e:
                    path_names.append(f"Node_{node_id}")
                except Exception as e:
                    path_names.append(f"Unknown_{node_id}")
            print(f"  Route: {' -> '.join(path_names)}")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
