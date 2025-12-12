"""
그래프 시각화 모듈
- 좌표 기반 그래프 렌더링
- 제약조건에 따른 노드 활성화/비활성화 표시
- 경로 시각화
"""

import os
import io
import tempfile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib import font_manager
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
from typing import List, Dict, Optional, Tuple
from graph import Graph

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 노드 스타일 정의
NODE_STYLES = {
    'entrance': {'color': '#2ecc71', 'icon': '입구.png', 'zoom': 0.17, 'label': '입구'},
    'attraction': {'color': '#e74c3c', 'icon': '어트랙션.png', 'zoom': 0.15, 'label': '어트랙션'},
    'restaurant': {'color': '#f39c12', 'icon': '식당.png', 'zoom': 0.15, 'label': '식당'},
    'show': {'color': '#3498db', 'icon': '공연.png', 'zoom': 0.12, 'label': '공연장'},
    'restroom': {'color': '#95a5a6', 'marker': 'p', 'size': 100, 'label': '화장실'},
}

DISABLED_STYLE = {'color': '#888888', 'marker': 'x', 'size': 600, 'alpha': 0.8, 'linewidth': 4}
PATH_STYLE = {'color': 'white', 'linewidth': 5, 'alpha': 0.9, 'zorder': 10}
PATH_MARKER_STYLE = {'color': 'white', 'edgecolor': '#3498db', 'linewidth': 3, 'size': 450, 'zorder': 11}

# 이미지 크기 상수
IMAGE_PADDING = 60
MAX_IMAGE_WIDTH = 1920
MAX_IMAGE_HEIGHT = 1080

# 폰트 크기 상수
TITLE_FONTSIZE = 50
LEGEND_FONTSIZE = 24
NAME_FONTSIZE = 20
NAME_FONTSIZE_SMALL = 14
ORDER_FONTSIZE = 18

# 선 두께 상수
BORDER_WIDTH = 4
EDGE_WIDTH = 2.0
EDGE_WIDTH_THIN = 0.5
PATH_ARROW_WIDTH = 3

# 여백 및 오프셋 상수
GRAPH_MARGIN_RATIO = 0.12
FILTERED_MARGIN_RATIO = 0.12
PATH_MARGIN_RATIO = 0.25
BORDER_PADDING_RATIO = 0.02
NAME_OFFSET_BASE = -200
BASE_COORD_RANGE = 1000  # 실제 그래프 데이터의 기준 좌표 범위 (x: 45~1034)
COORD_SAFETY_MARGIN = 200
COORD_EXPLOSION_THRESHOLD = 10000

# 아이콘 크기 배율
GRAPH_ICON_SCALE = 0.65
PATH_ICON_SCALE = 1.3
UNVISITED_ICON_SCALE = 0.7
FILTERED_ICON_SCALE = 0.7

# 프로젝트 경로 상수
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ICON_DIR = os.path.join(_PROJECT_ROOT, 'asset', 'icons')


def _get_icon_height(icon_path: str) -> int:
    """
    아이콘 이미지의 세로 크기 반환

    Args:
        icon_path: 아이콘 파일 경로

    Returns:
        int: 이미지 세로 픽셀 크기
    """
    img = Image.open(icon_path)
    return img.size[1]


def _load_and_tint_icon(icon_path: str, color: str, zoom: float = 0.1) -> OffsetImage:
    """
    아이콘 이미지를 로드하고 색상을 적용

    Args:
        icon_path: 아이콘 파일 경로
        color: 적용할 색상 (hex 코드)
        zoom: 아이콘 크기 배율

    Returns:
        OffsetImage: 색상이 적용된 아이콘 이미지
    """
    img = Image.open(icon_path).convert('RGBA')
    img_array = np.array(img)

    color = color.lstrip('#')
    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)

    rgb_array = img_array[:, :, :3]
    alpha_array = img_array[:, :, 3]

    brightness = rgb_array.mean(axis=2)
    mask = brightness < 100

    colored_array = rgb_array.copy()
    colored_array[mask] = [r, g, b]

    result = np.dstack([colored_array, alpha_array])

    return OffsetImage(result, zoom=zoom)


def _get_node_position(graph: Graph, node_id: int) -> Tuple[float, float]:
    """
    노드 좌표 반환

    Args:
        graph: 그래프 객체
        node_id: 노드 ID

    Returns:
        Tuple[float, float]: (x, y) 좌표
    """
    try:
        node = graph.get_node(node_id)
        return (getattr(node, 'x', 0), getattr(node, 'y', 0))
    except (ValueError, AttributeError):
        return (0, 0)


def _add_border_frame(ax, border_padding_ratio: float = BORDER_PADDING_RATIO) -> None:
    """
    테두리 프레임 추가

    Args:
        ax: matplotlib axes 객체
        border_padding_ratio: 테두리 패딩 비율
    """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_range = xlim[1] - xlim[0]
    y_range = ylim[1] - ylim[0]
    border_padding = min(abs(x_range), abs(y_range)) * border_padding_ratio

    rect = Rectangle(
        (xlim[0] + border_padding, ylim[0] + border_padding),
        x_range - 2 * border_padding,
        y_range - 2 * border_padding,
        linewidth=BORDER_WIDTH,
        edgecolor='white',
        facecolor='none',
        zorder=100
    )
    ax.add_patch(rect)


def _resize_with_aspect_ratio(
    img: Image.Image,
    max_width: int = MAX_IMAGE_WIDTH - 2 * IMAGE_PADDING,
    max_height: int = MAX_IMAGE_HEIGHT - 2 * IMAGE_PADDING
) -> Image.Image:
    """
    Aspect ratio 유지하며 이미지 리사이징

    Args:
        img: PIL Image 객체
        max_width: 최대 너비
        max_height: 최대 높이

    Returns:
        Image.Image: 리사이징된 이미지
    """
    width_ratio = img.width / max_width
    height_ratio = img.height / max_height

    if height_ratio > width_ratio:
        new_height = max_height
        new_width = int(img.width * (max_height / img.height))
    else:
        new_width = max_width
        new_height = int(img.height * (max_width / img.width))

    return img.resize((new_width, new_height), Image.Resampling.LANCZOS)


def _save_and_resize_figure(
    fig,
    output_path: str,
    padding: int = IMAGE_PADDING
) -> None:
    """
    Figure를 저장하고 리사이징 후 최종 저장

    Args:
        fig: matplotlib figure 객체
        output_path: 저장 경로
        padding: 이미지 패딩
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 임시 버퍼에 저장
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='black')
    plt.close()
    buf.seek(0)

    # 이미지 로드 및 리사이징
    img = Image.open(buf)
    img = _resize_with_aspect_ratio(img)

    # 검은 배경에 이미지 배치
    bg_width = img.width + 2 * padding
    bg_height = img.height + 2 * padding
    background = Image.new('RGB', (bg_width, bg_height), (0, 0, 0))
    background.paste(img, (padding, padding))

    background.save(output_path, dpi=(300, 300))


def _ensure_coordinate_bounds(ax, nodes: List[int], graph: Graph) -> None:
    """
    좌표 범위 초과 방지

    Args:
        ax: matplotlib axes 객체
        nodes: 노드 ID 리스트
        graph: 그래프 객체
    """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    x_range = abs(xlim[1] - xlim[0])
    y_range = abs(ylim[1] - ylim[0])

    # 좌표 범위가 너무 크거나 너무 작으면 재계산
    if x_range > COORD_EXPLOSION_THRESHOLD or y_range > COORD_EXPLOSION_THRESHOLD or x_range < 100 or y_range < 100:
        all_x = []
        all_y = []
        for nid in nodes:
            try:
                node = graph.get_node(nid)
                all_x.append(getattr(node, 'x', 0))
                all_y.append(getattr(node, 'y', 0))
            except (ValueError, AttributeError):
                pass

        if all_x and all_y:
            ax.set_xlim(min(all_x) - 100, max(all_x) + 100)
            ax.set_ylim(min(all_y) - 100, max(all_y) + 100)


def visualize_graph(
    graph: Graph,
    output_path: str = 'output/everland/graph.png',
    title: str = '테마파크 그래프',
    figsize: Tuple[int, int] = (22, 18)
) -> None:
    """
    전체 그래프 시각화

    Args:
        graph: 그래프 객체
        output_path: 저장 경로
        title: 그래프 제목
        figsize: matplotlib figure 크기
    """
    fig, ax = plt.subplots(figsize=figsize)
    fig.subplots_adjust(top=0.94, bottom=0.06, left=0.06, right=0.94)

    # 간선 그리기
    for node in graph.nodes:
        if not node:
            continue

        x1, y1 = _get_node_position(graph, node.id)
        neighbors = graph.get_neighbors(node.id)

        for neighbor_id, _ in neighbors:
            if node.id < neighbor_id:
                x2, y2 = _get_node_position(graph, neighbor_id)
                ax.plot([x1, x2], [y1, y2], 'lightgray', linewidth=EDGE_WIDTH, alpha=0.4, zorder=1)

    # 범례용 요소
    legend_elements = []

    for node_type, style in NODE_STYLES.items():
        nodes_of_type = [n for n in graph.nodes if n and n.node_type == node_type]

        if not nodes_of_type:
            continue

        if 'icon' in style:
            icon_path = os.path.join(_ICON_DIR, style['icon'])

            if os.path.exists(icon_path):
                for node in nodes_of_type:
                    x, y = getattr(node, 'x', 0), getattr(node, 'y', 0)

                    icon_img = _load_and_tint_icon(icon_path, style['color'], style['zoom'] * GRAPH_ICON_SCALE)

                    ab = AnnotationBbox(icon_img, (x, y), frameon=False, zorder=3)
                    ax.add_artist(ab)

            legend_elements.append(
                mpatches.Patch(facecolor=style['color'], label=style['label'])
            )
        else:
            x_coords = [getattr(n, 'x', 0) for n in nodes_of_type]
            y_coords = [getattr(n, 'y', 0) for n in nodes_of_type]

            ax.scatter(
                x_coords, y_coords,
                c=style['color'],
                marker=style.get('marker', 'o'),
                s=style.get('size', 100),
                label=style['label'],
                alpha=0.8,
                edgecolors='black',
                linewidth=1,
                zorder=3
            )

    ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold', pad=50, color='white')
    ax.axis('off')

    legend = ax.legend(handles=legend_elements if legend_elements else None,
                      loc='upper right', fontsize=LEGEND_FONTSIZE, frameon=False,
                      labelspacing=1.2, bbox_to_anchor=(0.95, 0.95))
    for text in legend.get_texts():
        text.set_color('white')
        text.set_fontweight('bold')

    ax.set_aspect('equal', adjustable='box')

    # 여백 추가
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_margin = (xlim[1] - xlim[0]) * GRAPH_MARGIN_RATIO
    y_margin = (ylim[1] - ylim[0]) * GRAPH_MARGIN_RATIO
    ax.set_xlim(xlim[0] - x_margin, xlim[1] + x_margin)
    ax.set_ylim(ylim[0] - y_margin, ylim[1] + y_margin)

    active_nodes = [n.id for n in graph.nodes if n is not None]
    _ensure_coordinate_bounds(ax, active_nodes, graph)

    _add_border_frame(ax)

    plt.tight_layout()

    _save_and_resize_figure(fig, output_path)

    print(f"    Graph visualization saved: {output_path}")


def visualize_filtered_graph(
    graph: Graph,
    usable_nodes: List[int],
    filtered_nodes: List[int],
    output_path: str = 'output/everland/filtered_graph.png',
    title: str = '사용자 제약조건 적용 노드',
    figsize: Tuple[int, int] = (22, 18)
) -> None:
    """
    제약조건이 적용된 노드 시각화 (사용자 제약 + 운영 중단)

    Args:
        graph: 그래프 객체
        usable_nodes: 사용 가능한 노드 ID 리스트
        filtered_nodes: 제약조건으로 필터링된 노드 ID 리스트
        output_path: 저장 경로
        title: 그래프 제목
        figsize: matplotlib figure 크기
    """
    fig, ax = plt.subplots(figsize=figsize)
    fig.subplots_adjust(top=0.94, bottom=0.06, left=0.06, right=0.94)

    usable_set = set(usable_nodes)

    # 초기 좌표 범위 설정
    all_nodes = list(set(usable_nodes + filtered_nodes))
    all_x = [_get_node_position(graph, nid)[0] for nid in all_nodes]
    all_y = [_get_node_position(graph, nid)[1] for nid in all_nodes]
    if all_x and all_y:
        ax.set_xlim(min(all_x) - 100, max(all_x) + 100)
        ax.set_ylim(min(all_y) - 100, max(all_y) + 100)

    # 간선 그리기
    for node in graph.nodes:
        if not node or node.id not in usable_set:
            continue

        x1, y1 = _get_node_position(graph, node.id)
        neighbors = graph.get_neighbors(node.id)

        for neighbor_id, _ in neighbors:
            if neighbor_id in usable_set and node.id < neighbor_id:
                x2, y2 = _get_node_position(graph, neighbor_id)
                ax.plot([x1, x2], [y1, y2], 'lightgray', linewidth=EDGE_WIDTH, alpha=0.4, zorder=1)

    # 제약조건 적용 노드 표시
    if filtered_nodes:
        for node_id in filtered_nodes:
            try:
                node = graph.get_node(node_id)
                x, y = getattr(node, 'x', 0), getattr(node, 'y', 0)
                node_style = NODE_STYLES.get(node.node_type, {})

                if 'icon' in node_style:
                    icon_path = os.path.join(_ICON_DIR, node_style['icon'])
                    if os.path.exists(icon_path):
                        icon_img = _load_and_tint_icon(icon_path, DISABLED_STYLE['color'], node_style['zoom'] * FILTERED_ICON_SCALE)
                        ab = AnnotationBbox(icon_img, (x, y), frameon=False, zorder=2)
                        ax.add_artist(ab)

                        if node.node_type in ['attraction', 'entrance', 'restaurant', 'show']:
                            icon_height = _get_icon_height(icon_path)
                            actual_zoom = node_style['zoom'] * FILTERED_ICON_SCALE
                            rendered_height = icon_height * actual_zoom
                            offset_y = -(rendered_height / 2) - 10
                            ax.text(
                                x, y + offset_y,
                                node.name,
                                fontsize=NAME_FONTSIZE_SMALL,
                                fontweight='bold',
                                ha='center',
                                va='top',
                                color=DISABLED_STYLE['color'],
                                bbox=dict(boxstyle='round,pad=0.5', facecolor='#1a1a1a',
                                         edgecolor='#666666', alpha=0.7, linewidth=1.5),
                                zorder=2
                            )
                else:
                    ax.scatter(
                        [x], [y],
                        c=DISABLED_STYLE['color'],
                        marker=node_style.get('marker', 'o'),
                        s=node_style.get('size', 100),
                        alpha=DISABLED_STYLE['alpha'],
                        edgecolors='gray',
                        linewidth=1,
                        zorder=2
                    )
            except ValueError:
                continue

    # 범례용 요소
    legend_elements = []

    for node_type, style in NODE_STYLES.items():
        nodes_of_type = [
            graph.get_node(nid) for nid in usable_nodes
            if graph.get_node(nid).node_type == node_type
        ]

        if not nodes_of_type:
            continue

        if 'icon' in style:
            icon_path = os.path.join(_ICON_DIR, style['icon'])

            if os.path.exists(icon_path):
                for node in nodes_of_type:
                    x, y = getattr(node, 'x', 0), getattr(node, 'y', 0)

                    icon_img = _load_and_tint_icon(icon_path, style['color'], style['zoom'])

                    ab = AnnotationBbox(icon_img, (x, y), frameon=False, zorder=3)
                    ax.add_artist(ab)

                    if node.node_type in ['attraction', 'entrance', 'restaurant', 'show']:
                        icon_height = _get_icon_height(icon_path)
                        actual_zoom = style['zoom']
                        rendered_height = icon_height * actual_zoom
                        offset_y = -(rendered_height / 2) - 10
                        ax.text(
                            x, y + offset_y,
                            node.name,
                            fontsize=NAME_FONTSIZE_SMALL,
                            fontweight='bold',
                            ha='center',
                            va='top',
                            color='white',
                            bbox=dict(boxstyle='round,pad=0.5', facecolor='#1a1a1a', edgecolor='white', alpha=0.9, linewidth=1.5),
                            zorder=4
                        )

            legend_elements.append(
                mpatches.Patch(facecolor=style['color'], label=style['label'])
            )
        else:
            x_coords = [getattr(n, 'x', 0) for n in nodes_of_type]
            y_coords = [getattr(n, 'y', 0) for n in nodes_of_type]

            ax.scatter(
                x_coords, y_coords,
                c=style['color'],
                marker=style.get('marker', 'o'),
                s=style.get('size', 100),
                label=f"{style['label']} (사용가능)",
                alpha=0.8,
                edgecolors='black',
                linewidth=1,
                zorder=3
            )

    if filtered_nodes:
        legend_elements.append(
            mpatches.Patch(facecolor=DISABLED_STYLE['color'], label='제약조건 적용',
                         alpha=DISABLED_STYLE['alpha'])
        )

    ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold', pad=50, color='white')
    ax.axis('off')

    legend = ax.legend(handles=legend_elements if legend_elements else None,
                      loc='upper right', fontsize=LEGEND_FONTSIZE, frameon=False,
                      labelspacing=1.2, bbox_to_anchor=(0.95, 0.95))
    for text in legend.get_texts():
        text.set_color('white')
        text.set_fontweight('bold')

    all_nodes = list(set(usable_nodes + filtered_nodes))
    _ensure_coordinate_bounds(ax, all_nodes, graph)

    ax.set_aspect('equal', adjustable='box')

    # 여백 추가
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_margin = (xlim[1] - xlim[0]) * FILTERED_MARGIN_RATIO
    y_margin = (ylim[1] - ylim[0]) * FILTERED_MARGIN_RATIO
    ax.set_xlim(xlim[0] - x_margin, xlim[1] + x_margin)
    ax.set_ylim(ylim[0] - y_margin, ylim[1] + y_margin)

    _add_border_frame(ax)

    plt.tight_layout()

    _save_and_resize_figure(fig, output_path)

    print(f"    Filtered graph visualization saved: {output_path}")


def visualize_path(
    graph: Graph,
    path: List[int],
    usable_nodes: List[int],
    algorithm_name: str = 'Algorithm',
    output_path: str = 'output/everland/path.png',
    figsize: Tuple[int, int] = (22, 18),
    destination_nodes: Optional[List[int]] = None
) -> None:
    """
    최적 경로 지도 시각화

    Args:
        graph: 그래프 객체
        path: 최적 경로 노드 ID 리스트 (중간 경유 노드 포함)
        usable_nodes: 사용 가능한 노드 ID 리스트
        algorithm_name: 알고리즘 이름
        output_path: 저장 경로
        figsize: matplotlib figure 크기
        destination_nodes: 실제 목적지 노드 리스트 (None이면 path와 동일)
    """
    fig, ax = plt.subplots(figsize=figsize)
    fig.subplots_adjust(top=0.94, bottom=0.06, left=0.06, right=0.94)

    usable_set = set(usable_nodes)
    path_set = set(path)

    # 배경 간선 그리기
    for node in graph.nodes:
        if not node or node.id not in usable_set:
            continue

        x1, y1 = _get_node_position(graph, node.id)
        neighbors = graph.get_neighbors(node.id)

        for neighbor_id, _ in neighbors:
            if neighbor_id in usable_set and node.id < neighbor_id:
                x2, y2 = _get_node_position(graph, neighbor_id)
                ax.plot([x1, x2], [y1, y2], 'lightgray', linewidth=EDGE_WIDTH_THIN, alpha=0.25, zorder=1)

    # 경로에 포함되지 않은 노드 흐리게 표시
    for node_type, style in NODE_STYLES.items():
        nodes_of_type = [
            graph.get_node(nid) for nid in usable_nodes
            if nid not in path_set and graph.get_node(nid).node_type == node_type
        ]

        if not nodes_of_type:
            continue

        if 'icon' in style:
            icon_path = os.path.join(_ICON_DIR, style['icon'])

            if os.path.exists(icon_path):
                for node in nodes_of_type:
                    x, y = getattr(node, 'x', 0), getattr(node, 'y', 0)

                    icon_img = _load_and_tint_icon(icon_path, '#cccccc', style['zoom'] * UNVISITED_ICON_SCALE)
                    ab = AnnotationBbox(icon_img, (x, y), frameon=False, zorder=2)
                    ax.add_artist(ab)
        else:
            x_coords = [getattr(n, 'x', 0) for n in nodes_of_type]
            y_coords = [getattr(n, 'y', 0) for n in nodes_of_type]

            ax.scatter(
                x_coords, y_coords,
                c='#cccccc',
                marker=style.get('marker', 'o'),
                s=style.get('size', 100) * 0.5,
                alpha=0.3,
                edgecolors='gray',
                linewidth=0.5,
                zorder=2
            )

    # 경로 및 방향 화살표 그리기
    if len(path) >= 2:
        path_x = []
        path_y = []

        for node_id in path:
            x, y = _get_node_position(graph, node_id)
            path_x.append(x)
            path_y.append(y)

        ax.plot(
            path_x, path_y,
            color=PATH_STYLE['color'],
            linewidth=PATH_STYLE['linewidth'],
            alpha=PATH_STYLE['alpha'],
            zorder=PATH_STYLE['zorder'],
            label='경로'
        )

        for i in range(len(path) - 1):
            x1, y1 = path_x[i], path_y[i]
            x2, y2 = path_x[i + 1], path_y[i + 1]

            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            dx = x2 - x1
            dy = y2 - y1

            arrow_scale = 0.15

            ax.annotate(
                '',
                xy=(mid_x + dx * arrow_scale, mid_y + dy * arrow_scale),
                xytext=(mid_x - dx * arrow_scale, mid_y - dy * arrow_scale),
                arrowprops=dict(
                    arrowstyle='-|>',
                    color=PATH_STYLE['color'],
                    lw=PATH_ARROW_WIDTH,
                    alpha=0.9,
                    mutation_scale=60
                ),
                zorder=PATH_MARKER_STYLE['zorder'] + 2
            )

    # 목적지 노드만 아이콘 및 순서 번호 표시
    # destination_nodes가 없으면 path 전체를 목적지로 간주 (하위 호환성)
    destinations = set(destination_nodes) if destination_nodes else set(path)

    # 목적지 노드의 순서 매핑 (경유 노드 제외)
    destination_order = {}
    order_counter = 1
    for node_id in path:
        if node_id in destinations:
            if node_id not in destination_order:
                destination_order[node_id] = order_counter
                order_counter += 1

    for node_id in path:
        # 경유 노드는 스킵
        if node_id not in destinations:
            continue

        node = graph.get_node(node_id)
        x, y = _get_node_position(graph, node_id)
        node_style = NODE_STYLES.get(node.node_type, {})

        if 'icon' in node_style:
            icon_path = os.path.join(_ICON_DIR, node_style['icon'])

            if os.path.exists(icon_path):
                icon_img = _load_and_tint_icon(icon_path, node_style['color'], node_style['zoom'] * PATH_ICON_SCALE)
                ab = AnnotationBbox(icon_img, (x, y), frameon=False, zorder=PATH_MARKER_STYLE['zorder'])
                ax.add_artist(ab)
        else:
            ax.scatter(
                [x], [y],
                c=node_style.get('color', PATH_MARKER_STYLE['color']),
                s=PATH_MARKER_STYLE['size'],
                edgecolors=PATH_MARKER_STYLE['edgecolor'],
                linewidth=PATH_MARKER_STYLE['linewidth'],
                zorder=PATH_MARKER_STYLE['zorder'],
                alpha=1.0
            )

        ax.text(
            x, y, str(destination_order[node_id]),
            color='white',
            fontsize=ORDER_FONTSIZE,
            fontweight='bold',
            ha='center',
            va='center',
            bbox=dict(boxstyle='circle,pad=0.35', facecolor='black', edgecolor='white', linewidth=2.5),
            zorder=PATH_MARKER_STYLE['zorder'] + 1
        )

        if node.node_type in ['attraction', 'entrance', 'restaurant', 'show']:
            icon_path = os.path.join(_ICON_DIR, node_style['icon'])
            icon_height = _get_icon_height(icon_path)
            actual_zoom = node_style['zoom'] * PATH_ICON_SCALE
            rendered_height = icon_height * actual_zoom
            offset_y = -(rendered_height / 2) - 10
            ax.text(
                x, y + offset_y,
                node.name,
                fontsize=NAME_FONTSIZE,
                fontweight='bold',
                ha='center',
                va='top',
                color='white',
                bbox=dict(boxstyle='round,pad=0.6', facecolor='#1a1a1a', edgecolor='white', alpha=0.95, linewidth=2),
                zorder=PATH_MARKER_STYLE['zorder']
            )

    title = f'{algorithm_name} - 최적 경로 지도'
    ax.set_title(title, fontsize=TITLE_FONTSIZE, fontweight='bold', pad=50, color='white')
    ax.axis('off')

    legend_elements = [
        mpatches.Patch(facecolor=PATH_STYLE['color'], label='경로'),
        plt.Line2D([0], [0], marker='o', color='w',
                   markerfacecolor=PATH_MARKER_STYLE['color'],
                   markeredgecolor=PATH_MARKER_STYLE['edgecolor'],
                   markeredgewidth=2, markersize=14, label='방문 노드')
    ]
    legend = ax.legend(handles=legend_elements, loc='upper right', fontsize=LEGEND_FONTSIZE, frameon=False,
                      labelspacing=1.2, bbox_to_anchor=(0.95, 0.95))
    for text in legend.get_texts():
        text.set_color('white')
        text.set_fontweight('bold')

    ax.set_aspect('equal', adjustable='box')

    # 여백 추가
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_margin = (xlim[1] - xlim[0]) * PATH_MARGIN_RATIO
    y_margin = (ylim[1] - ylim[0]) * PATH_MARGIN_RATIO
    ax.set_xlim(xlim[0] - x_margin, xlim[1] + x_margin)
    ax.set_ylim(ylim[0] - y_margin, ylim[1] + y_margin)

    _ensure_coordinate_bounds(ax, usable_nodes, graph)

    _add_border_frame(ax)

    plt.tight_layout()

    _save_and_resize_figure(fig, output_path)

    print(f"    Path visualization saved: {output_path}")


def visualize_all(
    graph: Graph,
    usable_nodes: List[int],
    filtered_nodes: List[int],
    path: List[int],
    algorithm_name: str,
    output_dir: str = 'output/everland',
    destination_nodes: Optional[List[int]] = None
) -> None:
    """
    전체 그래프, 제약조건 노드, 최적 경로 지도 생성

    Args:
        graph: 그래프 객체
        usable_nodes: 사용 가능한 노드 ID 리스트
        filtered_nodes: 제약조건으로 필터링된 노드 ID 리스트
        path: 최적 경로 노드 ID 리스트 (중간 경유 노드 포함)
        algorithm_name: 알고리즘 이름
        output_dir: 출력 디렉토리 경로
        destination_nodes: 실제 목적지 노드 리스트 (None이면 path와 동일)
    """
    print("[Generating visualizations...]")

    visualize_graph(
        graph,
        output_path=os.path.join(output_dir, 'graph.png'),
        title='테마파크 전체 그래프'
    )

    visualize_filtered_graph(
        graph,
        usable_nodes,
        filtered_nodes,
        output_path=os.path.join(output_dir, 'filtered_graph.png'),
        title='제약조건 적용 노드'
    )

    visualize_path(
        graph,
        path,
        usable_nodes,
        algorithm_name=algorithm_name,
        output_path=os.path.join(output_dir, f'path_{algorithm_name.replace(" ", "_").lower()}.png'),
        destination_nodes=destination_nodes
    )

    print(f"[All visualizations saved to: {output_dir}/]")
