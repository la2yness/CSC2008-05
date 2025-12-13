from graph import Graph, Node
from user import UserProfile
from weights import WeightCalculator
import unicodedata
import os

# 라우팅 알고리즘 모듈
from routing.shortest_path import compute_all_pairs_shortest_paths, reconstruct_path
from routing.greedy_nearest import greedy_nearest_next
from routing.greedy_lookahead import greedy_lookahead
from routing.greedy_2opt import greedy_nearest_with_2opt
from routing.cheapest_insertion import cheapest_insertion
from routing.random_baseline import random_baseline
from routing.milp_optimizer import milp_tsp
from evaluation import evaluate_algorithm, compare_algorithms
from park_loader import create_park_graph, CLOSED_RIDE_WAIT_TIME
from visualize import visualize_all, visualize_path

def display_width(text):
    """
    텍스트의 실제 표시 너비 계산 (한글은 2, 영문은 1)
    """
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width

def main():
    print("\n" + "=" * 100)
    print("Theme Park Route Planner - Algorithm Comparison")
    print("=" * 100 + "\n")

    # [1] Graph Creation
    print("[1] Creating theme park graph...")
    graph = create_park_graph()
    
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
    print("    Please enter visitor information:")

    # 이름 입력
    name = input("      Name: ").strip()
    if not name:
        name = "Guest"

    # 나이 입력
    while True:
        age_input = input("      Age: ").strip()
        try:
            age = int(age_input)
            if age < 0 or age > 150:
                print("      Invalid age. Please enter a valid age (0-150).")
                continue
            break
        except ValueError:
            print("      Invalid input. Please enter a number.")

    # 키 입력
    while True:
        height_input = input("      Height (cm): ").strip()
        try:
            height = float(height_input)
            if height < 50 or height > 250:
                print("      Invalid height. Please enter a valid height (50-250 cm).")
                continue
            break
        except ValueError:
            print("      Invalid input. Please enter a number.")

    user = UserProfile(name=name, age=age, height=height)
    print(f"\n    Created UserProfile(name={user.name}, age={user.age}, height={user.height}cm)")

    # [3] Selecting Desired Attractions
    print("\n[3] Selecting desired attractions...")
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
        56,  # 렛츠 트위스트
        156, # 스페이스 투어
        118, # 범퍼카
        151, # 로얄 쥬빌리 캐로셀
        111  # 매직 스윙
    ]
    
    # 운영 중인 놀이기구만 선택 (wait_time < CLOSED_RIDE_WAIT_TIME)
    available_nodes = []
    operation_filtered = []

    print(f"    Total wishlist: {len(wishlist)} nodes")

    for nid in wishlist:
        try:
            node = graph.get_node(nid)
            if node and node.wait_time < CLOSED_RIDE_WAIT_TIME:
                available_nodes.append(nid)
            else:
                operation_filtered.append((nid, node.name if node else "N/A", node.wait_time if node else "N/A"))
        except ValueError:
            operation_filtered.append((nid, "Not Found", "N/A"))
            continue

    print(f"    Available nodes: {len(available_nodes)} nodes")
    if operation_filtered:
        print(f"    Filtered out: {len(operation_filtered)} nodes")

        # 정렬을 위해 최대 표시 너비 계산
        max_width = max(display_width(f"[{nid}] {name}") for nid, name, _ in operation_filtered)

        for nid, name, wait in operation_filtered:
            label = f"[{nid}] {name}"
            current_width = display_width(label)
            padding = max_width - current_width

            if wait == CLOSED_RIDE_WAIT_TIME:
                print(f"      - {label}{' ' * padding} : 운영 중단")
            elif wait == "N/A":
                print(f"      - {label}{' ' * padding} : 존재하지 않음")
            else:
                print(f"      - {label}{' ' * padding} : 대기 {wait}분")

    if len(available_nodes) < 2:
        print("    ! Not enough destinations selected.")
        return

    # [4] Filtering Usable Nodes
    print("\n[4] Filtering usable nodes based on user constraints...")
    print(f"    Input nodes: {len(available_nodes)} nodes")
    print(f"    User: age={user.age}, height={user.height}cm")

    user_info = user.to_dict()
    usable_nodes = graph.filter_usable_nodes(user_info, available_nodes)

    # 사용자 제약조건에 의해 필터링된 노드 확인
    constraint_filtered = []
    for nid in available_nodes:
        if nid not in usable_nodes:
            try:
                node = graph.get_node(nid)
                reasons = []

                # 키 제약 확인
                if node.min_height is not None and user.height < node.min_height:
                    reasons.append(f"최소 키 {node.min_height}cm 필요")
                if node.max_height is not None and user.height > node.max_height:
                    reasons.append(f"최대 키 {node.max_height}cm 제한")

                # 나이 제약 확인
                if node.min_age is not None and user.age < node.min_age:
                    reasons.append(f"최소 나이 {node.min_age}세 필요")
                if node.max_age is not None and user.age > node.max_age:
                    reasons.append(f"최대 나이 {node.max_age}세 제한")

                if reasons:
                    constraint_filtered.append((nid, node.name, ", ".join(reasons)))
            except ValueError:
                continue

    # 정문은 항상 포함
    if 0 not in usable_nodes and 0 in available_nodes:
        usable_nodes.insert(0, 0)

    print(f"    Usable nodes: {len(usable_nodes)} nodes")

    if constraint_filtered:
        print(f"    Filtered out: {len(constraint_filtered)} nodes")

        # 정렬을 위해 최대 표시 너비 계산
        max_width = max(display_width(f"[{nid}] {name}") for nid, name, _ in constraint_filtered)

        for nid, name, reason in constraint_filtered:
            label = f"[{nid}] {name}"
            current_width = display_width(label)
            padding = max_width - current_width
            print(f"      - {label}{' ' * padding} : {reason}")
    else:
        print(f"    All attractions meet user constraints!")

    # [5] Computing Shortest Paths
    print("\n[5] Computing all-pairs shortest paths...")
    travel_costs, predecessors = compute_all_pairs_shortest_paths(graph, usable_nodes)
    print(f"    Computed travel costs for all nodes (including intermediate nodes for path reconstruction)")

    # [6] Setting up Weight Calculator
    print("\n[6] Setting up weight calculator...")
    wait_times = {nid: graph.get_node(nid).wait_time for nid in usable_nodes}
    weight_calc = WeightCalculator(alpha=2.0, beta=1.0)
    print(f"    WeightCalculator(alpha={weight_calc.alpha}, beta={weight_calc.beta})")

    # [7] Running Algorithms
    print("\n[7] Running algorithms and evaluating performance...\n")
    start_node = 0
    metrics_list = []

    algos = [
        ("Greedy Nearest-Next", greedy_nearest_next),
        ("Greedy + Lookahead", lambda s, u, t, w, c: greedy_lookahead(s, u, t, w, c, lookahead_depth=2)),
        ("Greedy + 2-Opt", lambda s, u, t, w, c: greedy_nearest_with_2opt(s, u, t, w, c, max_iterations=500)),
        ("Cheapest Insertion", cheapest_insertion),
        ("Random Baseline", lambda s, u, t, w, c: random_baseline(s, u, t, w, c, seed=42)),
        ("MILP Optimization", lambda s, u, t, w, c: milp_tsp(s, u, t, w, c, time_limit=60))
    ]

    for name, func in algos:
        print(f"    Running: {name}...")
        try:
            m = evaluate_algorithm(name, func, start_node, usable_nodes, travel_costs, wait_times, weight_calc)
            metrics_list.append(m)
        except Exception as e:
            print(f"    Error running {name}: {e}")

    compare_algorithms(metrics_list)

    valid_metrics = [m for m in metrics_list if m.total_cost != float('inf')]
    if not valid_metrics:
        print("\nNo valid route found.")
        return

    # 평가 기준: total_cost → move_time → exec_time → memory
    sorted_metrics = sorted(
        valid_metrics,
        key=lambda x: (x.total_cost, x.total_move_time, x.execution_time, x.memory_used)
    )

    best = sorted_metrics[0]
    second_best = sorted_metrics[1] if len(sorted_metrics) > 1 else None

    print("\n" + "="*100)
    print("Optimal Route Details")
    print("="*100)

    # 경로가 메인 입구로 끝나지 않으면 강제로 원점 회귀
    route_nodes = list(best.path)
    if route_nodes[-1] != 0:
        route_nodes.append(0)

    # 중간 경유 노드 포함한 실제 노드 재구성
    print("\n[Reconstructing full path with intermediate nodes...]")
    final_path = []

    for i in range(len(route_nodes)):
        if i == 0:
            final_path.append(route_nodes[i])
        else:
            # route_nodes[i-1]에서 route_nodes[i]로 가는 전체 경로 추가
            source = route_nodes[i-1]
            target = route_nodes[i]

            # predecessor를 사용하여 경로 재구성
            segment = reconstruct_path(predecessors[source], source, target)

            final_path.extend(segment[1:])

    print(f"    Original route: {len(route_nodes)} stops")
    print(f"    Full path with intermediate nodes: {len(final_path)} stops")

    wait_time = 0
    meal_time = 0
    show_time = 0

    # route_nodes 만 대기시간 계산
    route_set = set(route_nodes)
    for nid in final_path:
        if nid in route_set:
            node = graph.get_node(nid)
            if node.node_type == 'attraction':
                wait_time += node.wait_time
            elif node.node_type == 'restaurant':
                meal_time += node.wait_time
            elif node.node_type == 'show':
                show_time += node.wait_time

    print(f"\nAlgorithm: {best.algorithm_name}")
    print(f"Total Stops: {len(final_path)}")
    print(f"\nTime Breakdown:")
    print(f"  - Total Cost: {best.total_cost:.2f}분")
    print(f"  - Move Time: {best.total_move_time:.2f}분")
    print(f"  - Wait Time: {wait_time:.2f}분")
    if meal_time > 0:
        print(f"  - Meal Time: {meal_time:.2f}분")
    if show_time > 0:
        print(f"  - Show Time: {show_time:.2f}분")
    print(f"\nRoute:")

    # 경로 출력
    for i, nid in enumerate(final_path):
        node = graph.get_node(nid)
        name = node.name
        ntype = node.node_type
        wait = node.wait_time
        is_destination = nid in route_set

        if i > 0:
            print("     ↓")

        if is_destination:
            # 실제 방문 목적지
            if ntype == 'restaurant':
                print(f"  {i+1}. {name} (식사 {wait}분)")
            elif ntype == 'show':
                print(f"  {i+1}. {name} (공연 관람 {wait}분)")
            elif ntype == 'entrance':
                if i == 0:
                    print(f"  {i+1}. {name} (출발)")
                elif i == len(final_path) - 1:
                    print(f"  {i+1}. {name} (도착)")
                else:
                    print(f"  {i+1}. {name}")
            else:
                print(f"  {i+1}. {name} (대기 {wait}분)")
        else:
            # 중간 경유 노드
            print(f"  {i+1}. [{name} 경유]")

    print("\n" + "="*100 + "\n")

    # [8] Visualizations
    all_filtered_nodes = []
    for nid, _, _ in operation_filtered:
        all_filtered_nodes.append(nid)
    for nid, _, _ in constraint_filtered:
        all_filtered_nodes.append(nid)

    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(project_root, 'output', 'everland')

        visualize_all(
            graph=graph,
            usable_nodes=usable_nodes,
            filtered_nodes=all_filtered_nodes,
            path=final_path,
            algorithm_name=best.algorithm_name,
            output_dir=output_dir,
            destination_nodes=route_nodes
        )

        # 2등 알고리즘도 시각화
        if second_best is not None:
            print(f"\n[Visualizing second-best algorithm: {second_best.algorithm_name}...]")

            second_route_nodes = list(second_best.path)
            if second_route_nodes[-1] != 0:
                second_route_nodes.append(0)

            second_final_path = []
            for i in range(len(second_route_nodes)):
                if i == 0:
                    second_final_path.append(second_route_nodes[i])
                else:
                    source = second_route_nodes[i-1]
                    target = second_route_nodes[i]
                    segment = reconstruct_path(predecessors[source], source, target)
                    if segment:
                        second_final_path.extend(segment[1:])
                    else:
                        second_final_path.append(target)

            visualize_path(
                graph=graph,
                path=second_final_path,
                usable_nodes=usable_nodes,
                algorithm_name=second_best.algorithm_name,
                output_path=os.path.join(output_dir, f'path_{second_best.algorithm_name.replace(" ", "_").lower()}.png'),
                destination_nodes=second_route_nodes
            )

    except Exception as e:
        print(f"Warning: Visualization failed: {e}")

    print("\n" + "="*100 + "\n")

if __name__ == "__main__":
    main()