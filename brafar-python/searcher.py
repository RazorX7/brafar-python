import distance

from bidirectional_refactoring.mapping import RoughMapping, LoopMapping
from basic_framework.program_builder import get_programs, get_program
import time


def search_kth_max_match(k, buggy_method, correct_ps):
    lp_map = 0
    map_ps = []
    lp_edit_distance = 100
    need_refactor = True
    for correct_p in correct_ps:
        correct_m = correct_p.methods.get(buggy_method.m_name)
        if correct_m is None:
            continue
        if correct_m.is_containing_inner_func():
            continue
        if buggy_method.cfs == correct_m.cfs:
            if need_refactor:
                map_ps.clear()
            map_ps.append((correct_m.f_name, correct_m, 1))
            lp_edit_distance = 0
            need_refactor = False
        elif need_refactor:
            rough_map = RoughMapping(buggy_method.cs_node, correct_m.cs_node)
            rough_map.mapping()
            loop_map = LoopMapping(buggy_method.cs_node, correct_m.cs_node)
            loop_map.mapping()
            cur_lp_edit_distance = len(loop_map.src_nodes) + len(loop_map.dst_nodes) - 2 * loop_map.mapping_score
            if cur_lp_edit_distance < lp_edit_distance:
                lp_map = loop_map.mapping_score
                lp_edit_distance = cur_lp_edit_distance
                lp_map_rate = float(loop_map.mapping_score) / float(
                    max(len(loop_map.src_nodes), len(loop_map.dst_nodes)))
                map_ps.clear()
                map_ps.append((correct_m.f_name, correct_m, rough_map.mapping_score,
                               float(rough_map.mapping_score) / float(
                                   max(len(rough_map.src_nodes), len(rough_map.dst_nodes)))))
            elif cur_lp_edit_distance == lp_edit_distance:
                map_ps.append((correct_m.f_name, correct_m, rough_map.mapping_score,
                               float(rough_map.mapping_score) / float(
                                   max(len(rough_map.src_nodes), len(rough_map.dst_nodes)))))
    map_ps = sorted(map_ps, key=lambda x: x[2], reverse=True)
    new_map_ps = []
    for map_p in map_ps:
        if map_p[1].is_recursive() and not buggy_method.is_recursive():
            continue
        if map_p[1].get_call_funcs() == buggy_method.get_call_funcs():
            new_map_ps.append(map_p)
    if len(new_map_ps) == 0:
        new_map_ps = map_ps
    # if len(new_map_ps) > k:
    #     new_map_ps = new_map_ps[0:k]
    kth_ps = []
    for map_p in new_map_ps:
        kth_ps.append((map_p[0], map_p[1].get_method_code()))
    return kth_ps


def get_closest_correct_reference_program(buggy_code, k_th_closest_programs):
    min_ted, best_f_name = None, None
    for func_name, func_code in k_th_closest_programs:
        if min_ted is None:
            min_ted = distance.lev_multi_func_code_distance(buggy_code, func_code)
            best_f_name = func_name
        else:
            ted = distance.smt_lev_multi_func_code_distance(buggy_code, func_code, min_ted)
            if ted < min_ted:
                min_ted = ted
                best_f_name = func_name
    return best_f_name


class Searcher:
    def __init__(self, buggy_code_path, correct_code_path_list):
        self.k = 3
        self.__buggy_program = get_program(buggy_code_path)
        self.__correct_programs = get_programs(correct_code_path_list)
        self.__program_maps = {}
        self.run()

    def run(self):
        func_map = {}
        for func_name in self.__buggy_program.methods.keys():
            k_th_closest_programs = search_kth_max_match(
                self.k, self.__buggy_program.get_method(func_name), self.__correct_programs)
            func_map[func_name] = get_closest_correct_reference_program(
                self.__buggy_program.get_method(func_name).get_method_code(), k_th_closest_programs)
        self.__program_maps = func_map

    def get_program_maps(self):
        return self.__program_maps
