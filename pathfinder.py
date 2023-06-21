import math
from queue import PriorityQueue, Queue
from typing import List, Literal, Tuple

from global_var import global_data_dict

# 노드 타입
ENTRANCE = "entrance_location_list"
EMPTY_SPACE = "empty_space_list"
ANCHOR = "anchor_pos_list"


def calculate_distance(x: int, y: int, dx: int, dy: int, mode: Literal["manhattan", "euclidean"] = "manhattan") -> int:
    """Manhattan distance 계산 처리

    Args:
        x (int): 출발 좌표 X
        y (int): 출발 좌표 Y
        dx (int): 목적 좌표 X
        dy (int): 목적 좌표 Y
        mode (Literal[&quot;manhattan&quot;, &quot;euclidean&quot;], optional): 거리계산 모드. Defaults to "manhattan".

    Returns:
        int: 거리
    """

    if mode == "manhattan":
        return abs(dx - x) + abs(dy - y)
    elif mode == "euclidean":
        return math.sqrt((dx - x) ** 2 + (dy - y) ** 2)


class PathNode:
    """경로 노드"""

    def __init__(self, x: int, y: int, node_type: Literal["entrance_location_list", "empty_space_list", "anchor_pos_list"]) -> None:
        """
        Args:
            x (int): X 좌표
            y (int): Y 좌표
            node_type (Literal[&quot;entrance_location_list&quot;, &quot;empty_space_list&quot;, &quot;anchor_pos_list&quot;]): 노드 타입
        """
        self.x = x
        self.y = y
        self.node_type = node_type
        self.near_nodes = []  # 연결된 인접 노드

    @property
    def is_last_node(self) -> bool:
        """마지막 노드 여부"""
        return self.node_type == EMPTY_SPACE

    def __del__(self):
        pass


def calculate_distance_node(node: PathNode, dnode: PathNode) -> int:
    """노드간 거리 계산

    Args:
        node (PathNode): 출발노드
        dnode (PathNode): 목적노드

    Returns:
        int: 거리
    """

    return calculate_distance(node.x, node.y, dnode.x, dnode.y)


def nodes_clear():
    """저장된 노드 초기화"""

    rootnodes = global_data_dict["rootnodes"]
    nodes = global_data_dict["nodes"]

    for node in rootnodes:
        del node
    rootnodes.clear()
    for node in nodes:
        del node
    nodes.clear()


def node_preprocessing():
    """노드 전처리

    1. 좌표를 기반으로 노드 생성
    2. 주차장 입구 노드(루트노드) 및 주차 자리 노드를 가장 가까운 앵커노드에 연결
    """

    rootnodes = global_data_dict["rootnodes"]
    nodes = global_data_dict["nodes"]

    rootnode: PathNode
    node: PathNode
    p_node: PathNode
    q_node: PathNode

    for p_node in nodes:
        for q_node in nodes:
            if p_node == q_node:
                continue

            if p_node.node_type == EMPTY_SPACE:
                continue
            p_node.put(q_node)

    for p_node in nodes:
        min_distance = None
        dist_node = None

        for q_node in nodes:
            if p_node == q_node:
                continue

            if p_node.node_type == EMPTY_SPACE and q_node.node_type == ANCHOR:
                distance = calculate_distance_node(p_node, q_node)
                if min_distance is None or min_distance > distance:
                    min_distance = distance
                    dist_node = p_node

            elif p_node.node_type == ANCHOR and q_node.node_type == ANCHOR:
                distance = calculate_distance_node(p_node, q_node)
                if min_distance is None or min_distance > distance:
                    min_distance = distance
                    dist_node = p_node

        p_node.parent = dist_node

    min_distance = None
    dist_node = None

    for rootnode in rootnodes:
        for node in nodes:
            if node.node_type == ANCHOR:
                distance = calculate_distance_node(rootnode, node)
                if min_distance is None or min_distance > distance:
                    min_distance = distance
                    dist_node = p_node

        rootnode.put(dist_node)


def find_path(rootnode: PathNode) -> Tuple[PathNode, PathNode]:
    """가장 가까운 빈 주차자리 노드의 탐색 및 도달 경로 탐색 처리

    Args:
        rootnode (PathNode): 주차장 입구 노드(루트노드)

    Returns:
        Tuple[PathNode, PathNode]: 출발 노드, 도착 노드
    """

    node_preprocessing()

    nodes: List[PathNode]
    nodes = global_data_dict["nodes"]

    min_distance = None
    dist_node = None

    for node in nodes:
        if node.node_type == EMPTY_SPACE and node.is_empty_space:
            distance = calculate_distance_node(rootnode, node)
            if min_distance is None or min_distance > distance:
                min_distance = distance
                dist_node = node

    assert dist_node is not None, "빈 주차 자리를 찾을 수 없습니다."

    # 1. 입구에서 가장 가까운 빈 자리
    # 2. 경로 (노드를 순서대로 반환)
    # 3. 거리 계산 (멘하탄 거리)

    node: PathNode
    start_node = rootnode.get()
    queue = Queue()
    queue.put(dist_node.parent)

    while len(queue) > 0:
        node = queue.get()

        if node.parent == start_node:
            p_node = node.parent
            p_node.parent = start_node
            break

        queue.put(node.parent)

    return rootnode, dist_node
