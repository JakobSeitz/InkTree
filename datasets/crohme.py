# this file is responsible for finding the right files in the CROHME dataset

import os


# data/ folder lives one level above datasets/ (at project root)
_project_root = os.path.dirname(os.path.dirname(__file__))

relative_InkML_path = os.path.join("data", "CROHME23", "INKML")
InkML_path = os.path.join(_project_root, relative_InkML_path)

syntatic_artificial_train_paths = [
    os.path.join(InkML_path, "train", "Artificial_data", "gen_syntatic_data"),
]
artificial_train_paths = [
    os.path.join(InkML_path, "train", "Artificial_data", "gen_LaTeX_data_CROHME_2019"),
    os.path.join(InkML_path, "train", "Artificial_data", "gen_LaTeX_data_CROHME_2023_corpus")
] + syntatic_artificial_train_paths
real_train_paths = [
    os.path.join(InkML_path, "train", "CROHME2019"),
    os.path.join(InkML_path, "train", "CROHME2023_train")
]
val_paths = [
    os.path.join(InkML_path, "val", "CROHME2016_test"),
    os.path.join(InkML_path, "val", "CROHME2023_val"),
]
test_paths = [
    os.path.join(InkML_path, "test", "CROHME2019_test"),
    os.path.join(InkML_path, "test", "CROHME2023_test"),
]

warning_str = '\033[93m' + "Warning:" + '\033[0m'


class CrohmeFileManager:
    @staticmethod
    def get_train_files():
        print(f"[CrohmeFileManager] {warning_str} Loading all train files. Some files are broken. Use get_real_train_files() to get better results.")
        return CrohmeFileManager.get_artificial_train_files() + CrohmeFileManager.get_real_train_files()

    @staticmethod
    def get_artificial_train_files():
        print(f"[CrohmeFileManager] {warning_str} Loading artificial train files. Most of them are broken.")
        return CrohmeFileManager.get_files_from_paths(artificial_train_paths)

    @staticmethod
    def get_artificial_train_files_2019():
        print(f"[CrohmeFileManager] {warning_str} Loading artificial train files. Most of them are broken.")
        return CrohmeFileManager.get_files_from_paths([artificial_train_paths[0]])

    @staticmethod
    def get_artificial_train_files_2023():
        print(f"[CrohmeFileManager] {warning_str} Loading artificial train files. Most of them are broken.")
        return CrohmeFileManager.get_files_from_paths([artificial_train_paths[1]])

    @staticmethod
    def get_syntatic_train_files():
        """ Those files are labeled inaccurately but the trace groups are correct. It can be used for segmentation """
        print(f"[CrohmeFileManager] {warning_str} Loading syntatic train files. They have no relation graph.")
        return CrohmeFileManager.get_files_from_paths(syntatic_artificial_train_paths)

    @staticmethod
    def get_real_train_files():
        """ Those files are labeled accurately """
        return CrohmeFileManager.get_files_from_paths(real_train_paths)

    @staticmethod
    def get_val_files():
        return CrohmeFileManager.get_files_from_paths(val_paths)

    @staticmethod
    def get_test_files():
        return CrohmeFileManager.get_files_from_paths(test_paths)

    @staticmethod
    def get_2016test_files():
        return CrohmeFileManager.get_files_from_paths([os.path.join(InkML_path, "val", 'CROHME2016_test')])

    @staticmethod
    def get_2019test_files():
        return CrohmeFileManager.get_files_from_paths([os.path.join(InkML_path, "test", "CROHME2019_test")])

    @staticmethod
    def get_2023test_files():
        return CrohmeFileManager.get_files_from_paths([os.path.join(InkML_path, "test", "CROHME2023_test")])

    @staticmethod
    def get_files_from_paths(paths):
        files = []
        for path in paths:
            if not os.path.isdir(path):
                raise FileNotFoundError(f"Path {path} does not exist")
            files += [os.path.join(path, file) for file in os.listdir(path) if file.endswith('.inkml')]
        return files
