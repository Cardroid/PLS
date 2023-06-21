import copy
import math
from queue import PriorityQueue, Queue
from typing import Callable, Generator, List, Literal, Optional, Tuple

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
        self._near_nodes = []  # 연결된 인접 노드

    def add_near_node(self, node):
        """연결된 노드 추가

        Args:
            node (PathNode): _description_
        """
        self._near_nodes.append(node)

    def get_near_node(self) -> Generator:
        """연결된 노드 반환

        Yields:
            Generator[PathNode]: 노드를 하나씩 반환
        """
        return self._near_nodes

    @property
    def is_root_node(self) -> bool:
        """루트 노드 여부"""
        return self.node_type == ENTRANCE

    @property
    def is_leaf_node(self) -> bool:
        """마지막 노드 여부"""
        return self.node_type == EMPTY_SPACE

    def __repr__(self) -> str:
        return (
            f"\n=====\n 노드 위치: ({self.x} {self.y})\n"
            f" 노드 타입: {self.node_type}\n"
            f" 루트노드 여부: {self.is_root_node}\n"
            f" 리프노드 여부: {self.is_leaf_node}\n"
            f" 연결된 노드 개수: {len(self._near_nodes)}"
        )

    def clear(self):
        self._near_nodes.clear()


def calculate_distance_node(node: PathNode, dnode: PathNode, mode: Literal["manhattan", "euclidean"] = "manhattan") -> int:
    """노드간 거리 계산

    Args:
        node (PathNode): 출발노드
        dnode (PathNode): 목적노드
        mode (Literal[&quot;manhattan&quot;, &quot;euclidean&quot;], optional): 거리계산 모드. Defaults to "manhattan".

    Returns:
        int: 거리
    """

    return calculate_distance(node.x, node.y, dnode.x, dnode.y, mode)


def nodes_clear():
    """저장된 노드 초기화"""

    nodes = global_data_dict["nodes"]
    for node in nodes:
        node.clear()
    nodes.clear()


def node_preprocessing(node_Creater: Optional[Callable[..., PathNode]]):
    """노드 전처리

    1. 좌표를 기반으로 노드 생성
    2. 주차장 입구 노드(루트노드) 및 주차 자리 노드를 가장 가까운 앵커노드에 연결

    Args:
        node_Creater (Optional[Callable[..., PathNode]]): 노드 생성자
    """

    if node_Creater is None:
        node_Creater = PathNode

    data_list: List[str]
    anchor_pos_list: List[str]
    nodes: List[PathNode] = global_data_dict["nodes"]

    p_node: PathNode
    q_node: PathNode

    anchor_pos_list = global_data_dict["anchor_pos_list"]
    anchor_node_list = []

    for s_data in anchor_pos_list:
        data = tuple(map(int, s_data.split(",")))
        node = node_Creater(data[0], data[1], ANCHOR)
        nodes.append(node)
        anchor_node_list.append(node)

    overlap_space_list = global_data_dict["overlap_space_list"]

    for list_tag in ["empty_space_list", "entrance_location_list"]:
        data_list = global_data_dict[list_tag]
        for s_data in data_list:
            x, y = tuple(map(int, s_data.split(",")))

            if list_tag == "empty_space_list":
                is_jump = False
                for cls, (ox, oy) in overlap_space_list:
                    if x == ox and y == oy:
                        is_jump = True
                        break
                if is_jump:
                    continue

            node = node_Creater(x, y, list_tag)

            min_distance = None
            dist_node = None

            for anchor_node in anchor_node_list:
                distance = calculate_distance_node(anchor_node, node)
                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    dist_node = anchor_node

            node.add_near_node(dist_node)
            dist_node.add_near_node(node)
            nodes.append(node)

    compare = (
        lambda bx, by, ax, ay, a_node, b_node: a_node.x == bx
        and a_node.y == by
        and b_node.x == ax
        and b_node.y == ay
        or b_node.x == bx
        and b_node.y == by
        and a_node.x == ax
        and a_node.y == ay
    )

    for edge in global_data_dict["edge_list"]:
        is_break = False
        bpos, apos = edge.split("-")
        bx, by = tuple(map(int, bpos.split(",")))
        ax, ay = tuple(map(int, apos.split(",")))

        for p_node in nodes:
            for q_node in nodes:
                if p_node == q_node:
                    continue
                if compare(bx, by, ax, ay, p_node, q_node):
                    p_node.add_near_node(q_node)
                    q_node.add_near_node(p_node)
                    is_break = True
                if is_break:
                    break
            if is_break:
                break


def find_path(entry_pos: Tuple[int, int], node_Creater: Optional[Callable[..., PathNode]], is_fast_mode: bool = True) -> Tuple[PathNode, PathNode]:
    """가장 가까운 빈 주차자리 노드의 탐색 및 도달 경로 탐색 처리

    Args:
        rootnode (PathNode): 주차장 입구 노드(루트노드)
        node_Creater (Optional[Callable[..., PathNode]]): 노드 생성자
        is_fast_mode (bool): 단순 경로 탐색 여부

    Returns:
        Tuple[PathNode, PathNode]: 출발 노드, 도착 노드
    """

    nodes_clear()

    node_preprocessing(node_Creater)

    nodes: List[PathNode] = global_data_dict["nodes"]

    entry_pos_x, entry_pos_y = entry_pos
    root_node = None

    for node in nodes:
        if node.x == entry_pos_x and node.y == entry_pos_y:
            root_node = node

    assert root_node is not None, "루트 노드를 찾지 못했습니다."

    # 1. 입구에서 가장 가까운 빈 자리
    # 2. 경로 (노드를 순서대로 반환)
    # 3. 거리 계산 (멘하탄 거리)

    node: PathNode
    near_node: PathNode
    path_list: List[PathNode]
    path = PriorityQueue()
    queue = Queue()
    queue.put((0, [root_node]))

    while not queue.empty():
        distance, path_list = queue.get()
        node = path_list[-1]

        for near_node in node.get_near_node():
            if near_node.is_leaf_node:
                out_path_list = copy.copy(path_list)
                out_path_list.append(near_node)
                temp = (distance + calculate_distance_node(node, near_node), out_path_list)
                path.put(temp)
                if is_fast_mode:
                    return temp
                else:
                    continue

            if near_node in path_list:
                continue

            path_list.append(near_node)
            queue.put((distance + calculate_distance_node(node, near_node), copy.copy(path_list)))

    result_list = []
    idx = 0
    while not path.empty() and idx < 3:
        result_list.append(path.get())
        idx += 1

    if len(result_list) == 0:
        print("경로를 찾을 수 없습니다.")
        return None
    else:
        print("[탐색된 경로]")
        for idx, result in enumerate(result_list):
            current_distance, current_path = result
            print(f"\n[{idx + 1}번] 가장 가까운 빈 공간 거리: {current_distance}")
            print(f"[출발 노드]")
            print(" -> " + str(current_path[0]).replace("\n", "\n -> "))
            print(f"\n[도착 노드]")
            print(" -> " + str(current_path[-1]).replace("\n", "\n -> "))

            print(f"\n==> 경로: {current_path}")

        return result_list[0]
