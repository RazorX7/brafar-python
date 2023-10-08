import ast
import os.path
import random
import time

import fault_locator
from basic_framework.block_builder import BlockType
from bidirectional_refactoring.edit_script import EditScript
from bidirectional_refactoring.refactoring import Recover
from distance import ProgramTree
from searcher import Searcher
from basic_framework.program_builder import get_program, Reconstructor, get_code
from aligner import Aligner
from repairer import Repairer
from fault_locator import TestResult


def get_file_list(p_dir_path, sample_rate):
    path_list = []
    for file_name in os.listdir(p_dir_path):
        code_path = os.path.join(p_dir_path, file_name)
        path_list.append(code_path)
    # random.shuffle(path_list)
    l = len(path_list)
    path_list = path_list[:int(sample_rate / 100 * l)]
    return path_list
            

def get_case_paths(dir_path, type_name):
    res = []
    for file_name in os.listdir(dir_path):
        curr_path = os.path.join(dir_path, file_name)
        if os.path.isfile(curr_path):
            if file_name.__contains__(type_name):
                res.append(curr_path)
    return res


class Brafar:
    def __init__(self, buggy_f, correct_f, func_name, case_inputs, case_outputs, _global):
        self._init_test_result = None
        self.__repaired_code = None
        self.__repair_result = False
        self.__has_fixed = None
        self.__aligner = None
        self.__MAX_REPAIR_COUNT = 25
        self.buggy_p = get_program(buggy_f)
        self.buggy_m = self.buggy_p.get_method(func_name)
        self.correct_p = get_program(correct_f)
        self.correct_m = self.correct_p.get_method(func_name)
        self.__test_case_inputs = case_inputs
        self.__test_case_outputs = case_outputs
        self.__global_path = _global
        self.init_test()
        if self.__repair_result:
            self.__repaired_code = ast.unparse(self.buggy_m.get_m_node())
            return
        self.bidirectional_refactoring()
        self.__aligner = Aligner(self.buggy_m, self.correct_m)
        self.buggy_m.get_block_builder().update_m_node()
        self.__has_fixed = []
        self.__repair_result = False
        self.__repaired_code = None
        # self.block_by_block_repair()
        self.buggy_m.get_block_builder().update_m_node()
        self.repair_with_afl()

    def init_test(self):
        reconstructed_p = Reconstructor(self.correct_p.get_p_node(), self.buggy_m.get_m_node())
        self._init_test_result = TestResult(ast.unparse(reconstructed_p.get_reconstructed_p_node()),
                                            self.__test_case_inputs, self.__test_case_outputs, self.__global_path)
        self.__repair_result = self._init_test_result.get_test_result()

    def block_by_block_repair(self):
        for block_node in self.buggy_m.get_meta_block_nodes():
            Repairer(block_node, self.__aligner)

    def get_repaired_code(self):
        return self.__repaired_code

    # def block_by_block_repair_from(self, begin_in, end_in):
    #     need_repair_back = True
    #     back_begin_index = begin_in
    #     while back_begin_index >= 0 and need_repair_back:
    #         begin_in = back_begin_index
    #         need_repair_back = False
    #         back_begin_index = -1
    #         for i in range(begin_in, end_in):
    #             __repairer = Repairer(self.buggy_m.get_meta_block_nodes()[i], self.__aligner)
    #             if __repairer.get_need_repair_back():
    #                 need_repair_back = True
    #                 if back_begin_index == -1 or __repairer.get_begin_index() < back_begin_index:
    #                     back_begin_index = __repairer.get_begin_index()
    #         end_in = begin_in

    # def repair_block(self, cur_block):
    #     __repairer = Repairer(cur_block, self.__aligner)
    #     if __repairer.get_need_repair_back():
    #         self.block_by_block_repair_from(__repairer.get_begin_index(), cur_block.get_meta_index())

    def block_by_block_repair_from(self, begin_in, end_in, trace: list):
        need_repair_back = True
        back_begin_index = begin_in
        while back_begin_index >= 0 and need_repair_back:
            begin_in = back_begin_index
            need_repair_back = False
            back_begin_index = -1
            for i in range(begin_in, end_in):
                if trace.__contains__(i) or (self.buggy_m.get_meta_block_nodes()[i].get_type() != BlockType.BASIC_BLOCK and trace.__contains__(i-1)):
                    __repairer = Repairer(self.buggy_m.get_meta_block_nodes()[i], self.__aligner)
                    if __repairer.get_need_repair_back():
                        need_repair_back = True
                        if back_begin_index == -1 or __repairer.get_begin_index() < back_begin_index:
                            back_begin_index = __repairer.get_begin_index()
            end_in = begin_in

    def repair_block(self, cur_block, trace: list):
        __repairer = Repairer(cur_block, self.__aligner)
        if __repairer.get_need_repair_back():
            self.block_by_block_repair_from(__repairer.get_begin_index(), cur_block.get_meta_index(), trace)

    def bidirectional_refactoring(self):
        if self.buggy_m.cfs != self.correct_m.cfs:
            edit_s = EditScript(self.buggy_m.m_node, self.correct_m.m_node)

    def get_repair_result(self):
        return self.__repair_result

    def repair_with_afl(self):
        test_result = self._init_test_result
        input_cases = test_result.get_failed_input_cases()
        output_cases = test_result.get_failed_output_cases()
        repair_count = 0
        while not test_result.get_test_result() and repair_count < 25:
            fl = fault_locator.FaultLocator(self.buggy_m, self.correct_m, self.correct_p, input_cases[0],
                                            output_cases[0], self.__aligner, self.__has_fixed, self.__global_path)
            if fl.get_fault_block() is None:
                print(False)
                break
            if not self.__has_fixed.__contains__(fl.get_fault_block().get_meta_index()):
                if fl.get_test_result() is not None:
                    if fl.get_test_result().get_need_b2b_repair():
                        self.block_by_block_repair_from(fl.get_fault_block().get_meta_index(), len(self.buggy_m.get_meta_block_nodes()), fl.get_correct_block_trace())
                    else:
                        self.repair_block(fl.get_fault_block(), fl.get_correct_block_trace())
                else:
                    self.repair_block(fl.get_fault_block(), fl.get_correct_block_trace())
                self.__has_fixed.append(fl.get_fault_block().get_meta_index())
            else:
                need_fixed_index = fl.get_fault_block().get_meta_index()-1
                flag = False
                while True:
                    if need_fixed_index < 0:
                        break
                    if not self.__has_fixed.__contains__(need_fixed_index):
                        self.repair_block(self.buggy_m.get_meta_block_nodes()[need_fixed_index],
                                          fl.get_correct_block_trace())
                        self.__has_fixed.append(fl.get_fault_block().get_meta_index())
                        flag = True
                        break
                    need_fixed_index -= 1
                if not flag:
                    print(False)
                    break
            self.buggy_m.get_block_builder().update_m_node()
            reconstructed_p = Reconstructor(self.correct_p.get_p_node(), self.buggy_m.get_m_node())
            code = ast.unparse(reconstructed_p.get_reconstructed_p_node())
            repair_count += 1
            # print("======================= Repair", repair_count, "============================")
            # print(code)
            test_result = TestResult(code, self.__test_case_inputs,
                                     self.__test_case_outputs, self.__global_path)
            input_cases = test_result.get_failed_input_cases()
            output_cases = test_result.get_failed_output_cases()
        # print("==================== End Repair =======================")
        # print("Repair Result:", test_result.get_test_result())
        self.__repair_result = test_result.get_test_result()
        Recover(self.buggy_m.get_m_node())
        reconstructed_p = Reconstructor(self.correct_p.get_p_node(), self.buggy_m.get_m_node())
        self.__repaired_code = ast.unparse(self.buggy_m.get_m_node())
        # print(ast.unparse(reconstructed_p.get_reconstructed_p_node()))


    # def repair_with_afl(self):
    #     while not self.test_result:


# class S_Brafar:
#     def __init__(self, ques_dir_path, correct_code_dir_path, ans_dir_path, sample_rate, exp_time):
#         self.__ques_dir_path = ques_dir_path
#         self.__correct_code_dir_path = correct_code_dir_path
#         self.__reference_code_path = os.path.join(ques_dir_path,"reference.py")
#         self.__exp_time = exp_time
#         self.__correct_code_path_list = get_file_list(correct_code_dir_path, sample_rate)
#         self.__correct_code_path_list.extend(self.__reference_code_path)
#         self.__buggy_code_path_list = get_file_list(ques_dir_path, 100)
#         self.__ans_dir_path = ans_dir_path
#         self.__case_inputs = sorted(get_case_paths(ans_dir_path, "input"))
#         self.__case_outputs = sorted(get_case_paths(ans_dir_path, "output"))
#         self.__program_map = {}
#
#     def run(self):
#         searcher = Searcher(self.__buggy_code_path_list, self.__correct_code_path_list)
#         self.__program_map = searcher.get_program_maps()
#         for f_name in self.__program_map.keys():
#             func_maps = self.__program_map.get(f_name)
#             for func_name in func_maps.keys():
#                 mapped_correct_code_paths = func_maps.get(func_name)
#                 for mapped_correct_code_path in mapped_correct_code_paths:
#                     Brafar(f_name, mapped_correct_code_path, func_name, self.__case_inputs, self.__case_outputs)

def get_target_wrong_file(target_wrong_folder):
    base_name = os.path.basename(target_wrong_folder)
    for file in os.listdir(target_wrong_folder):
        if file.find(base_name) != -1:
            return os.path.join(target_wrong_folder, file)


class S_Brafar:
    def __init__(self, base_dir, wrong_dir_path, correct_code_dir_path, reference_dir_path,
                 ans_dir_path, sample_rate, exp_time):

        self.__correct_code_dir_path = correct_code_dir_path
        self.__reference_code_path = os.path.join(reference_dir_path, "reference.py")
        self.__global_path = None
        if os.path.exists(os.path.join(base_dir, "code", "global.py")):
            self.__global_path = os.path.join(base_dir, "code", "global.py")
        self.__exp_time = exp_time
        self.__correct_code_path_list = get_file_list(correct_code_dir_path, sample_rate)
        self.__correct_code_path_list.append(self.__reference_code_path)
        self.__buggy_code_path = get_target_wrong_file(wrong_dir_path)
        self.__original_code = get_code(self.__buggy_code_path)
        self.__ans_dir_path = ans_dir_path
        self.__case_inputs = sorted(get_case_paths(ans_dir_path, "input"))
        self.__case_outputs = sorted(get_case_paths(ans_dir_path, "output"))
        self.__program_map = {}
        self.__repaired_map = {}
        self.__repaired_code = ""
        self.run()
        with open(os.path.join(base_dir, "repaired_code.py"), 'w') as file:
            file.write(self.__repaired_code)

    def get_original_code(self):
        return self.__original_code

    def get_repaired_code(self):
        return self.__repaired_code

    def get_buggy_code_path(self):
        return self.__buggy_code_path

    def run(self):
        searcher = Searcher(self.__buggy_code_path, self.__correct_code_path_list)
        self.__program_map = searcher.get_program_maps()
        p_tree = ProgramTree(self.__buggy_code_path)
        f_name = self.__buggy_code_path
        func_maps = self.__program_map
        for func_name in func_maps.keys():
            mapped_correct_code_paths = func_maps.get(func_name)
            repaired_func = []
            for mapped_correct_code_path in mapped_correct_code_paths:
                re_func = Brafar(f_name, mapped_correct_code_path, func_name,
                                 self.__case_inputs, self.__case_outputs, self.__global_path)
                if re_func.get_repair_result() and re_func.get_repaired_code() is not None:
                    repaired_func.append(re_func.get_repaired_code())
            self.__repaired_map[func_name] = p_tree.get_closest_func(func_name, repaired_func)
            # self.__repaired_code += "\n"
            self.__repaired_code += self.__repaired_map[func_name]
            self.__repaired_code += "\n"
            # print("=============================The final Repair is as follows===================================")
            # print(self.__repaired_map.get(func_name))
        self.validate_repaired_code()

    def validate_repaired_code(self):
        repair_result = TestResult(self.__repaired_code, self.__case_inputs, self.__case_outputs, self.__global_path)
        print("The repair result is:", repair_result.get_test_result())
        # print("=============================The final Repair is as follows===================================")
        # print(self.__repaired_code)


# if __name__ == '__main__':
#     startTime = time.time()
#     S_Brafar("education-python-benchmark/question_1/497", "education-python-benchmark/base/question_1/correct",
#              "education-python-benchmark/base/question_1/ans", 100, 100).run()
#     endTime = time.time()
#     print(endTime-startTime)
