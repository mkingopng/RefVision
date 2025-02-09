"""
map the directory structure and save to a .txt file
"""
import os

EXCLUDE_DIRS = {'.git', '.idea', 'data', 'runs', 'model_zoo'}
OUTPUT_FILE = 'project_structure.txt'


def generate_file_tree(directory, prefix=''):
    """
    Generate a tree structure of the files and directories in the given directory with visual indentation.
    """
    tree = []
    entries = [e for e in sorted(os.listdir(directory)) if
               e not in EXCLUDE_DIRS]
    entry_count = len(entries)

    for index, entry in enumerate(entries):
        path = os.path.join(directory, entry)
        is_last = index == entry_count - 1
        connector = '└── ' if is_last else '├── '

        if os.path.isdir(path):
            tree.append(f'{prefix}{connector}{entry}/')
            extension = '    ' if is_last else '│   '
            tree.extend(generate_file_tree(path, prefix + extension))
        elif os.path.isfile(path):
            tree.append(f'{prefix}{connector}{entry}')

    return tree


def save_file_tree():
    """
    Save the project structure to a .txt file
    """
    root_dir = '.'  # Current directory
    tree = generate_file_tree(root_dir)

    with open(OUTPUT_FILE, 'w') as f:
        f.write('\n'.join(tree))

    print(f"Project structure saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    save_file_tree()
