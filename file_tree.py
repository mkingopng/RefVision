"""
map the directory structure and save to a .txt file
"""
import os

EXCLUDE_DIRS = {'.git', '.idea'}
OUTPUT_FILE = 'project_structure.txt'


def generate_file_tree(directory, indent=''):
    tree = []
    entries = sorted(os.listdir(directory))

    for entry in entries:
        path = os.path.join(directory, entry)
        if os.path.isdir(path) and entry not in EXCLUDE_DIRS:
            tree.append(f'{indent}{entry}/')
            tree.extend(generate_file_tree(path, indent + '    '))
        elif os.path.isfile(path):
            tree.append(f'{indent}{entry}')

    return tree


def save_file_tree():
    root_dir = '.'  # Current directory
    tree = generate_file_tree(root_dir)

    with open(OUTPUT_FILE, 'w') as f:
        f.write('\n'.join(tree))

    print(f"Project structure saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    save_file_tree()
