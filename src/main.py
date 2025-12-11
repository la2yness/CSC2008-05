from graph import Graph, Node
from user import UserProfile
from weights import WeightCalculator

# 라우팅 알고리즘 모듈
from routing.leg_shortest_path import compute_all_pairs_shortest_paths
from routing.alg_greedy_nearest import greedy_nearest_next
from routing.alg_greedy_2opt import greedy_nearest_with_2opt
from routing.alg_cheapest_insertion import cheapest_insertion
from routing.alg_random_baseline import random_baseline
from evaluation import evaluate_algorithm, compare_algorithms
from everland_loader import create_everland_graph

def main():
    print("\n" + "=" * 100)
    print("Theme Park Route Planner - Algorithm Comparison")
    print("=" * 100 + "\n")

    # [1] Graph Creation
    print("[1] Creating theme park graph...")
    graph = create_everland_graph()
    
    if graph is None: return

    # 활성 노드 필터링
    active_nodes = [n for n in graph.nodes if n is not None]
    
    # 간선 수 계산
    total_edges = 0
    for n in active_nodes:
        neighbors = graph.get_neighbors(n.id)
        total_edges += len(neighbors)
    
    print(f"    Created: Graph(nodes={len(active_nodes)}, edges={total_edges})")
    print(f"    Total nodes: {len(active_nodes)}")

    # [2] User Profile
    print("\n[2] Creating user profile...")
    user = UserProfile(name="Alice", age=25, height=170)
    print(f"    User: UserProfile(name={user.name}, age={user.age}, height={user.height}cm)")

    # [3] Selecting Desired Attractions
    print("\n[3] Selecting desired attractions...")
    # [수정] 방문지 대폭 추가 (기존 + 56, 156, 118, 151, 111)
    wishlist = [
        0,   # 정문
        157, # T 익스프레스
        207, # 로스트 밸리
        206, # 아마존 익스프레스
        58,  # 콜럼버스 대탐험
        54,  # 더블 락스핀
        107, # 썬더폴스
        180, # 차이나문 (식당)
        217, # 판타스틱 윙스 (공연)
        56,  # 렛츠 트위스트 (추가)
        156, # 스페이스 투어 (추가)
        118, # 범퍼카 (추가)
        151, # 로얄 쥬빌리 캐로셀 (추가)
        111  # 매직 스윙 (추가)
    ]
    
    desired_nodes = []
    for nid in wishlist:
        node = graph.get_node(nid)
        if node and node.wait_time < 999:
            desired_nodes.append(nid)
            
    print(f"    Desired nodes: {desired_nodes}")

    if len(desired_nodes) < 2:
        print("    ! Not enough destinations selected.")
        return

    # [4] Filtering Usable Nodes
    print("\n[4] Filtering usable nodes based on user constraints...")
    try: 
        user_info = user.to_dict()
    except: 
        user_info = {"age": user.age, "height": user.height}

    usable_nodes = graph.filter_usable_nodes(user_info, desired_nodes)
    
    if 0 not in usable_nodes and 0 in desired_nodes:
        usable_nodes.insert(0, 0)
        
    print(f"    Usable nodes: {usable_nodes}")

    # [5] Computing Shortest Paths
    print("\n[5] Computing all-pairs shortest paths...")
    travel_costs = compute_all_pairs_shortest_paths(graph, usable_nodes)
    print(f"    Computed travel costs for {len(usable_nodes)} nodes (optimized for usable nodes only)")

    # [6] Setting up Weight Calculator
    print("\n[6] Setting up weight calculator...")
    wait_times = {nid: graph.get_node(nid).wait_time for nid in usable_nodes}
    weight_calc = WeightCalculator(alpha=1.0, beta=1.0)
    print(f"    WeightCalculator(alpha={weight_calc.alpha}, beta={weight_calc.beta})")

    # [7] Running Algorithms
    print("\n[7] Running algorithms and evaluating performance...\n")
    start_node = 0
    metrics_list = []

    algos = [
        ("Greedy Nearest-Next", greedy_nearest_next),
        ("Greedy + 2-Opt", lambda s, u, t, w, c: greedy_nearest_with_2opt(s, u, t, w, c, max_iterations=500)),
        ("Cheapest Insertion", cheapest_insertion),
        ("Random Baseline", lambda s, u, t, w, c: random_baseline(s, u, t, w, c, seed=42))
    ]

    for name, func in algos:
        print(f"    Running: {name}...")
        try:
            m = evaluate_algorithm(name, func, start_node, usable_nodes, travel_costs, wait_times, weight_calc)
            metrics_list.append(m)
        except Exception as e:
            print(f"    Error running {name}: {e}")

    # 결과 비교 출력
    print("\n" + "="*100)
    print("Algorithm Performance Comparison")
    print("="*100)
    compare_algorithms(metrics_list)
    print("="*100)

    # 최적 경로 상세 출력
    valid_metrics = [m for m in metrics_list if m.total_cost != float('inf')]
    if not valid_metrics:
        print("\nNo valid route found.")
        return

    best = sorted(valid_metrics, key=lambda x: x.total_cost)[0]
    
    print(f"\nBest Performance:")
    print(f"  - Lowest Total Cost: {best.algorithm_name} ({best.total_cost:.2f})")
    print("="*100)
    
    print("\n\nDetailed Path Information:")
    print("="*100)
    
    route_display_list = []
    
    # [수정] 경로가 메인 입구(0)로 끝나지 않으면 강제로 추가 (원점 회귀)
    final_path = list(best.path)
    if final_path[-1] != 0:
        final_path.append(0)

    for nid in final_path:
        node = graph.get_node(nid)
        
        name = getattr(node, 'name', f"ID_{nid}")
        ntype = getattr(node, 'node_type', 'attraction')
        wait = getattr(node, 'wait_time', 0)
        
        info = ""
        if ntype == 'restaurant':
            info = f"[{name} (식사 {wait}분)]"
        elif ntype == 'show':
            info = f"[{name} (관람 {wait}분)]"
        elif ntype == 'entrance':
            # 출발지인지 도착지인지 구분 (맨 마지막에 있으면 도착)
            if nid == final_path[-1] and len(final_path) > 1:
                info = f"[{name} (도착)]"
            else:
                info = f"[{name} (출발)]"
        else:
            info = f"[{name} (대기 {wait}분)]"
            
        route_display_list.append(info)
        
    print(" -> ".join(route_display_list))
    print("="*100 + "\n")

if __name__ == "__main__":
    main()