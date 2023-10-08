import argparse
import os

from core import S_Brafar

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data_dir", help="the path of the data directory.",
                        nargs='+', required=True)
    parser.add_argument("-q", "--questions", help="a sequence of question names.",
                        nargs='+', default=None)
    parser.add_argument("-t", "--testcases", help="a sequence of question names.",
                        nargs='+', default=None)
    parser.add_argument("-s", "--sampling_rates", help="a sequence of sampling rates.",
                        nargs='+', type=int, default=[0, 20, 40, 60, 80, 100])
    parser.add_argument("-o", "--output_path", help="the output path.",
                        nargs='+', default=None)
    args = parser.parse_args()

    base_dir = os.path.join(args.data_dir[0], args.questions[0])
    wrong_dir = os.path.join(base_dir, "code", "wrong")
    correct_dir = os.path.join(base_dir, "code", "correct")
    reference_dir = os.path.join(base_dir, "code", "reference")
    ans_dir = os.path.join(base_dir, "ans")
    s_brafar = S_Brafar(base_dir, wrong_dir, correct_dir,
                        reference_dir, ans_dir, args.sampling_rates[0], 15)
    if not os.path.exists(args.output_path[0]):
        os.makedirs(args.output_path[0])
    os.popen("diff {} {} > {}".format(s_brafar.get_buggy_code_path(), os.path.join(base_dir, "repaired_code.py"),
                                      os.path.join(args.output_path[0], "patch.diff")))
    # print("repair")

