"""
평가 지표 및 성능 분석
- 총 비용, 이동 시간, 대기 시간
- 실행 시간, 메모리 사용량 측정
"""

import time
import tracemalloc
from typing import Dict, List, Callable, Any


class PerformanceMetrics:

    def __init__(
        self,
        algorithm_name: str,
        path: List[int],
        total_cost: float,
        total_move_time: float,
        total_wait_time: float,
        execution_time: float,
        memory_used: float
    ):
        """
        Args:
            algorithm_name: 알고리즘 이름
            path: 생성된 경로
            total_cost: 총 비용 (가중치 적용)
            total_move_time: 총 이동 시간
            total_wait_time: 총 대기 시간
            execution_time: 실행 시간 (초)
            memory_used: 메모리 사용량 (KB)
        """
        self.algorithm_name = algorithm_name
        self.path = path
        self.total_cost = total_cost
        self.total_move_time = total_move_time
        self.total_wait_time = total_wait_time
        self.execution_time = execution_time
        self.memory_used = memory_used
        self.num_nodes_visited = len(path)

    def __repr__(self):
        return (
            f"PerformanceMetrics(\n"
            f"  algorithm={self.algorithm_name},\n"
            f"  nodes_visited={self.num_nodes_visited},\n"
            f"  total_cost={self.total_cost:.2f},\n"
            f"  total_move_time={self.total_move_time:.2f},\n"
            f"  total_wait_time={self.total_wait_time:.2f},\n"
            f"  execution_time={self.execution_time:.6f}s,\n"
            f"  memory_used={self.memory_used:.4f}KB\n"
            f")"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm_name": self.algorithm_name,
            "path": self.path,
            "num_nodes_visited": self.num_nodes_visited,
            "total_cost": self.total_cost,
            "total_move_time": self.total_move_time,
            "total_wait_time": self.total_wait_time,
            "execution_time": self.execution_time,
            "memory_used": self.memory_used
        }


def evaluate_algorithm(
    algorithm_name: str,
    algorithm_func: Callable,
    start_node: int,
    target_nodes: List[int],
    travel_costs: Dict[int, Dict[int, float]],
    wait_times: Dict[int, float],
    weight_calculator,
    **kwargs
) -> PerformanceMetrics:
    """
    Args:
        algorithm_name: 알고리즘 이름
        algorithm_func: 알고리즘 함수
        start_node: 시작 노드 ID
        target_nodes: 방문할 노드 ID 리스트
        travel_costs: 미리 계산된 이동 시간 딕셔너리
        wait_times: 각 노드의 대기 시간 딕셔너리
        weight_calculator: WeightCalculator 객체
        **kwargs: 알고리즘 함수에 전달할 추가 인자

    Returns:
        PerformanceMetrics 객체
    """
    # 메모리 추적 시작
    tracemalloc.start()

    # 베이스라인 메모리 스냅샷 (초기 상태)
    snapshot_before = tracemalloc.take_snapshot()

    # 실행 시간 측정 시작
    start_time = time.perf_counter()

    # 알고리즘 실행
    path = algorithm_func(
        start_node,
        target_nodes,
        travel_costs,
        wait_times,
        weight_calculator,
        **kwargs
    )

    # 실행 시간 측정 종료
    end_time = time.perf_counter()
    execution_time = end_time - start_time

    # 알고리즘 실행 후 메모리 스냅샷
    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    # 두 스냅샷 간의 차이를 계산하여 실제 알고리즘 메모리 사용량 측정
    top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    memory_used = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0) / 1024  # KB 단위

    # 경로 메트릭 계산
    metrics = weight_calculator.calculate_metrics(path, travel_costs, wait_times)

    # PerformanceMetrics 객체 생성
    result = PerformanceMetrics(
        algorithm_name=algorithm_name,
        path=path,
        total_cost=metrics["total_cost"],
        total_move_time=metrics["total_move_time"],
        total_wait_time=metrics["total_wait_time"],
        execution_time=execution_time,
        memory_used=memory_used
    )

    return result


def compare_algorithms(
    metrics_list: List[PerformanceMetrics]
) -> None:
    """
    Args:
        metrics_list: PerformanceMetrics 객체 리스트
    """
    if not metrics_list:
        print("No metrics to compare.")
        return

    print("\n" + "=" * 100)
    print("Algorithm Performance Comparison")
    print("=" * 100)

    # 헤더 출력
    header = f"{'Algorithm':<25} {'Nodes':<8} {'Total Cost':<12} {'Move Time':<12} {'Wait Time':<12} {'Exec Time(s)':<14} {'Memory(KB)':<12}"
    print(header)
    print("-" * 100)

    # 각 알고리즘 결과 출력
    for m in metrics_list:
        row = (
            f"{m.algorithm_name:<25} "
            f"{m.num_nodes_visited:<8} "
            f"{m.total_cost:<12.2f} "
            f"{m.total_move_time:<12.2f} "
            f"{m.total_wait_time:<12.2f} "
            f"{m.execution_time:<14.6f} "
            f"{m.memory_used:<12.4f}"
        )
        print(row)

    print("=" * 100)

    # 최고 성능 알고리즘 찾기
    best_cost = min(metrics_list, key=lambda x: x.total_cost)
    fastest = min(metrics_list, key=lambda x: x.execution_time)
    least_memory = min(metrics_list, key=lambda x: x.memory_used)

    print("\nBest Performance:")
    print(f"  - Lowest Total Cost: {best_cost.algorithm_name} ({best_cost.total_cost:.2f})")
    print(f"  - Fastest Execution: {fastest.algorithm_name} ({fastest.execution_time:.6f}s)")
    print(f"  - Least Memory: {least_memory.algorithm_name} ({least_memory.memory_used:.4f}KB)")
    print("\n" + "=" * 100 + "\n")
